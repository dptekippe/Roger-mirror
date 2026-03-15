"""
echochamber_hook.py — OpenClaw after_model_response hook for EchoChamberGym.

Loads the trained PPO model, builds a state vector from the LLM response
context, predicts an anti-bias action, and injects [EchoChamber] annotations
when the agent decides to steelman or synthesize.

Graceful fallback: if the PPO model is not found, defaults to action=0
(accept_primary) so the gateway continues without error.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Domain weight mapping (must match echochamber_gym.py)
DOMAIN_WEIGHTS = {
    "fantasy_football": 1.5,
    "chess": 1.2,
    "deployment": 1.0,
    "general": 0.8,
}

ACTION_NAMES = {
    0: "accept_primary",
    1: "steelman_contra1",
    2: "steelman_contra2",
    3: "hybrid_synthesis",
    4: "escalate_PC",
    5: "memory_commit_debate",
}


class EchoChamberHook:
    """OpenClaw hook: after_model_response.

    Runs the trained EchoChamber PPO model on each LLM response to decide
    whether to inject metacognitive contra-analysis.
    """

    trigger = "after_model_response"

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        self.model_path = config.get("model_path", "./checkpoints/echo_ppo.zip")
        self.pgvector_table = config.get("pgvector_table", "memories")
        self.insights_table = config.get("universal_insights_table", "universal_insights")
        self.debate_log_path = config.get("debate_log_path", "./debate_tree_log.jsonl")
        self.domain_weights = config.get("domain_weights", DOMAIN_WEIGHTS)
        self.metacog_threshold = config.get("metacog_threshold", 0.7)
        self._model = None
        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self):
        """Attempt to load the PPO model. Fail silently → action=0 fallback."""
        try:
            from stable_baselines3 import PPO
            if Path(self.model_path).exists():
                self._model = PPO.load(self.model_path)
                logger.info("EchoChamber PPO model loaded from %s", self.model_path)
            else:
                logger.warning(
                    "EchoChamber PPO model not found at %s — falling back to accept_primary",
                    self.model_path,
                )
        except Exception as exc:
            logger.warning("Failed to load PPO model: %s — falling back to accept_primary", exc)

    # ------------------------------------------------------------------
    # State construction
    # ------------------------------------------------------------------

    def _build_state(self, context: dict) -> np.ndarray:
        """Extract a 7-dim state vector from the OpenClaw context."""
        response_meta = context.get("response_metadata", {})
        conf_score = float(response_meta.get("confidence", 0.5))

        # Contra hits from pgvector
        contra_memories = context.get("contra_memories", [])
        contra_hits = float(min(len(contra_memories), 10))

        debate_depth = float(context.get("debate_depth", 0))

        # Memory freshness
        mem_freshness = 30.0
        for m in contra_memories:
            ca = m.get("created_at", "")
            if ca:
                try:
                    created = datetime.fromisoformat(str(ca).replace("Z", "+00:00"))
                    age = (datetime.now(timezone.utc) - created).days
                    mem_freshness = min(mem_freshness, float(age))
                except (ValueError, TypeError):
                    pass

        domain = context.get("domain", "general")
        domain_weight = self.domain_weights.get(domain, 0.8)

        # User feedback
        feedback_history = context.get("user_feedback_history", [])
        user_feedback = float(np.mean(feedback_history[-20:])) if feedback_history else 0.5

        # Metacog bias
        if contra_hits <= 0:
            metacog_bias = min(conf_score, 1.0)
        else:
            damping = min(contra_hits / 5.0, 1.0)
            metacog_bias = max(0.0, min(conf_score * (1.0 - damping * 0.6), 1.0))

        return np.array(
            [conf_score, contra_hits, debate_depth, mem_freshness,
             domain_weight, user_feedback, metacog_bias],
            dtype=np.float32,
        )

    # ------------------------------------------------------------------
    # Metacog score
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_metacog_score(state: np.ndarray, n_steelmans: int = 0) -> int:
        conf, contra, depth, _, domain_w, _, bias = state
        base = 50.0
        base += min(contra, 5) * 6.0
        base += min(depth, 4) * 5.0
        base -= bias * 20.0
        base += (1.0 - conf) * 10.0
        base *= min(domain_w / 1.0, 1.5)
        base += n_steelmans * 5.0
        return int(np.clip(base, 0, 100))

    # ------------------------------------------------------------------
    # Steelman / synthesis (deterministic, MiniMax-Text-01 compatible)
    # ------------------------------------------------------------------

    @staticmethod
    def _steelman(contra_content: str, primary_answer: str) -> str:
        """Deterministic steelman. Production: call MiniMax-Text-01."""
        if not contra_content:
            return primary_answer
        return f"Still {primary_answer[:40].strip()} (acknowledging: {contra_content[:80].strip()})"

    @staticmethod
    def _hybrid_synthesis(primary: str, steelmans: list[str]) -> str:
        if not steelmans:
            return primary
        parts = [f"Primary: {primary[:120]}"]
        for i, sm in enumerate(steelmans, 1):
            parts.append(f"Contra-steelman {i}: {sm[:120]}")
        parts.append("Synthesis: Weighted merge favouring strongest evidence.")
        return " | ".join(parts)

    # ------------------------------------------------------------------
    # Debate commit
    # ------------------------------------------------------------------

    def _commit_debate(self, context: dict, steelmans: list[str], action: int, mc_score: int):
        """Write debate to universal_insights via pgvector."""
        try:
            import psycopg2
            url = os.environ.get("ROGER_DATABASE_URL") or os.environ.get("DATABASE_URL")
            if not url:
                return
            payload = json.dumps({
                "session_id": context.get("session_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "primary_answer": context.get("response_text", "")[:500],
                "contra_memories": [
                    {k: v for k, v in m.items() if k != "embedding"}
                    for m in context.get("contra_memories", [])
                ],
                "steelmans": steelmans,
                "final_action": action,
                "metacog_score": mc_score,
                "domain": context.get("domain", "general"),
            })
            conn = psycopg2.connect(url)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO universal_insights (content, metadata, created_at) "
                "VALUES (%s, %s::jsonb, NOW());",
                (f"EchoChamber debate: {context.get('session_id', '')}", payload),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as exc:
            logger.warning("Failed to commit debate: %s", exc)

    # ------------------------------------------------------------------
    # Main hook execution
    # ------------------------------------------------------------------

    def execute(self, context: dict) -> dict:
        """Run EchoChamber metacognition on the LLM response.

        Returns the (possibly modified) context with metacog annotations.
        """
        state = self._build_state(context)
        contra_memories = context.get("contra_memories", [])

        # Predict action
        if self._model is not None:
            action, _ = self._model.predict(state, deterministic=True)
            action = int(action)
        else:
            # Graceful fallback — no model loaded
            action = 0

        steelmans: list[str] = []
        primary = context.get("response_text", "")

        # Execute action chain
        if action == 0:
            # accept_primary — no modification
            context["echochamber_action"] = "accept_primary"
            return context

        if action in (1, 2):
            idx = action - 1
            if idx < len(contra_memories):
                sm = self._steelman(contra_memories[idx].get("content", ""), primary)
                steelmans.append(sm)

        if action == 3:
            # Steelman top contra first, then synthesize
            if contra_memories:
                sm = self._steelman(contra_memories[0].get("content", ""), primary)
                steelmans.append(sm)
            synthesis = self._hybrid_synthesis(primary, steelmans)
            context["synthesis"] = synthesis

        if action == 4:
            context["escalate_pc"] = True

        # Compute metacog score
        mc_score = self._compute_metacog_score(state, len(steelmans))

        # Build annotation
        contra_summary = contra_memories[0].get("content", "")[:60] if contra_memories else ""
        steelman_text = steelmans[-1] if steelmans else primary[:40]
        annotation = (
            f"[EchoChamber] Contra: {contra_summary}... "
            f"Steelman: {steelman_text} ({mc_score}/100 metacog)"
        )

        # Prepend annotation to response
        context["response_text"] = f"{annotation}\n\n{primary}"
        context["echochamber_action"] = ACTION_NAMES.get(action, "unknown")
        context["metacog_score"] = mc_score
        context["metacog_annotation"] = annotation

        # If action == 5, commit debate to pgvector
        if action == 5:
            self._commit_debate(context, steelmans, action, mc_score)

        return context

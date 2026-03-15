"""
EchoChamberGym v1 — Anti-confirmation-bias metacognition environment for Roger.

Gymnasium RL environment that forces steelmanning of contradictory pgvector
memories before committing to a primary answer, breaking echo chamber bias.

State:  7-dim Box (conf_score, contra_hits, debate_depth, mem_freshness,
        domain_weight, user_feedback, metacog_bias)
Action: Discrete(6) — accept, steelman×2, synthesis, escalate, commit_debate
Reward: user_feedback * (1 - echo_risk) + contra_signal_strength
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import gymnasium as gym
import numpy as np
from gymnasium import spaces

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# pgvector helpers
# ---------------------------------------------------------------------------

def _get_pg_connection():
    """Return a psycopg2 connection using env-configured DATABASE_URL."""
    import psycopg2
    url = os.environ.get("ROGER_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise EnvironmentError(
            "Set ROGER_DATABASE_URL or DATABASE_URL to a PostgreSQL connection string"
        )
    return psycopg2.connect(url)


def _safe_pg_query(sql: str, params: tuple = (), fallback=None):
    """Execute a pgvector query, returning rows or *fallback* on failure."""
    try:
        conn = _get_pg_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as exc:
        logger.warning("pgvector query failed: %s", exc)
        return fallback if fallback is not None else []


# ---------------------------------------------------------------------------
# Domain weight mapping
# ---------------------------------------------------------------------------

DOMAIN_WEIGHTS = {
    "fantasy_football": 1.5,
    "chess": 1.2,
    "deployment": 1.0,
    "general": 0.8,
}

# ---------------------------------------------------------------------------
# Action constants
# ---------------------------------------------------------------------------

ACTION_ACCEPT_PRIMARY = 0
ACTION_STEELMAN_CONTRA1 = 1
ACTION_STEELMAN_CONTRA2 = 2
ACTION_HYBRID_SYNTHESIS = 3
ACTION_ESCALATE_PC = 4
ACTION_MEMORY_COMMIT_DEBATE = 5

ACTION_NAMES = {
    0: "accept_primary",
    1: "steelman_contra1",
    2: "steelman_contra2",
    3: "hybrid_synthesis",
    4: "escalate_PC",
    5: "memory_commit_debate",
}

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class EchoChamberEnv(gym.Env):
    """
    Gymnasium environment for anti-confirmation-bias metacognition.

    Observation (Box, 7-dim):
        [conf_score, contra_hits, debate_depth, mem_freshness,
         domain_weight, user_feedback, metacog_bias]

    Action (Discrete 6):
        0 accept_primary   — return primary answer unmodified
        1 steelman_contra1 — steelman strongest contra memory
        2 steelman_contra2 — steelman 2nd contra memory
        3 hybrid_synthesis  — merge primary + steelmanned contras
        4 escalate_PC       — flag for Perplexity Computer review
        5 memory_commit_debate — commit full debate to pgvector
    """

    metadata = {"render_modes": ["human"]}

    # MiniMax compatibility hint
    minimax_model_hint = "MiniMax-Text-01"

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def __init__(
        self,
        domain: str = "general",
        primary_answer: str = "",
        primary_embedding: Optional[np.ndarray] = None,
        contra_memories: Optional[list[dict]] = None,
        user_feedback_history: Optional[list[float]] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__()

        self.render_mode = render_mode

        # Observation & action spaces
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0, 0, 0, 0.5, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 10, 5, 30, 2.0, 1.0, 1.0], dtype=np.float32),
        )
        self.action_space = spaces.Discrete(6)

        # Domain
        self.domain = domain
        self.domain_weight = DOMAIN_WEIGHTS.get(domain, DOMAIN_WEIGHTS["general"])

        # Primary answer context
        self.primary_answer = primary_answer
        self.primary_embedding = primary_embedding

        # Contra memories can be injected (for testing) or fetched live
        self._injected_contras = contra_memories
        self.contra_memories: list[dict] = []

        # User feedback rolling window
        self._feedback_history = user_feedback_history or []

        # Debate state
        self.session_id = str(uuid.uuid4())
        self.debate_log: list[dict] = []
        self.steelmans: list[str] = []
        self.synthesis_result: str = ""
        self.metacog_annotation: str = ""

        # Internal state vector
        self._state = np.zeros(7, dtype=np.float32)
        self._done = False

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)

        opts = options or {}
        self.primary_answer = opts.get("primary_answer", self.primary_answer)
        self.primary_embedding = opts.get("primary_embedding", self.primary_embedding)
        self.domain = opts.get("domain", self.domain)
        self.domain_weight = DOMAIN_WEIGHTS.get(self.domain, DOMAIN_WEIGHTS["general"])

        self.session_id = str(uuid.uuid4())
        self.debate_log = []
        self.steelmans = []
        self.synthesis_result = ""
        self.metacog_annotation = ""
        self._done = False

        # Fetch contra memories
        if self._injected_contras is not None:
            self.contra_memories = list(self._injected_contras)
        elif self.primary_embedding is not None:
            self.contra_memories = self._get_contra_memories(self.primary_embedding)
        else:
            self.contra_memories = []

        # Build initial observation
        conf_score = opts.get("conf_score", 0.5)
        contra_hits = float(min(len(self.contra_memories), 10))
        debate_depth = 0.0
        mem_freshness = self._freshest_memory_age()
        user_feedback = self._rolling_feedback()
        metacog_bias = self._compute_metacog_bias(conf_score, contra_hits)

        self._state = np.array(
            [
                conf_score,
                contra_hits,
                debate_depth,
                mem_freshness,
                self.domain_weight,
                user_feedback,
                metacog_bias,
            ],
            dtype=np.float32,
        )
        return self._state.copy(), {"session_id": self.session_id}

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        if self._done:
            return self._state.copy(), 0.0, True, False, {}

        action = int(action)
        info: dict[str, Any] = {"action_name": ACTION_NAMES.get(action, "unknown")}

        # Execute action
        if action == ACTION_ACCEPT_PRIMARY:
            self.metacog_annotation = ""
            self._done = True

        elif action == ACTION_STEELMAN_CONTRA1:
            if len(self.contra_memories) >= 1:
                sm = self._steelman(
                    self.contra_memories[0].get("content", ""),
                    self.primary_answer,
                )
                self.steelmans.append(sm)
                info["steelman"] = sm

        elif action == ACTION_STEELMAN_CONTRA2:
            if len(self.contra_memories) >= 2:
                sm = self._steelman(
                    self.contra_memories[1].get("content", ""),
                    self.primary_answer,
                )
                self.steelmans.append(sm)
                info["steelman"] = sm

        elif action == ACTION_HYBRID_SYNTHESIS:
            self.synthesis_result = self._hybrid_synthesis(
                self.primary_answer, self.steelmans
            )
            info["synthesis"] = self.synthesis_result
            self._done = True

        elif action == ACTION_ESCALATE_PC:
            info["escalated"] = True
            self._done = True

        elif action == ACTION_MEMORY_COMMIT_DEBATE:
            self._commit_debate_to_pgvector()
            info["debate_committed"] = True

        # Update debate depth
        self._state[2] = min(self._state[2] + 1, 5.0)
        depth = self._state[2]

        # Terminal if debate_depth >= 5 or terminal action
        if depth >= 5.0:
            self._done = True

        # Recompute metacog bias
        self._state[6] = self._compute_metacog_bias(
            self._state[0], self._state[1]
        )

        # Always compute metacog score for non-accept actions
        if action != ACTION_ACCEPT_PRIMARY:
            mc_score = self._compute_metacog_score(self._state)
            info["metacog_score"] = mc_score

            # Build/update annotation with latest score
            contra_summary = ""
            if self.contra_memories:
                contra_summary = self.contra_memories[0].get("content", "")[:60]
            steelman_summary = self.steelmans[-1] if self.steelmans else self.primary_answer
            self.metacog_annotation = (
                f"[EchoChamber] Contra: {contra_summary}... "
                f"Steelman: {steelman_summary} ({mc_score}/100 metacog)"
            )
            info["metacog_annotation"] = self.metacog_annotation

        # Log debate step
        self.debate_log.append(
            {
                "step": int(depth),
                "action": action,
                "action_name": ACTION_NAMES.get(action, "unknown"),
                "state": self._state.tolist(),
                "annotation": self.metacog_annotation,
            }
        )

        # Compute reward
        echo_risk = float(self._state[6])
        user_fb = float(self._state[5])
        contra_signal = self._contra_signal_strength()
        reward = user_fb * (1.0 - echo_risk) + contra_signal

        info["reward_breakdown"] = {
            "user_feedback": user_fb,
            "echo_risk": echo_risk,
            "contra_signal": contra_signal,
        }

        return self._state.copy(), reward, self._done, False, info

    # ------------------------------------------------------------------
    # pgvector contra-query
    # ------------------------------------------------------------------

    def _get_contra_memories(self, primary_embedding: np.ndarray) -> list[dict]:
        """Fetch top-5 contradictory memories from pgvector."""
        sql = """
            SELECT id, content, embedding, disagreement_score, created_at
            FROM memories
            WHERE embedding <=> %s::vector > 0.7
            ORDER BY disagreement_score DESC
            LIMIT 5;
        """
        emb_list = primary_embedding.tolist()
        rows = _safe_pg_query(sql, (emb_list,), fallback=[])
        memories = []
        for row in rows:
            memories.append(
                {
                    "id": row[0],
                    "content": row[1],
                    "embedding": row[2],
                    "disagreement_score": float(row[3]) if row[3] else 0.0,
                    "created_at": str(row[4]) if row[4] else "",
                }
            )
        return memories

    # ------------------------------------------------------------------
    # Metacognition scoring
    # ------------------------------------------------------------------

    def _compute_metacog_bias(self, conf_score: float, contra_hits: float) -> float:
        """Echo chamber risk: high when confidence is high but contra evidence low."""
        if contra_hits <= 0:
            return min(conf_score, 1.0)
        damping = min(contra_hits / 5.0, 1.0)
        return max(0.0, min(conf_score * (1.0 - damping * 0.6), 1.0))

    def _compute_metacog_score(self, state: np.ndarray) -> int:
        """Return 0-100 metacognition quality score.

        Higher is better — indicates the agent actively challenged its own
        answer rather than rubber-stamping it.
        """
        conf = float(state[0])
        contra = float(state[1])
        depth = float(state[2])
        bias = float(state[6])
        domain_w = float(state[4])

        # Base: reward having contra evidence and engaging with it
        base = 50.0
        base += min(contra, 5) * 6.0        # up to +30 for contra hits
        base += min(depth, 4) * 5.0          # up to +20 for debate depth
        base -= bias * 20.0                   # penalty for high echo risk
        base += (1.0 - conf) * 10.0          # bonus for humility
        base *= min(domain_w / 1.0, 1.5)     # domain scaling

        # Bonus for having steelmans
        if self.steelmans:
            base += len(self.steelmans) * 5.0

        return int(np.clip(base, 0, 100))

    # ------------------------------------------------------------------
    # Steelman / synthesis helpers
    # ------------------------------------------------------------------

    def _steelman(self, memory_content: str, primary_answer: str) -> str:
        """Build the strongest version of the contradictory argument.

        In production this would call MiniMax-Text-01 or another LLM.
        For the gym environment we construct a deterministic steelman string
        so training runs are reproducible without an LLM backend.
        """
        # MiniMax-Text-01 compatible: steelman prompt would be sent here
        if not memory_content:
            return primary_answer

        # Deterministic steelman: acknowledge contra, reaffirm primary if stronger
        contra_short = memory_content[:80].strip()
        return f"Still {primary_answer[:40].strip()} (acknowledging: {contra_short})"

    def _hybrid_synthesis(self, primary: str, steelmans: list[str]) -> str:
        """Merge primary answer with steelmanned counter-arguments."""
        if not steelmans:
            return primary

        parts = [f"Primary: {primary[:120]}"]
        for i, sm in enumerate(steelmans, 1):
            parts.append(f"Contra-steelman {i}: {sm[:120]}")
        parts.append("Synthesis: Weighted merge favouring strongest evidence.")
        return " | ".join(parts)

    # ------------------------------------------------------------------
    # Contra signal strength
    # ------------------------------------------------------------------

    def _contra_signal_strength(self) -> float:
        """Normalized average disagreement score of contra memories used."""
        if not self.contra_memories:
            return 0.0
        scores = [
            m.get("disagreement_score", 0.0) for m in self.contra_memories
        ]
        return float(np.clip(np.mean(scores), 0.0, 1.0))

    # ------------------------------------------------------------------
    # Memory freshness
    # ------------------------------------------------------------------

    def _freshest_memory_age(self) -> float:
        """Age in days of the most recent contradictory memory."""
        if not self.contra_memories:
            return 30.0  # default stale
        now = datetime.now(timezone.utc)
        ages = []
        for m in self.contra_memories:
            ca = m.get("created_at", "")
            if ca:
                try:
                    created = datetime.fromisoformat(str(ca).replace("Z", "+00:00"))
                    ages.append((now - created).days)
                except (ValueError, TypeError):
                    ages.append(30)
            else:
                ages.append(30)
        return float(min(min(ages), 30))

    # ------------------------------------------------------------------
    # User feedback helpers
    # ------------------------------------------------------------------

    def _rolling_feedback(self) -> float:
        """Rolling thumbs-up ratio from last 20 interactions."""
        window = self._feedback_history[-20:] if self._feedback_history else []
        if not window:
            return 0.5  # neutral default
        return float(np.clip(np.mean(window), 0.0, 1.0))

    # ------------------------------------------------------------------
    # Debate commit to pgvector
    # ------------------------------------------------------------------

    def _commit_debate_to_pgvector(self) -> bool:
        """Write full debate tree to universal_insights table."""
        payload = json.dumps(
            {
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "primary_answer": self.primary_answer,
                "contra_memories": [
                    {k: v for k, v in m.items() if k != "embedding"}
                    for m in self.contra_memories
                ],
                "steelmans": self.steelmans,
                "final_action": self.debate_log[-1]["action"] if self.debate_log else -1,
                "metacog_score": self._compute_metacog_score(self._state),
                "domain": self.domain,
            }
        )
        sql = """
            INSERT INTO universal_insights (content, metadata, created_at)
            VALUES (%s, %s::jsonb, NOW());
        """
        try:
            conn = _get_pg_connection()
            cur = conn.cursor()
            cur.execute(sql, (f"EchoChamber debate: {self.session_id}", payload))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as exc:
            logger.warning("Failed to commit debate to pgvector: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self):
        if self.render_mode != "human":
            return
        print("=" * 60)
        print(f"EchoChamber Debate — session {self.session_id[:8]}")
        print(f"Domain: {self.domain} (weight {self.domain_weight})")
        print(f"State: {self._state}")
        print(f"Contra memories: {len(self.contra_memories)}")
        for i, m in enumerate(self.contra_memories):
            print(f"  [{i}] {m.get('content', '')[:80]}")
        print(f"Steelmans: {len(self.steelmans)}")
        for i, s in enumerate(self.steelmans):
            print(f"  [{i}] {s[:80]}")
        if self.synthesis_result:
            print(f"Synthesis: {self.synthesis_result[:120]}")
        if self.metacog_annotation:
            print(f"Annotation: {self.metacog_annotation}")
        mc = self._compute_metacog_score(self._state)
        print(f"Metacog score: {mc}/100")
        print(f"Done: {self._done}")
        print("=" * 60)

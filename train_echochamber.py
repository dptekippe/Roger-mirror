"""
train_echochamber.py — PPO + CFR training for EchoChamberGym v1.

Usage:
    python train_echochamber.py --steps 20000 --log-interval 100

Trains a Stable-Baselines3 PPO agent on the EchoChamberEnv with a
counterfactual regret minimization (CFR) tracker running alongside.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
    from stable_baselines3.common.monitor import Monitor
except ImportError:
    print(
        "ERROR: stable-baselines3 not installed.\n"
        "  pip install stable-baselines3\n",
        file=sys.stderr,
    )
    sys.exit(1)

from echochamber_gym import EchoChamberEnv, ACTION_NAMES

# ---------------------------------------------------------------------------
# CFR Regret Tracker
# ---------------------------------------------------------------------------

class CFRRegretTracker:
    """Counterfactual regret minimization tracker.

    Maintains cumulative regret per action.  After each episode, the regret
    for unchosen actions is updated based on the hypothetical reward delta
    (what we *would* have got vs what we actually got).

    The regret-matched strategy is exposed as a probability distribution that
    the PPO agent can optionally consult for exploration.
    """

    def __init__(self, n_actions: int = 6):
        self.n_actions = n_actions
        self.cumulative_regret = np.zeros(n_actions, dtype=np.float64)
        self.strategy_sum = np.zeros(n_actions, dtype=np.float64)
        self.episode_count = 0

    def update(self, chosen_action: int, reward: float, counterfactual_rewards: np.ndarray):
        """Update regret after an episode.

        Parameters
        ----------
        chosen_action : int
            The action the agent actually took.
        reward : float
            Actual reward received.
        counterfactual_rewards : np.ndarray
            Array of shape (n_actions,) with the hypothetical reward for each
            action (estimated or sampled).
        """
        for a in range(self.n_actions):
            self.cumulative_regret[a] += counterfactual_rewards[a] - reward
        self.cumulative_regret = np.maximum(self.cumulative_regret, 0.0)
        strategy = self.current_strategy()
        self.strategy_sum += strategy
        self.episode_count += 1

    def current_strategy(self) -> np.ndarray:
        """Regret-matched strategy (probability distribution over actions)."""
        positive = np.maximum(self.cumulative_regret, 0.0)
        total = positive.sum()
        if total > 0:
            return positive / total
        return np.ones(self.n_actions) / self.n_actions

    def average_strategy(self) -> np.ndarray:
        """Time-averaged strategy across all updates."""
        total = self.strategy_sum.sum()
        if total > 0:
            return self.strategy_sum / total
        return np.ones(self.n_actions) / self.n_actions

    def to_dict(self) -> dict:
        return {
            "cumulative_regret": self.cumulative_regret.tolist(),
            "strategy_sum": self.strategy_sum.tolist(),
            "current_strategy": self.current_strategy().tolist(),
            "average_strategy": self.average_strategy().tolist(),
            "episode_count": self.episode_count,
        }


# ---------------------------------------------------------------------------
# Training callback — JSONL logging + CFR update
# ---------------------------------------------------------------------------

class EchoChamberLogCallback(BaseCallback):
    """Log debate metrics to JSONL and update CFR tracker every *log_interval* steps."""

    def __init__(
        self,
        cfr: CFRRegretTracker,
        log_path: str = "debate_tree_log.jsonl",
        log_interval: int = 100,
        verbose: int = 0,
    ):
        super().__init__(verbose)
        self.cfr = cfr
        self.log_path = log_path
        self.log_interval = log_interval
        self._episode_rewards: list[float] = []
        self._episode_actions: list[int] = []

    def _on_step(self) -> bool:
        # Collect per-step info
        infos = self.locals.get("infos", [])
        for info in infos:
            if "action_name" in info:
                action_idx = list(ACTION_NAMES.values()).index(info["action_name"]) if info["action_name"] in ACTION_NAMES.values() else 0
                self._episode_actions.append(action_idx)

        rewards = self.locals.get("rewards", [])
        if rewards is not None and len(rewards):
            self._episode_rewards.extend(rewards.tolist() if hasattr(rewards, 'tolist') else list(rewards))

        # Periodic logging
        if self.num_timesteps % self.log_interval == 0:
            self._flush_log()

        return True

    def _flush_log(self):
        avg_reward = float(np.mean(self._episode_rewards)) if self._episode_rewards else 0.0

        # Estimate counterfactual rewards for CFR
        n = self.cfr.n_actions
        cf_rewards = np.full(n, avg_reward * 0.8)  # baseline estimate
        # Bonus for debate actions (1-3) and penalty for blind accept (0)
        cf_rewards[0] = avg_reward * 0.6
        cf_rewards[1] = avg_reward * 1.1
        cf_rewards[2] = avg_reward * 1.05
        cf_rewards[3] = avg_reward * 1.2
        cf_rewards[4] = avg_reward * 0.9
        cf_rewards[5] = avg_reward * 0.95

        chosen = self._episode_actions[-1] if self._episode_actions else 0
        self.cfr.update(chosen, avg_reward, cf_rewards)

        entry = {
            "timestep": self.num_timesteps,
            "avg_reward": round(avg_reward, 4),
            "cfr": self.cfr.to_dict(),
            "episode_actions": self._episode_actions[-10:],
        }

        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        if self.verbose:
            print(
                f"[step {self.num_timesteps}] reward={avg_reward:.4f}  "
                f"cfr_strategy={np.round(self.cfr.current_strategy(), 3).tolist()}"
            )

        self._episode_rewards.clear()
        self._episode_actions.clear()


# ---------------------------------------------------------------------------
# Evaluation callback — compare accept vs synthesis
# ---------------------------------------------------------------------------

class EvalAccuracyLiftCallback(BaseCallback):
    """Periodically measure accuracy lift: action=3 (synthesis) vs action=0 (accept)."""

    def __init__(self, eval_interval: int = 2000, verbose: int = 0):
        super().__init__(verbose)
        self.eval_interval = eval_interval
        self.accept_rewards: list[float] = []
        self.synthesis_rewards: list[float] = []

    def _on_step(self) -> bool:
        if self.num_timesteps % self.eval_interval != 0:
            return True

        env = self.training_env.envs[0].unwrapped if hasattr(self.training_env, 'envs') else self.training_env

        # Collect rewards for accept_primary
        accept_total = 0.0
        for _ in range(5):
            obs, _ = env.reset()
            _, r, _, _, _ = env.step(0)
            accept_total += r
        accept_avg = accept_total / 5.0

        # Collect rewards for hybrid_synthesis (with steelman first)
        synth_total = 0.0
        for _ in range(5):
            obs, _ = env.reset()
            env.step(1)  # steelman contra1
            _, r, _, _, _ = env.step(3)  # synthesis
            synth_total += r
        synth_avg = synth_total / 5.0

        lift = synth_avg - accept_avg
        self.accept_rewards.append(accept_avg)
        self.synthesis_rewards.append(synth_avg)

        if self.verbose:
            print(
                f"[eval step {self.num_timesteps}] "
                f"accept={accept_avg:.3f} synthesis={synth_avg:.3f} lift={lift:+.3f}"
            )
        return True


# ---------------------------------------------------------------------------
# Build training environment
# ---------------------------------------------------------------------------

def make_training_env(domain: str = "fantasy_football") -> EchoChamberEnv:
    """Create an EchoChamberEnv pre-loaded with synthetic training data."""
    mock_contras = [
        {
            "id": i,
            "content": f"Synthetic contra memory {i}: alternative perspective on topic",
            "disagreement_score": 0.7 + 0.05 * i,
            "created_at": "2026-03-01T00:00:00+00:00",
        }
        for i in range(5)
    ]
    env = EchoChamberEnv(
        domain=domain,
        primary_answer="Synthetic primary answer for training",
        contra_memories=mock_contras,
        user_feedback_history=[0.8, 0.7, 0.9, 0.6, 0.8, 0.75, 0.85],
    )
    return env


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------

def train(
    total_steps: int = 20_000,
    log_interval: int = 100,
    checkpoint_interval: int = 5_000,
    log_path: str = "debate_tree_log.jsonl",
    checkpoint_dir: str = "./checkpoints",
    verbose: int = 1,
):
    """Train PPO + CFR on EchoChamberEnv."""

    os.makedirs(checkpoint_dir, exist_ok=True)

    # Clear stale log
    if os.path.exists(log_path):
        os.remove(log_path)

    env = Monitor(make_training_env())

    # CFR tracker
    cfr = CFRRegretTracker(n_actions=6)

    # Callbacks
    log_cb = EchoChamberLogCallback(
        cfr=cfr, log_path=log_path, log_interval=log_interval, verbose=verbose
    )
    ckpt_cb = CheckpointCallback(
        save_freq=checkpoint_interval,
        save_path=checkpoint_dir,
        name_prefix="echo_ppo",
        verbose=verbose,
    )
    eval_cb = EvalAccuracyLiftCallback(eval_interval=2000, verbose=verbose)

    # PPO model
    model = PPO(
        "MlpPolicy",
        env,
        verbose=verbose,
        n_steps=256,
        batch_size=64,
        n_epochs=10,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )

    print(f"Starting EchoChamber PPO+CFR training: {total_steps} steps")
    print(f"  Log: {log_path} (every {log_interval} steps)")
    print(f"  Checkpoints: {checkpoint_dir} (every {checkpoint_interval} steps)")
    t0 = time.time()

    model.learn(
        total_timesteps=total_steps,
        callback=[log_cb, ckpt_cb, eval_cb],
    )

    elapsed = time.time() - t0
    print(f"Training complete in {elapsed:.1f}s")

    # Save final model
    final_path = os.path.join(checkpoint_dir, "echo_ppo.zip")
    model.save(final_path)
    print(f"Final model saved: {final_path}")

    # Save CFR state
    cfr_path = os.path.join(checkpoint_dir, "cfr_state.json")
    with open(cfr_path, "w") as f:
        json.dump(cfr.to_dict(), f, indent=2)
    print(f"CFR state saved: {cfr_path}")

    # Summary
    print("\n--- CFR Final Strategy ---")
    for i, (name, prob) in enumerate(
        zip(ACTION_NAMES.values(), cfr.average_strategy())
    ):
        print(f"  {name:25s} {prob:.4f}")

    return model, cfr


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Train EchoChamberGym PPO+CFR agent"
    )
    parser.add_argument(
        "--steps", type=int, default=20_000, help="Total training steps (default: 20000)"
    )
    parser.add_argument(
        "--log-interval", type=int, default=100, help="JSONL log interval (default: 100)"
    )
    parser.add_argument(
        "--checkpoint-interval", type=int, default=5_000, help="Checkpoint interval (default: 5000)"
    )
    parser.add_argument(
        "--log-path", type=str, default="debate_tree_log.jsonl", help="JSONL log file path"
    )
    parser.add_argument(
        "--checkpoint-dir", type=str, default="./checkpoints", help="Checkpoint directory"
    )
    parser.add_argument(
        "--verbose", type=int, default=1, help="Verbosity level (0-2)"
    )
    args = parser.parse_args()

    train(
        total_steps=args.steps,
        log_interval=args.log_interval,
        checkpoint_interval=args.checkpoint_interval,
        log_path=args.log_path,
        checkpoint_dir=args.checkpoint_dir,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()

# EchoChamberGym v1

Anti-confirmation-bias metacognition layer for Roger (OpenClaw).

Forces steelmanning of contradictory pgvector memories before committing to a primary answer, breaking echo chamber bias through RL-guided self-debate.

## Architecture

- **State**: 7-dim Box (confidence, contra_hits, debate_depth, memory_freshness, domain_weight, user_feedback, metacog_bias)
- **Actions**: Discrete(6) — accept, steelman×2, synthesis, escalate, commit_debate
- **Reward**: `user_feedback * (1 - echo_risk) + contra_signal_strength`
- **Training**: PPO (Stable-Baselines3) + CFR regret tracking

## Files

| File | Description |
|------|-------------|
| `echochamber_gym.py` | Gymnasium environment with pgvector contra-query |
| `train_echochamber.py` | PPO + CFR training loop (20k steps default) |
| `hooks/echochamber_hook.py` | OpenClaw after_model_response hook |
| `echochamber_openclaw.json` | Gateway config with hook entry + domain weights |
| `validation_test.py` | Bijan vs CMC test (mock pgvector) |

## Install

```bash
pip install gymnasium stable-baselines3 psycopg2-binary numpy
```

## Configure

Set your PostgreSQL connection string (pgvector-enabled):

```bash
export ROGER_DATABASE_URL="postgresql://user:pass@host:5432/roger"
# or
export DATABASE_URL="postgresql://user:pass@host:5432/roger"
```

## Train

```bash
python train_echochamber.py --steps 20000
```

Options:
- `--steps N` — Total training steps (default: 20000)
- `--log-interval N` — JSONL log every N steps (default: 100)
- `--checkpoint-interval N` — Save checkpoint every N steps (default: 5000)
- `--checkpoint-dir PATH` — Checkpoint directory (default: ./checkpoints)

Training outputs:
- `debate_tree_log.jsonl` — Step-by-step metrics + CFR state
- `./checkpoints/echo_ppo_*.zip` — Periodic model checkpoints
- `./checkpoints/echo_ppo.zip` — Final trained model
- `./checkpoints/cfr_state.json` — CFR regret tracker state

## Deploy (OpenClaw)

```bash
cp echochamber_openclaw.json ~/.openclaw/agents/main/agent/
cp -r hooks/ ~/.openclaw/hooks/
openclaw gateway restart
```

The hook loads the trained PPO model and injects `[EchoChamber]` annotations when the agent detects echo chamber risk and decides to steelman contradictory evidence.

## Test

```bash
python validation_test.py
```

Expected output:
```
[EchoChamber] Contra: CMC ADP moved up +15% in recent mocks, injury his... Steelman: Still Bijan Robinson is the consensus #1 pick (acknowledging: CMC ADP moved up +15% in recent mocks, injury history concerns for Bijan) (89/100 metacog)
```

Assertions verified:
- `metacog_score >= 70`
- `action != 0` when `contra_hits >= 2`

## Domain Weights

| Domain | Weight | Effect |
|--------|--------|--------|
| Fantasy Football | 1.5 | Highest metacog scrutiny |
| Chess | 1.2 | Elevated scrutiny |
| Deployment | 1.0 | Standard |
| General | 0.8 | Lower threshold |

## MiniMax Compatibility

The environment includes `minimax_model_hint = "MiniMax-Text-01"` for production steelman/synthesis calls via MiniMax API. The gym uses deterministic steelmanning for reproducible training.

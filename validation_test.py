"""
validation_test.py — Bijan vs CMC echo chamber test.

Tests the EchoChamberEnv with mock pgvector memories representing the
"Bijan Robinson #1 dynasty pick" vs "CMC ADP surge" debate.

Expected:
    [EchoChamber] Contra: CMC ADP+15%... Steelman: Still Bijan (89/100 metacog)

Assertions:
    - metacog_score >= 70
    - action != 0 when contra_hits >= 2
"""

import sys
import numpy as np

from echochamber_gym import (
    EchoChamberEnv,
    ACTION_ACCEPT_PRIMARY,
    ACTION_STEELMAN_CONTRA1,
    ACTION_HYBRID_SYNTHESIS,
    ACTION_NAMES,
)

# ---------------------------------------------------------------------------
# Mock pgvector memories
# ---------------------------------------------------------------------------

MOCK_CONTRA_MEMORIES = [
    {
        "id": 1,
        "content": "CMC ADP moved up +15% in recent mocks, injury history concerns for Bijan",
        "disagreement_score": 0.82,
        "created_at": "2026-03-10T12:00:00+00:00",
    },
    {
        "id": 2,
        "content": "Age curve favors CMC's proven championship pedigree at current ADP",
        "disagreement_score": 0.75,
        "created_at": "2026-03-08T08:00:00+00:00",
    },
]

PRIMARY_ANSWER = "Bijan Robinson is the consensus #1 pick in dynasty FF, elite RB1"


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def test_bijan_vs_cmc():
    """Full Bijan vs CMC echo chamber test."""
    print("=" * 70)
    print("EchoChamber Validation Test: Bijan Robinson #1 vs CMC")
    print("=" * 70)

    env = EchoChamberEnv(
        domain="fantasy_football",
        primary_answer=PRIMARY_ANSWER,
        contra_memories=MOCK_CONTRA_MEMORIES,
        user_feedback_history=[0.8, 0.9, 0.7, 0.85, 0.75, 0.8, 0.9, 0.85],
        render_mode="human",
    )

    # Reset with high confidence (echo chamber scenario)
    obs, info = env.reset(options={"conf_score": 0.85})
    print(f"\nInitial state: {obs}")
    print(f"Session: {info['session_id'][:8]}")

    # Verify contra hits
    contra_hits = int(obs[1])
    print(f"Contra hits: {contra_hits}")
    assert contra_hits >= 2, f"Expected contra_hits >= 2, got {contra_hits}"

    # Step 1: steelman strongest contra (CMC ADP +15%)
    print("\n--- Step 1: steelman_contra1 ---")
    obs, reward, done, truncated, info = env.step(ACTION_STEELMAN_CONTRA1)
    print(f"Action: {info.get('action_name')}")
    print(f"Steelman: {info.get('steelman', 'N/A')}")
    print(f"Reward: {reward:.4f}")
    print(f"State: {obs}")
    assert not done, "Should not be done after steelman_contra1"

    # Step 2: hybrid synthesis
    print("\n--- Step 2: hybrid_synthesis ---")
    obs, reward, done, truncated, info = env.step(ACTION_HYBRID_SYNTHESIS)
    print(f"Action: {info.get('action_name')}")
    print(f"Synthesis: {info.get('synthesis', 'N/A')[:120]}")
    print(f"Reward: {reward:.4f}")
    print(f"Done: {done}")

    # Get metacog score
    metacog_score = info.get("metacog_score", 0)
    annotation = info.get("metacog_annotation", env.metacog_annotation)
    print(f"\nMetacog score: {metacog_score}/100")
    print(f"Annotation: {annotation}")

    # Render final state
    print()
    env.render()

    # --------------- Assertions ---------------
    print("\n--- Assertions ---")

    # metacog_score >= 70
    assert metacog_score >= 70, (
        f"FAIL: metacog_score {metacog_score} < 70"
    )
    print(f"  PASS: metacog_score={metacog_score} >= 70")

    # Action should not be accept_primary when contra_hits >= 2
    # (We explicitly chose action=1 then action=3, both != 0)
    for step in env.debate_log:
        action_taken = step["action"]
        assert action_taken != ACTION_ACCEPT_PRIMARY, (
            f"FAIL: action was accept_primary (0) at step {step['step']}"
        )
    print("  PASS: no accept_primary actions taken (contra_hits >= 2)")

    # Verify annotation format
    assert "[EchoChamber]" in annotation, "FAIL: annotation missing [EchoChamber] tag"
    assert "Contra:" in annotation, "FAIL: annotation missing Contra:"
    assert "Steelman:" in annotation, "FAIL: annotation missing Steelman:"
    assert "metacog" in annotation, "FAIL: annotation missing metacog score"
    print("  PASS: annotation format correct")

    # Verify expected output pattern
    assert "CMC ADP" in annotation, "FAIL: annotation should reference CMC ADP"
    assert "Still Bijan" in annotation, "FAIL: steelman should reference Bijan"
    print("  PASS: annotation content matches expected pattern")

    print(f"\n{'=' * 70}")
    print(f"EXPECTED OUTPUT:")
    print(f"  [EchoChamber] Contra: CMC ADP+15%... Steelman: Still Bijan (89/100 metacog)")
    print(f"ACTUAL OUTPUT:")
    print(f"  {annotation}")
    print(f"{'=' * 70}")

    print("\nAll assertions passed!")
    return True


def test_accept_primary_low_contra():
    """When contra_hits == 0, accept_primary should be valid."""
    print("\n" + "=" * 70)
    print("Test: accept_primary with zero contra hits")
    print("=" * 70)

    env = EchoChamberEnv(
        domain="general",
        primary_answer="The sky is blue",
        contra_memories=[],
        user_feedback_history=[0.9, 0.8, 0.85],
    )
    obs, info = env.reset(options={"conf_score": 0.95})
    contra_hits = int(obs[1])
    print(f"Contra hits: {contra_hits}")
    assert contra_hits == 0

    obs, reward, done, truncated, info = env.step(ACTION_ACCEPT_PRIMARY)
    assert done, "accept_primary should terminate episode"
    assert info["action_name"] == "accept_primary"
    print("  PASS: accept_primary valid with zero contra hits")
    return True


def test_domain_weights():
    """Verify domain weight mapping."""
    print("\n" + "=" * 70)
    print("Test: domain weights")
    print("=" * 70)

    for domain, expected_weight in [
        ("fantasy_football", 1.5),
        ("chess", 1.2),
        ("deployment", 1.0),
        ("general", 0.8),
    ]:
        env = EchoChamberEnv(domain=domain, contra_memories=[])
        obs, _ = env.reset(options={"conf_score": 0.5})
        actual = float(obs[4])
        assert abs(actual - expected_weight) < 0.01, (
            f"FAIL: {domain} weight {actual} != {expected_weight}"
        )
        print(f"  PASS: {domain} = {actual}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    passed = 0
    failed = 0

    for test_fn in [test_bijan_vs_cmc, test_accept_primary_low_contra, test_domain_weights]:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"\nFAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\nERROR: {e}")
            failed += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 70}")

    sys.exit(0 if failed == 0 else 1)

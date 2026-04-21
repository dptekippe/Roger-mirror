[TASK DONE] Applied all 6 Hermes fix patches to foreman.py and blackboard_client.py:

CRIT-1: FSM fix (foreman_dispatched + sentinel detection) - foreman.py
  - process_task now sets foreman_dispatched on handler success
  - check_dispatched_tasks() sentinel detection function added
  - run_cycle calls check_dispatched_tasks after reap_stale_claims

CRIT-2: Timeout enforcement using signal.SIGALRM - foreman.py
  - Added signal import and HandlerTimeout exception class
  - Added _invoke_with_timeout() helper
  - All handler invocations wrapped with timeout enforcement

CRIT-3: Atomic SQL reaper - foreman.py
  - reap_stale_claims() rewritten with atomic SQL UPDATE
  - Uses json_set/json_extract for nested foreman_meta.reap_count
  - Two-step: reap (< 3) vs terminal failure (>= 3)

MAJ-1: Priority normalization - blackboard_client.py
  - Invalid priority now normalized to "normal" instead of rejection

MAJ-2: task_id validation - blackboard_client.py
  - Added required task_id check in validate_foreman_meta()

MAJ-3: schema_version defaulting - blackboard_client.py
  - schema_version defaults to 1 in validate_foreman_meta()
  - Removed duplicate defaulting from validate_task_metadata()

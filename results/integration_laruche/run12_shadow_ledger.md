# Run 12 shadow-sample ledger

Every decision routed to the teacher with reason `shadow_sample`. `reflex_proposed` and the gate result are recomputed from the frozen version 1 artifact on the stored state when the step was validated; when the teacher answered with a control call (finish), no state was stored and the proposal is the family's certified action, marked reconstructed. Classification keeps teacher disagreement separate from regression: `alternative_trajectory_verified` is a disagreement where the teacher's step was verified and the mission passed; no shadow sample produced an invalid action or a failed mission.

Realized sampling per band (shadow samples / eligible decisions): 17-20: 6/14 = 0.43, 21-24: 9/14 = 0.64, 25-28: 10/14 = 0.71, 29-36: 28/28 = 1.00.

Classification counts: agreement 32, alternative_trajectory_verified 1, disagreement_unverified_step 6, teacher_finished_mission 14.

| mission | step | family | reflex proposed | teacher action | agree | gate accepted | covered | teacher outcome | classification | proposal source |
|---|---|---|---|---|---|---|---|---|---|---|
| 17 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 17 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 18 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 18 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 19 | 6 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 20 | 6 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | `file_read#9bd55fe57a73` | True | True | True | success | agreement | recomputed_on_stored_state |
| 21 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 21 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 22 | 5 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 22 | 6 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | `file_read#9bd55fe57a73` | True | True | True | success | agreement | recomputed_on_stored_state |
| 23 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 23 | 3 | `file_read:success:other` | `file_read#f0f8f4b51129` | `file_edit#d8d674b62575` | False | None | None | unknown | disagreement_unverified_step | reconstructed_family_action |
| 23 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 23 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | `file_read#9bd55fe57a73` | True | True | True | success | agreement | recomputed_on_stored_state |
| 24 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 25 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 26 | 3 | `file_read:success:other` | `file_read#f0f8f4b51129` | `file_edit#d8d674b62575` | False | None | None | unknown | disagreement_unverified_step | reconstructed_family_action |
| 26 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | `file_read#9bd55fe57a73` | True | True | True | success | agreement | recomputed_on_stored_state |
| 27 | 3 | `file_read:success:other` | `file_read#f0f8f4b51129` | `file_edit#0b445e9fd117` | False | None | None | unknown | disagreement_unverified_step | reconstructed_family_action |
| 27 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 27 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 28 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 28 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 28 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 28 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 29 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 29 | 2 | `file_read:success:other` | `file_read#f0f8f4b51129` | `file_read#f0f8f4b51129` | True | True | True | success | agreement | recomputed_on_stored_state |
| 29 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 29 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 30 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 30 | 2 | `file_read:success:other` | `file_read#f0f8f4b51129` | `file_edit#cf3864667dd5` | False | None | None | unknown | disagreement_unverified_step | reconstructed_family_action |
| 30 | 3 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 30 | 4 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 31 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 31 | 5 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 31 | 6 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | `shell_exec#d1c77abc019a` | False | None | None | unknown | disagreement_unverified_step | reconstructed_family_action |
| 32 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 32 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 32 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 33 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 33 | 3 | `file_read:success:other` | `file_read#f0f8f4b51129` | `file_read#f0f8f4b51129` | True | True | True | success | agreement | recomputed_on_stored_state |
| 33 | 5 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#a4e317297fb3` | False | True | True | success | alternative_trajectory_verified | recomputed_on_stored_state |
| 33 | 6 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 34 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 34 | 5 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 34 | 6 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 35 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 35 | 3 | `file_read:success:other` | `file_read#f0f8f4b51129` | `file_edit#d8d674b62575` | False | None | None | unknown | disagreement_unverified_step | reconstructed_family_action |
| 35 | 4 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 35 | 5 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |
| 36 | 0 | `start:none:none` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | None | None | unknown | agreement | reconstructed_family_action |
| 36 | 5 | `file_edit:success:other` | `shell_exec#5fa23c7577e0` | `shell_exec#5fa23c7577e0` | True | True | True | success | agreement | recomputed_on_stored_state |
| 36 | 6 | `shell_exec:success:tests_passed` | `file_read#9bd55fe57a73` | finish (control call) | None | None | None | None | teacher_finished_mission | reconstructed_family_action |

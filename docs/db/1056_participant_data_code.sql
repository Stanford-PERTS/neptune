/* triton #1056 add code to participant data */

ALTER TABLE `participant_data`
  ADD `code` varchar(50) NOT NULL
  AFTER `project_cohort_id`;

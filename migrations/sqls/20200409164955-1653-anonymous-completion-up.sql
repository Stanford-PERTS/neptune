/* triton #1653 API gives participant ids and progress, benefits from index */

ALTER TABLE `participant_data`
  ADD INDEX `project_cohort-modified` (`project_cohort_id`, `modified`);

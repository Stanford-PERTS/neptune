/* neptune #1024 Remove "testing only" from participation counts */

ALTER TABLE `participant_data` ADD `testing` bool  NOT NULL DEFAULT 0;

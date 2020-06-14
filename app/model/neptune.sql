CREATE DATABASE IF NOT EXISTS `neptune`;

USE `neptune`;

GRANT ALL PRIVILEGES ON neptune.* TO 'neptune'@'localhost' IDENTIFIED BY 'neptune';

DROP TABLE IF EXISTS `checkpoint`;

CREATE TABLE `checkpoint` (
  `id` varchar(50) NOT NULL DEFAULT '',
  `parent_id` varchar(50) NOT NULL DEFAULT '',
  `name` text NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'incomplete',
  `survey_id` varchar(50) DEFAULT NULL,
  `cohort_label` varchar(100) DEFAULT NULL,
  `project_id` varchar(50) DEFAULT NULL,
  `program_id` varchar(50) DEFAULT NULL,
  `organization_id` varchar(50) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

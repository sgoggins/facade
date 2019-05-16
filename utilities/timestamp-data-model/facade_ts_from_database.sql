/*
 Navicat Premium Data Transfer

 Source Server         : mudcats-supersean
 Source Server Type    : MariaDB
 Source Server Version : 100129
 Source Host           : mudcats.augurlabs.io:3306
 Source Schema         : facade_ts

 Target Server Type    : MariaDB
 Target Server Version : 100129
 File Encoding         : 65001

 Date: 16/05/2019 13:50:31
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for affiliations
-- ----------------------------
DROP TABLE IF EXISTS `affiliations`;
CREATE TABLE `affiliations` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `domain` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `affiliation` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL DEFAULT '1970-01-01',
  `active` tinyint(1) NOT NULL DEFAULT '1',
  `last_modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `domain,affiliation,start_date` (`domain`,`affiliation`,`start_date`),
  KEY `domain,active` (`domain`,`active`)
) ENGINE=InnoDB AUTO_INCREMENT=522 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for aliases
-- ----------------------------
DROP TABLE IF EXISTS `aliases`;
CREATE TABLE `aliases` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `canonical` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `alias` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  `last_modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `canonical,alias` (`canonical`,`alias`),
  KEY `alias,active` (`alias`,`active`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for analysis_data
-- ----------------------------
DROP TABLE IF EXISTS `analysis_data`;
CREATE TABLE `analysis_data` (
  `repos_id` int(10) unsigned NOT NULL,
  `commit` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author_raw_email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author_email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author_date` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author_affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `committer_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `committer_raw_email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `committer_email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `committer_date` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `committer_affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `added` int(10) unsigned NOT NULL,
  `removed` int(10) unsigned NOT NULL,
  `whitespace` int(10) unsigned NOT NULL,
  `filename` varchar(4096) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_attempted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `author_email,author_affiliation,author_date` (`author_email`,`author_affiliation`,`author_date`),
  KEY `committer_email,committer_affiliation,committer_date` (`committer_email`,`committer_affiliation`,`committer_date`),
  KEY `repos_id,commit` (`repos_id`,`commit`),
  KEY `author_raw_email` (`author_raw_email`),
  KEY `committer_raw_email` (`committer_raw_email`),
  KEY `author_affiliation` (`author_affiliation`),
  KEY `committer_affiliation` (`committer_affiliation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for analysis_log
-- ----------------------------
DROP TABLE IF EXISTS `analysis_log`;
CREATE TABLE `analysis_log` (
  `repos_id` int(10) unsigned NOT NULL,
  `status` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_attempted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `repos_id` (`repos_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for auth
-- ----------------------------
DROP TABLE IF EXISTS `auth`;
CREATE TABLE `auth` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user` (`user`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for auth_history
-- ----------------------------
DROP TABLE IF EXISTS `auth_history`;
CREATE TABLE `auth_history` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(96) COLLATE utf8mb4_unicode_ci NOT NULL,
  `attempted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for exclude
-- ----------------------------
DROP TABLE IF EXISTS `exclude`;
CREATE TABLE `exclude` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `projects_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `domain` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for project_annual_cache
-- ----------------------------
DROP TABLE IF EXISTS `project_annual_cache`;
CREATE TABLE `project_annual_cache` (
  `projects_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `year` smallint(5) unsigned NOT NULL,
  `added` bigint(20) unsigned NOT NULL,
  `removed` bigint(20) unsigned NOT NULL,
  `whitespace` bigint(20) unsigned NOT NULL,
  `files` bigint(20) unsigned NOT NULL,
  `patches` bigint(20) unsigned NOT NULL,
  KEY `projects_id,affiliation` (`projects_id`,`affiliation`),
  KEY `projects_id,email` (`projects_id`,`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for project_monthly_cache
-- ----------------------------
DROP TABLE IF EXISTS `project_monthly_cache`;
CREATE TABLE `project_monthly_cache` (
  `projects_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `month` tinyint(3) unsigned NOT NULL,
  `year` smallint(5) unsigned NOT NULL,
  `added` bigint(20) unsigned NOT NULL,
  `removed` bigint(20) unsigned NOT NULL,
  `whitespace` bigint(20) unsigned NOT NULL,
  `files` bigint(20) unsigned NOT NULL,
  `patches` bigint(20) unsigned NOT NULL,
  KEY `projects_id,year,affiliation` (`projects_id`,`year`,`affiliation`),
  KEY `projects_id,year,email` (`projects_id`,`year`,`email`),
  KEY `projects_id,affiliation` (`projects_id`,`affiliation`),
  KEY `projects_id,email` (`projects_id`,`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for project_weekly_cache
-- ----------------------------
DROP TABLE IF EXISTS `project_weekly_cache`;
CREATE TABLE `project_weekly_cache` (
  `projects_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `week` tinyint(3) unsigned NOT NULL,
  `year` smallint(5) unsigned NOT NULL,
  `added` bigint(20) unsigned NOT NULL,
  `removed` bigint(20) unsigned NOT NULL,
  `whitespace` bigint(20) unsigned NOT NULL,
  `files` bigint(20) unsigned NOT NULL,
  `patches` bigint(20) unsigned NOT NULL,
  KEY `projects_id,year,affiliation` (`projects_id`,`year`,`affiliation`),
  KEY `projects_id,year,email` (`projects_id`,`year`,`email`),
  KEY `projects_id,affiliation` (`projects_id`,`affiliation`),
  KEY `projects_id,email` (`projects_id`,`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for projects
-- ----------------------------
DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  `website` varchar(128) DEFAULT NULL,
  `recache` tinyint(1) DEFAULT '1',
  `last_modified` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=294 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for repo_annual_cache
-- ----------------------------
DROP TABLE IF EXISTS `repo_annual_cache`;
CREATE TABLE `repo_annual_cache` (
  `repos_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `year` smallint(5) unsigned NOT NULL,
  `added` bigint(20) unsigned NOT NULL,
  `removed` bigint(20) unsigned NOT NULL,
  `whitespace` bigint(20) unsigned NOT NULL,
  `files` bigint(20) unsigned NOT NULL,
  `patches` bigint(20) unsigned NOT NULL,
  KEY `repos_id,affiliation` (`repos_id`,`affiliation`),
  KEY `repos_id,email` (`repos_id`,`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for repo_monthly_cache
-- ----------------------------
DROP TABLE IF EXISTS `repo_monthly_cache`;
CREATE TABLE `repo_monthly_cache` (
  `repos_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `month` tinyint(3) unsigned NOT NULL,
  `year` smallint(5) unsigned NOT NULL,
  `added` bigint(20) unsigned NOT NULL,
  `removed` bigint(20) unsigned NOT NULL,
  `whitespace` bigint(20) unsigned NOT NULL,
  `files` bigint(20) unsigned NOT NULL,
  `patches` bigint(20) unsigned NOT NULL,
  KEY `repos_id,year,affiliation` (`repos_id`,`year`,`affiliation`),
  KEY `repos_id,year,email` (`repos_id`,`year`,`email`),
  KEY `repos_id,affiliation` (`repos_id`,`affiliation`),
  KEY `repos_id,email` (`repos_id`,`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for repo_weekly_cache
-- ----------------------------
DROP TABLE IF EXISTS `repo_weekly_cache`;
CREATE TABLE `repo_weekly_cache` (
  `repos_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `affiliation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `week` tinyint(3) unsigned NOT NULL,
  `year` smallint(5) unsigned NOT NULL,
  `added` bigint(20) unsigned NOT NULL,
  `removed` bigint(20) unsigned NOT NULL,
  `whitespace` bigint(20) unsigned NOT NULL,
  `files` bigint(20) unsigned NOT NULL,
  `patches` bigint(20) unsigned NOT NULL,
  KEY `repos_id,year,affiliation` (`repos_id`,`year`,`affiliation`),
  KEY `repos_id,year,email` (`repos_id`,`year`,`email`),
  KEY `repos_id,affiliation` (`repos_id`,`affiliation`),
  KEY `repos_id,email` (`repos_id`,`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for repos
-- ----------------------------
DROP TABLE IF EXISTS `repos`;
CREATE TABLE `repos` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `projects_id` int(10) unsigned NOT NULL,
  `git` varchar(256) NOT NULL,
  `path` varchar(256) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `added` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `status` varchar(32) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=17048 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for repos_fetch_log
-- ----------------------------
DROP TABLE IF EXISTS `repos_fetch_log`;
CREATE TABLE `repos_fetch_log` (
  `repos_id` int(10) unsigned NOT NULL,
  `status` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `repos_id,status` (`repos_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for settings
-- ----------------------------
DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `setting` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_modified` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for special_tags
-- ----------------------------
DROP TABLE IF EXISTS `special_tags`;
CREATE TABLE `special_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `tag` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email,start_date,tag` (`email`,`start_date`,`tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for unknown_cache
-- ----------------------------
DROP TABLE IF EXISTS `unknown_cache`;
CREATE TABLE `unknown_cache` (
  `type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `projects_id` int(10) unsigned NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `domain` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL',
  `added` bigint(20) unsigned NOT NULL,
  KEY `type,projects_id` (`type`,`projects_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for utility_log
-- ----------------------------
DROP TABLE IF EXISTS `utility_log`;
CREATE TABLE `utility_log` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `level` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `attempted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for working_commits
-- ----------------------------
DROP TABLE IF EXISTS `working_commits`;
CREATE TABLE `working_commits` (
  `repos_id` int(10) unsigned NOT NULL,
  `working_commit` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT 'NULL'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

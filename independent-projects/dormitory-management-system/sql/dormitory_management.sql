-- 宿舍管理系统：MySQL 完整建库脚本（可直接执行）
-- 数据库：dormitory_management | 用户：root / 密码：root

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS `dormitory_management`;
CREATE DATABASE `dormitory_management`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE `dormitory_management`;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(64) NOT NULL,
  `password` VARCHAR(64) NOT NULL,
  `full_name` VARCHAR(64) NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `building_id` BIGINT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`),
  KEY `idx_users_building` (`building_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `building` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(128) NOT NULL,
  `address` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_building_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `floor` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `building_id` BIGINT NOT NULL,
  `name` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_floor_building` (`building_id`),
  CONSTRAINT `fk_floor_building`
    FOREIGN KEY (`building_id`) REFERENCES `building` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `dormitory` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `building_id` BIGINT NOT NULL,
  `floor_id` BIGINT NOT NULL,
  `dorm_code` VARCHAR(64) NOT NULL,
  `capacity` INT NOT NULL,
  `preference_tags` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_dorm_building` (`building_id`),
  KEY `idx_dorm_floor` (`floor_id`),
  CONSTRAINT `fk_dorm_building`
    FOREIGN KEY (`building_id`) REFERENCES `building` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_dorm_floor`
    FOREIGN KEY (`floor_id`) REFERENCES `floor` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `bed` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `dormitory_id` BIGINT NOT NULL,
  `bed_no` VARCHAR(64) NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `occupant_id` BIGINT DEFAULT NULL,
  `notes` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bed_dormitory_no` (`dormitory_id`,`bed_no`),
  UNIQUE KEY `uk_bed_occupant` (`occupant_id`),
  KEY `idx_bed_dormitory` (`dormitory_id`),
  KEY `idx_bed_occupant` (`occupant_id`),
  CONSTRAINT `fk_bed_dormitory`
    FOREIGN KEY (`dormitory_id`) REFERENCES `dormitory` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_bed_occupant`
    FOREIGN KEY (`occupant_id`) REFERENCES `users` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `move_in_application` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` BIGINT NOT NULL,
  `reason` VARCHAR(255) NOT NULL,
  `preferred_dormitory_id` BIGINT DEFAULT NULL,
  `preference_tags` VARCHAR(255) DEFAULT NULL,
  `status` VARCHAR(20) NOT NULL,
  `approved_by` BIGINT DEFAULT NULL,
  `assigned_bed_id` BIGINT DEFAULT NULL,
  `comment` VARCHAR(255) DEFAULT NULL,
  `apply_time` DATETIME NOT NULL,
  `process_time` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_movein_student` (`student_id`),
  KEY `idx_movein_pref_dorm` (`preferred_dormitory_id`),
  KEY `idx_movein_approver` (`approved_by`),
  KEY `idx_movein_bed` (`assigned_bed_id`),
  CONSTRAINT `fk_movein_student`
    FOREIGN KEY (`student_id`) REFERENCES `users` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_movein_pref_dorm`
    FOREIGN KEY (`preferred_dormitory_id`) REFERENCES `dormitory` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_movein_approver`
    FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_movein_bed`
    FOREIGN KEY (`assigned_bed_id`) REFERENCES `bed` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `move_out_application` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` BIGINT NOT NULL,
  `bed_id` BIGINT NOT NULL,
  `reason` VARCHAR(512) NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `approved_by` BIGINT DEFAULT NULL,
  `comment` VARCHAR(255) DEFAULT NULL,
  `apply_time` DATETIME NOT NULL,
  `process_time` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_moveout_student` (`student_id`),
  KEY `idx_moveout_bed` (`bed_id`),
  KEY `idx_moveout_approver` (`approved_by`),
  CONSTRAINT `fk_moveout_student`
    FOREIGN KEY (`student_id`) REFERENCES `users` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_moveout_bed`
    FOREIGN KEY (`bed_id`) REFERENCES `bed` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_moveout_approver`
    FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `repair` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` BIGINT NOT NULL,
  `location` VARCHAR(255) NOT NULL,
  `description` VARCHAR(512) NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `handler_id` BIGINT DEFAULT NULL,
  `comment` VARCHAR(255) DEFAULT NULL,
  `create_time` DATETIME NOT NULL,
  `handle_time` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_repair_student` (`student_id`),
  KEY `idx_repair_handler` (`handler_id`),
  CONSTRAINT `fk_repair_student`
    FOREIGN KEY (`student_id`) REFERENCES `users` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_repair_handler`
    FOREIGN KEY (`handler_id`) REFERENCES `users` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `bill` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` BIGINT NOT NULL,
  `bed_id` BIGINT DEFAULT NULL,
  `bill_month` VARCHAR(16) NOT NULL,
  `electricity` DECIMAL(10,2) NOT NULL,
  `water` DECIMAL(10,2) NOT NULL,
  `other_fee` DECIMAL(10,2) NOT NULL,
  `total` DECIMAL(10,2) NOT NULL,
  `record_date` DATE NOT NULL,
  `state` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_bill_student` (`student_id`),
  KEY `idx_bill_bed` (`bed_id`),
  CONSTRAINT `fk_bill_student`
    FOREIGN KEY (`student_id`) REFERENCES `users` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_bill_bed`
    FOREIGN KEY (`bed_id`) REFERENCES `bed` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `notice` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(128) NOT NULL,
  `content` VARCHAR(1024) NOT NULL,
  `scope` VARCHAR(20) NOT NULL,
  `building_id` BIGINT DEFAULT NULL,
  `author_id` BIGINT DEFAULT NULL,
  `create_time` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_notice_scope` (`scope`),
  KEY `idx_notice_building` (`building_id`),
  KEY `idx_notice_author` (`author_id`),
  CONSTRAINT `fk_notice_building`
    FOREIGN KEY (`building_id`) REFERENCES `building` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_notice_author`
    FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `users`
  ADD CONSTRAINT `fk_users_building`
  FOREIGN KEY (`building_id`) REFERENCES `building` (`id`)
  ON DELETE SET NULL ON UPDATE CASCADE;

-- 固定外键关系后，补充基础示例数据（对齐初始化逻辑）
INSERT INTO `building` (`id`,`name`,`address`) VALUES
  (1, '1号宿舍楼', '理工楼A区'),
  (2, '2号宿舍楼', '理工楼B区');

INSERT INTO `floor` (`id`,`building_id`,`name`) VALUES
  (1, 1, '1层'),
  (2, 1, '2层'),
  (3, 2, '1层');

INSERT INTO `dormitory` (`id`,`building_id`,`floor_id`,`dorm_code`,`capacity`,`preference_tags`) VALUES
  (1, 1, 1, '1-101', 8, '安静,早睡,整洁,阅读'),
  (2, 1, 1, '1-102', 6, '活跃,正常,一般,运动'),
  (3, 2, 3, '2-201', 10, '安静,晚睡,整洁,游戏');

INSERT INTO `bed` (`id`,`dormitory_id`,`bed_no`,`status`,`occupant_id`,`notes`) VALUES
  (1, 1, '1号床', 'VACANT', NULL, '自动生成'), (2, 1, '2号床', 'VACANT', NULL, '自动生成'),
  (3, 1, '3号床', 'VACANT', NULL, '自动生成'), (4, 1, '4号床', 'VACANT', NULL, '自动生成'),
  (5, 1, '5号床', 'VACANT', NULL, '自动生成'), (6, 1, '6号床', 'VACANT', NULL, '自动生成'),
  (7, 1, '7号床', 'VACANT', NULL, '自动生成'), (8, 1, '8号床', 'VACANT', NULL, '自动生成'),
  (9, 2, '1号床', 'VACANT', NULL, '自动生成'), (10, 2, '2号床', 'VACANT', NULL, '自动生成'),
  (11, 2, '3号床', 'VACANT', NULL, '自动生成'), (12, 2, '4号床', 'VACANT', NULL, '自动生成'),
  (13, 2, '5号床', 'VACANT', NULL, '自动生成'), (14, 2, '6号床', 'VACANT', NULL, '自动生成'),
  (15, 3, '1号床', 'VACANT', NULL, '自动生成'), (16, 3, '2号床', 'VACANT', NULL, '自动生成'),
  (17, 3, '3号床', 'VACANT', NULL, '自动生成'), (18, 3, '4号床', 'VACANT', NULL, '自动生成'),
  (19, 3, '5号床', 'VACANT', NULL, '自动生成'), (20, 3, '6号床', 'VACANT', NULL, '自动生成'),
  (21, 3, '7号床', 'VACANT', NULL, '自动生成'), (22, 3, '8号床', 'VACANT', NULL, '自动生成'),
  (23, 3, '9号床', 'VACANT', NULL, '自动生成'), (24, 3, '10号床', 'VACANT', NULL, '自动生成');

INSERT INTO `users` (`id`,`username`,`password`,`full_name`,`role`,`building_id`) VALUES
  (1, 'admin', '$2a$10$weWCs3b87.0anSeWdla9Uehv9v1.1pirHWTM/uwTmBJ4N/g094MjK', '系统管理员', 'ADMIN', NULL),
  (2, 'manager', '$2a$10$weWCs3b87.0anSeWdla9Uehv9v1.1pirHWTM/uwTmBJ4N/g094MjK', '宿舍管理员', 'DORM_MANAGER', 1),
  (3, 'student', '$2a$10$weWCs3b87.0anSeWdla9Uehv9v1.1pirHWTM/uwTmBJ4N/g094MjK', '测试学生', 'STUDENT', NULL);

INSERT INTO `notice` (`id`,`title`,`content`,`scope`,`building_id`,`author_id`,`create_time`) VALUES
  (1, '欢迎使用宿舍管理系统', '示例系统已启动，可直接登录：admin、manager 或 student，密码都是 123456。', 'ALL', NULL, 1, NOW());

ALTER TABLE `bill` AUTO_INCREMENT = 1;
ALTER TABLE `building` AUTO_INCREMENT = 3;
ALTER TABLE `dormitory` AUTO_INCREMENT = 4;
ALTER TABLE `floor` AUTO_INCREMENT = 4;
ALTER TABLE `move_in_application` AUTO_INCREMENT = 1;
ALTER TABLE `move_out_application` AUTO_INCREMENT = 1;
ALTER TABLE `repair` AUTO_INCREMENT = 1;
ALTER TABLE `users` AUTO_INCREMENT = 4;
ALTER TABLE `notice` AUTO_INCREMENT = 2;

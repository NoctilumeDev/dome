-- =====================================================
-- 图书借阅管理系统 MySQL 8 一键初始化脚本
-- 可在命令行、MySQL 客户端或 Navicat 中直接完整执行
-- =====================================================

CREATE DATABASE IF NOT EXISTS `library_management`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE `library_management`;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
-- 删除旧表（按外键依赖顺序）
DROP TABLE IF EXISTS book_review;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS borrow_record;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS bookshelf;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS user;

-- 用户表
CREATE TABLE user (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_account VARCHAR(32)  NOT NULL UNIQUE COMMENT '账号',
    user_name    VARCHAR(32)  NOT NULL COMMENT '用户名',
    user_pwd     VARCHAR(64)  NOT NULL COMMENT '密码',
    user_avatar  VARCHAR(255)          COMMENT '头像路径',
    user_role    TINYINT      NOT NULL DEFAULT 2 COMMENT '角色: 1=管理员, 2=读者',
    is_login     TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '0=正常, 1=冻结',
    create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 分类表
CREATE TABLE category (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(32) NOT NULL COMMENT '分类名称',
    create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分类表';

-- 书架表
CREATE TABLE bookshelf (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(64)  NOT NULL COMMENT '书架名称',
    location    VARCHAR(128)          COMMENT '位置',
    capacity    INT          NOT NULL DEFAULT 100 COMMENT '容量',
    description VARCHAR(255)          COMMENT '备注',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='书架表';

-- 图书表
CREATE TABLE book (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(128) NOT NULL COMMENT '书名',
    author          VARCHAR(64)  NOT NULL COMMENT '作者',
    isbn            VARCHAR(20)           COMMENT 'ISBN号',
    publisher       VARCHAR(64)           COMMENT '出版社',
    category        VARCHAR(32)           COMMENT '分类',
    bookshelf_id    INT                   COMMENT '所属书架ID',
    total_count     INT          NOT NULL DEFAULT 1 COMMENT '总数量',
    available_count INT          NOT NULL DEFAULT 1 COMMENT '可借数量',
    cover           VARCHAR(255)          COMMENT '封面路径',
    description     TEXT                  COMMENT '简介',
    create_time     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    INDEX idx_bookshelf_id (bookshelf_id),
    CONSTRAINT fk_book_bookshelf FOREIGN KEY (bookshelf_id) REFERENCES bookshelf(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书表';

-- 借阅记录表
CREATE TABLE borrow_record (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT           NOT NULL COMMENT '用户ID',
    book_id     INT           NOT NULL COMMENT '图书ID',
    borrow_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '借阅时间',
    due_date    DATETIME      NOT NULL COMMENT '应还日期',
    return_time DATETIME               COMMENT '归还时间',
    status      TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '0=借阅中, 1=已归还',
    fine_amount DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '逾期罚款金额(元)',
    INDEX idx_user_id (user_id),
    INDEX idx_book_id (book_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='借阅记录表';

-- 读者反馈表
CREATE TABLE feedback (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL COMMENT '读者ID',
    content     VARCHAR(500) NOT NULL COMMENT '反馈内容',
    reply       VARCHAR(500)          COMMENT '管理员回复',
    status      TINYINT      NOT NULL DEFAULT 0 COMMENT '0=待处理, 1=已回复',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    reply_time  DATETIME              COMMENT '回复时间',
    INDEX idx_feedback_user (user_id),
    INDEX idx_feedback_status (status),
    CONSTRAINT fk_feedback_user FOREIGN KEY (user_id) REFERENCES user(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='读者反馈表';

-- 图书评论表
CREATE TABLE book_review (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL COMMENT '读者ID',
    book_id     INT          NOT NULL COMMENT '图书ID',
    rating      TINYINT      NOT NULL COMMENT '评分1-5',
    content     VARCHAR(500) NOT NULL COMMENT '书评内容',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_review_user_book (user_id, book_id),
    INDEX idx_review_book (book_id),
    CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES user(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_review_book FOREIGN KEY (book_id) REFERENCES book(id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书评论表';

-- =====================================================
-- 测试数据（密码均为: 123456，BCrypt 加密存储）
-- =====================================================

-- 管理员
INSERT INTO user (user_account, user_name, user_pwd, user_role, is_login, create_time) VALUES
('admin',    '管理员', '$2a$10$sUGWmtJuqOm5gojVAh91BuCbH3aoTgp9SzBMYkpOXBzh7Ud73ollS', 1, 0, NOW());

-- 读者
INSERT INTO user (user_account, user_name, user_pwd, user_role, is_login, create_time) VALUES
('zhangsan', '张三',   '$2a$10$sUGWmtJuqOm5gojVAh91BuCbH3aoTgp9SzBMYkpOXBzh7Ud73ollS', 2, 0, NOW()),
('lisi',     '李四',   '$2a$10$sUGWmtJuqOm5gojVAh91BuCbH3aoTgp9SzBMYkpOXBzh7Ud73ollS', 2, 0, NOW());

-- 分类
INSERT INTO category (name, create_time) VALUES
('编程', NOW()), ('文学', NOW()), ('历史', NOW()), ('科学', NOW());

-- 书架
INSERT INTO bookshelf (name, location, capacity, description, create_time) VALUES
('A区-1号架', '图书馆一楼东侧', 200, '计算机类图书', NOW()),
('B区-3号架', '图书馆二楼西侧', 150, '文学类图书',   NOW()),
('C区-2号架', '图书馆三楼北侧', 180, '综合类图书',   NOW());

-- 图书
INSERT INTO book (name, author, isbn, publisher, category, bookshelf_id, total_count, available_count, description, create_time) VALUES
('Java编程思想',    'Bruce Eckel', '9787111213826', '机械工业出版社',     '编程', 1, 5, 5, 'Java经典入门书籍',        NOW()),
('Spring Boot实战', 'Craig Walls', '9787115417305', '人民邮电出版社',     '编程', 1, 3, 3, 'Spring Boot入门到精通',    NOW()),
('活着',            '余华',        '9787530215319', '北京十月文艺出版社', '文学', 2, 4, 4, '余华代表作',               NOW()),
('三体',            '刘慈欣',      '9787536692930', '重庆出版社',         '科学', 3, 6, 6, '科幻巨作',                 NOW()),
('万历十五年',      '黄仁宇',      '9787108009821', '三联书店',           '历史', 3, 2, 2, '明史研究经典',             NOW());


SET FOREIGN_KEY_CHECKS = 1;

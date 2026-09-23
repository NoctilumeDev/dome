-- 先给这几周的报修找一个地方
CREATE DATABASE after_class DEFAULT CHARACTER SET utf8mb4;

USE after_class;

-- 里面先放一张空表
CREATE TABLE repair (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    room VARCHAR(20),
    content VARCHAR(200)
);

-- 加两条报修
INSERT INTO repair (room, content)
VALUES ('3-412', '水龙头漏水');

INSERT INTO repair (room, content)
VALUES ('5-203', '门锁坏了');

-- 看看刚才加进去的东西
SELECT * FROM repair;

-- 第一条报修说得再清楚一点
UPDATE repair
SET content = '水龙头一直滴水'
WHERE id = 1;

SELECT * FROM repair;

-- 第二条报修不要了
DELETE FROM repair
WHERE id = 2;

SELECT * FROM repair;

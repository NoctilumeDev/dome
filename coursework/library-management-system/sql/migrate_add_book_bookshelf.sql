USE `library_management`;
SET NAMES utf8mb4;

SET @schema_name = DATABASE();

SELECT COUNT(*) INTO @column_exists
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = @schema_name
  AND TABLE_NAME = 'book'
  AND COLUMN_NAME = 'bookshelf_id';

SET @ddl = IF(
    @column_exists = 0,
    'ALTER TABLE `book` ADD COLUMN `bookshelf_id` INT NULL COMMENT ''所属书架ID'' AFTER `category`',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE `book`
SET `bookshelf_id` = (
    SELECT `id` FROM `bookshelf` WHERE `name` = 'A区-1号架' LIMIT 1
)
WHERE `bookshelf_id` IS NULL
  AND (`category` LIKE '%编程%' OR `name` LIKE '%Java%' OR `name` LIKE '%Spring%');

UPDATE `book`
SET `bookshelf_id` = (
    SELECT `id` FROM `bookshelf` WHERE `name` = 'C区-2号架' LIMIT 1
)
WHERE `bookshelf_id` IS NULL
  AND (`category` LIKE '%科学%' OR `category` LIKE '%历史%');

UPDATE `book`
SET `bookshelf_id` = (
    SELECT `id` FROM `bookshelf` WHERE `name` = 'B区-3号架' LIMIT 1
)
WHERE `bookshelf_id` IS NULL;

SELECT COUNT(*) INTO @index_exists
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = @schema_name
  AND TABLE_NAME = 'book'
  AND INDEX_NAME = 'idx_bookshelf_id';

SET @ddl = IF(
    @index_exists = 0,
    'ALTER TABLE `book` ADD INDEX `idx_bookshelf_id` (`bookshelf_id`)',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @fk_exists
FROM information_schema.REFERENTIAL_CONSTRAINTS
WHERE BINARY CONSTRAINT_SCHEMA = BINARY @schema_name
  AND TABLE_NAME = 'book'
  AND CONSTRAINT_NAME = 'fk_book_bookshelf';

SET @ddl = IF(
    @fk_exists = 0,
    'ALTER TABLE `book` ADD CONSTRAINT `fk_book_bookshelf` FOREIGN KEY (`bookshelf_id`) REFERENCES `bookshelf` (`id`) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

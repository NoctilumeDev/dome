package cn.kmbeast.service.assistant;

import org.springframework.stereotype.Repository;

import javax.annotation.Resource;
import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 将查询计划编译为固定字段、参数化、只读 SQL。
 */
@Repository
public class BookQueryRepository {
    private static final int MAX_ROWS = 50;
    private static final String SELECT_COLUMNS =
            "SELECT b.id,b.name,b.author,b.isbn,b.publisher,b.category,"
                    + "b.total_count AS totalCount,b.available_count AS availableCount,"
                    + "b.cover,b.description,b.create_time AS createTime,"
                    + "b.bookshelf_id AS bookshelfId,s.name AS bookshelfName,s.location "
                    + "FROM book b LEFT JOIN bookshelf s ON s.id=b.bookshelf_id";

    @Resource
    private DataSource dataSource;

    public QueryResult query(BookQueryPlan plan, Integer currentUserId, boolean isAdmin) {
        if (!plan.isBookIntent()) {
            return queryBusinessData(plan, currentUserId, isAdmin);
        }
        List<String> conditions = new ArrayList<>();
        List<Object> parameters = new ArrayList<>();

        addLikeCondition(conditions, parameters, "b.name", plan.getTitle());
        addLikeCondition(conditions, parameters, "b.author", plan.getAuthor());
        addLikeCondition(conditions, parameters, "b.category", plan.getCategory());
        addLikeCondition(conditions, parameters, "b.publisher", plan.getPublisher());

        if (plan.getKeywords() != null) {
            List<String> keywordConditions = new ArrayList<>();
            for (String keyword : plan.getKeywords()) {
                if (keyword == null || keyword.isBlank()) {
                    continue;
                }
                keywordConditions.add("(b.name LIKE ? OR b.author LIKE ? OR b.isbn LIKE ? OR "
                        + "b.publisher LIKE ? OR b.category LIKE ? OR b.description LIKE ?)");
                for (int index = 0; index < 6; index++) {
                    parameters.add("%" + keyword.trim() + "%");
                }
            }
            if (!keywordConditions.isEmpty()) {
                conditions.add("(" + String.join(" OR ", keywordConditions) + ")");
            }
        }

        if (Boolean.TRUE.equals(plan.getAvailableOnly())) {
            conditions.add("b.available_count > 0");
        } else if (Boolean.FALSE.equals(plan.getAvailableOnly())) {
            conditions.add("b.available_count <= 0");
        }

        int limit = Math.max(1, Math.min(plan.getLimit() == null ? 20 : plan.getLimit(), MAX_ROWS));
        String where = conditions.isEmpty() ? "1=1" : String.join(" AND ", conditions);
        String orderBy = plan.getIntent() == BookIntent.RECOMMEND_BOOK
                ? "b.available_count DESC,b.id DESC" : "b.id DESC";
        String sql = SELECT_COLUMNS + " WHERE " + where + " ORDER BY " + orderBy + " LIMIT " + limit;

        List<Map<String, Object>> rows = execute(sql, parameters);
        return new QueryResult(rows, sql + System.lineSeparator() + "-- 参数: " + parameters);
    }

    private QueryResult queryBusinessData(BookQueryPlan plan, Integer currentUserId, boolean isAdmin) {
        if (plan.requiresAdmin() && !isAdmin) {
            throw new IllegalStateException("当前账号无权查询其他读者的数据");
        }
        int limit = Math.max(1, Math.min(plan.getLimit() == null ? 20 : plan.getLimit(), MAX_ROWS));
        List<Object> parameters = new ArrayList<>();
        String sql;

        if (plan.getIntent() == BookIntent.LIST_USERS) {
            sql = "SELECT id,user_account AS userAccount,user_name AS userName,user_role AS userRole,"
                    + "is_login AS isLogin,create_time AS createTime FROM user ORDER BY id DESC LIMIT " + limit;
        } else if (plan.getIntent() == BookIntent.SEARCH_REVIEWS || plan.getIntent() == BookIntent.MY_REVIEWS) {
            StringBuilder where = new StringBuilder(" WHERE 1=1");
            if (plan.getIntent() == BookIntent.MY_REVIEWS) {
                where.append(" AND r.user_id=?");
                parameters.add(currentUserId);
            }
            if (plan.getTitle() != null && !plan.getTitle().isBlank()) {
                where.append(" AND b.name LIKE ?");
                parameters.add("%" + plan.getTitle().trim() + "%");
            }
            sql = "SELECT r.id,r.user_id AS userId,u.user_name AS userName,r.book_id AS bookId,"
                    + "b.name AS bookName,r.rating,r.content,r.create_time AS createTime,r.update_time AS updateTime "
                    + "FROM book_review r LEFT JOIN user u ON u.id=r.user_id LEFT JOIN book b ON b.id=r.book_id"
                    + where + " ORDER BY r.id DESC LIMIT " + limit;
        } else if (plan.getIntent() == BookIntent.FEEDBACK_OVERVIEW || plan.getIntent() == BookIntent.MY_FEEDBACK) {
            String where = plan.getIntent() == BookIntent.MY_FEEDBACK ? " WHERE f.user_id=?" : " WHERE 1=1";
            if (plan.getIntent() == BookIntent.MY_FEEDBACK) {
                parameters.add(currentUserId);
            }
            sql = "SELECT f.id,f.user_id AS userId,u.user_name AS userName,f.content,f.reply,f.status,"
                    + "f.create_time AS createTime,f.reply_time AS replyTime FROM feedback f "
                    + "LEFT JOIN user u ON u.id=f.user_id" + where + " ORDER BY f.id DESC LIMIT " + limit;
        } else {
            StringBuilder where = new StringBuilder(" WHERE 1=1");
            if (plan.getIntent() == BookIntent.MY_BORROWS || plan.getIntent() == BookIntent.MY_DUE_SOON) {
                where.append(" AND br.user_id=?");
                parameters.add(currentUserId);
            } else if (plan.getUserName() != null && !plan.getUserName().isBlank()) {
                where.append(" AND u.user_name LIKE ?");
                parameters.add("%" + plan.getUserName().trim() + "%");
            }
            if (plan.getIntent() == BookIntent.RECENT_RETURNS) {
                where.append(" AND br.status=1 AND br.return_time IS NOT NULL");
            } else if (plan.getIntent() == BookIntent.DUE_SOON || plan.getIntent() == BookIntent.MY_DUE_SOON) {
                where.append(" AND br.status=0 AND br.due_date>=NOW() AND br.due_date<=?");
                parameters.add(LocalDateTime.now().plusDays(plan.getDays() == null ? 3 : plan.getDays()));
            } else if (plan.getIntent() == BookIntent.OVERDUE_BORROWS) {
                where.append(" AND br.status=0 AND br.due_date<NOW()");
            }
            String orderBy = plan.getIntent() == BookIntent.RECENT_RETURNS ? "br.return_time DESC" : "br.due_date ASC";
            sql = "SELECT br.id,br.user_id AS userId,u.user_name AS userName,br.book_id AS bookId,"
                    + "b.name AS bookName,br.borrow_time AS borrowTime,br.due_date AS dueDate,"
                    + "br.return_time AS returnTime,br.status,br.fine_amount AS fineAmount "
                    + "FROM borrow_record br LEFT JOIN user u ON u.id=br.user_id LEFT JOIN book b ON b.id=br.book_id"
                    + where + " ORDER BY " + orderBy + " LIMIT " + limit;
        }
        return new QueryResult(execute(sql, parameters), sql + System.lineSeparator() + "-- 参数: " + parameters);
    }

    private void addLikeCondition(List<String> conditions, List<Object> parameters,
                                  String column, String value) {
        if (value != null && !value.isBlank()) {
            conditions.add(column + " LIKE ?");
            parameters.add("%" + value.trim() + "%");
        }
    }

    private List<Map<String, Object>> execute(String sql, List<Object> parameters) {
        List<Map<String, Object>> rows = new ArrayList<>();
        try (Connection connection = dataSource.getConnection()) {
            connection.setReadOnly(true);
            try (PreparedStatement statement = connection.prepareStatement(sql)) {
                statement.setQueryTimeout(5);
                statement.setMaxRows(MAX_ROWS);
                for (int index = 0; index < parameters.size(); index++) {
                    statement.setObject(index + 1, parameters.get(index));
                }
                try (ResultSet resultSet = statement.executeQuery()) {
                    ResultSetMetaData metaData = resultSet.getMetaData();
                    int columnCount = metaData.getColumnCount();
                    while (resultSet.next()) {
                        Map<String, Object> row = new LinkedHashMap<>();
                        for (int index = 1; index <= columnCount; index++) {
                            row.put(toCamelCase(metaData.getColumnLabel(index)), resultSet.getObject(index));
                        }
                        rows.add(row);
                    }
                }
            }
        } catch (Exception exception) {
            throw new IllegalStateException("图书数据库查询失败", exception);
        }
        return rows;
    }

    private String toCamelCase(String value) {
        String column = value == null ? "" : value.trim();
        if (!column.contains("_")) {
            return column;
        }
        StringBuilder result = new StringBuilder();
        boolean upperNext = false;
        for (char current : column.toCharArray()) {
            if (current == '_') {
                upperNext = true;
            } else if (upperNext) {
                result.append(Character.toUpperCase(current));
                upperNext = false;
            } else {
                result.append(Character.toLowerCase(current));
            }
        }
        return result.toString();
    }

    public static class QueryResult {
        private final List<Map<String, Object>> rows;
        private final String displaySql;

        public QueryResult(List<Map<String, Object>> rows, String displaySql) {
            this.rows = rows;
            this.displaySql = displaySql;
        }

        public List<Map<String, Object>> getRows() {
            return rows;
        }

        public String getDisplaySql() {
            return displaySql;
        }
    }
}

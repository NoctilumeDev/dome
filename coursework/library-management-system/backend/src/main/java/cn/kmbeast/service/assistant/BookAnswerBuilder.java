package cn.kmbeast.service.assistant;

import org.springframework.stereotype.Component;

import java.util.List;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * 只使用数据库结果确定性地生成自然语言答案。
 */
@Component
public class BookAnswerBuilder {

    public String build(String question, BookQueryPlan plan, List<Map<String, Object>> rows) {
        int total = rows == null ? 0 : rows.size();
        if (total == 0) {
            return emptyAnswer(plan);
        }
        if (plan.getIntent() == BookIntent.LIST_CATALOG) {
            return summarizeCatalog(rows);
        }
        if (plan.getIntent() == BookIntent.LIST_USERS) {
            return summarizeUsers(rows);
        }
        if (plan.getIntent() == BookIntent.BORROW_OVERVIEW || plan.getIntent() == BookIntent.MY_BORROWS) {
            return summarizeBorrows(rows, plan.getIntent() == BookIntent.MY_BORROWS ? "你的借阅记录" : "借阅记录");
        }
        if (plan.getIntent() == BookIntent.RECENT_RETURNS) {
            return summarizeReturns(rows);
        }
        if (plan.getIntent() == BookIntent.DUE_SOON || plan.getIntent() == BookIntent.MY_DUE_SOON) {
            return summarizeDueSoon(rows, plan.getDays() == null ? 3 : plan.getDays());
        }
        if (plan.getIntent() == BookIntent.OVERDUE_BORROWS) {
            return summarizeBorrows(rows, "逾期未还记录");
        }
        if (plan.getIntent() == BookIntent.SEARCH_REVIEWS || plan.getIntent() == BookIntent.MY_REVIEWS) {
            return summarizeReviews(rows);
        }
        if (plan.getIntent() == BookIntent.FEEDBACK_OVERVIEW || plan.getIntent() == BookIntent.MY_FEEDBACK) {
            return summarizeFeedback(rows);
        }
        if (plan.getIntent() == BookIntent.FIND_LOCATION) {
            return summarizeLocations(rows);
        }
        if (plan.getIntent() == BookIntent.CHECK_AVAILABILITY) {
            long available = rows.stream().filter(this::isAvailable).count();
            int availableCopies = rows.stream().mapToInt(row -> number(row.get("availableCount"))).sum();
            return "本馆共查到 " + total + " 种相关图书，其中 " + available
                    + " 种当前可借，合计可借 " + availableCopies + " 册。"
                    + System.lineSeparator() + summarize(rows);
        }
        if (isExistenceQuestion(question) || hasText(plan.getTitle())) {
            return "有，本馆查到了 " + total + " 条匹配记录。"
                    + System.lineSeparator() + summarize(rows);
        }
        if (plan.getIntent() == BookIntent.RECOMMEND_BOOK) {
            return "我只根据本馆实际馆藏进行推荐，共找到 " + total + " 种符合条件的图书："
                    + System.lineSeparator() + summarize(rows);
        }
        return "本馆数据库中共找到 " + total + " 种相关图书："
                + System.lineSeparator() + summarize(rows);
    }

    private String emptyAnswer(BookQueryPlan plan) {
        if (plan.getIntent() == BookIntent.LIST_CATALOG) {
            return "本馆数据库中暂未登记图书或书架信息。";
        }
        if (!plan.isBookIntent()) {
            return "数据库中暂未检索到符合当前条件的记录。";
        }
        String subject = plan.primarySubject();
        if (plan.getIntent() == BookIntent.RECOMMEND_BOOK) {
            return "本馆暂未检索到与“" + subject + "”匹配的馆藏，因此无法基于数据库给出推荐。";
        }
        if (plan.getIntent() == BookIntent.FIND_LOCATION) {
            return "本馆暂未检索到与“" + subject + "”匹配的图书，也无法提供位置信息。";
        }
        return "本馆数据库中暂未检索到与“" + subject + "”匹配的图书。";
    }

    private String summarize(List<Map<String, Object>> rows) {
        StringBuilder answer = new StringBuilder();
        int showCount = Math.min(rows.size(), 5);
        for (int index = 0; index < showCount; index++) {
            if (index > 0) {
                answer.append(System.lineSeparator());
            }
            answer.append("• ").append(formatBook(rows.get(index)));
        }
        if (rows.size() > showCount) {
            answer.append(System.lineSeparator())
                    .append("• 另有 ").append(rows.size() - showCount).append(" 本，请查看下方表格。");
        }
        return answer.toString();
    }

    private String formatBook(Map<String, Object> row) {
        StringBuilder result = new StringBuilder(text(row.get("name"), "未知书名"));
        result.append("，作者：").append(text(row.get("author"), "未记录"));
        result.append("，分类：").append(text(row.get("category"), "未分类"));
        result.append("，出版社：").append(text(row.get("publisher"), "未记录"));
        result.append("，当前可借：").append(number(row.get("availableCount"))).append(" 册");
        String bookshelfName = text(row.get("bookshelfName"), "");
        String location = text(row.get("location"), "");
        if (!bookshelfName.isBlank() || !location.isBlank()) {
            result.append("，位置：");
            if (!bookshelfName.isBlank()) {
                result.append(bookshelfName);
            }
            if (!location.isBlank()) {
                if (!bookshelfName.isBlank()) {
                    result.append("（");
                }
                result.append(location);
                if (!bookshelfName.isBlank()) {
                    result.append("）");
                }
            }
        }
        return result.toString();
    }

    private String summarizeLocations(List<Map<String, Object>> rows) {
        StringBuilder answer = new StringBuilder("已查到以下馆藏位置：");
        int count = 0;
        for (Map<String, Object> row : rows) {
            String bookshelfName = text(row.get("bookshelfName"), "");
            String location = text(row.get("location"), "");
            if (bookshelfName.isBlank() && location.isBlank()) {
                continue;
            }
            if (count > 0) {
                answer.append("；");
            }
            answer.append("《").append(text(row.get("name"), "未知书名")).append("》：");
            if (!bookshelfName.isBlank()) {
                answer.append(bookshelfName);
            }
            if (!location.isBlank()) {
                if (!bookshelfName.isBlank()) {
                    answer.append("，");
                }
                answer.append(location);
            }
            count++;
            if (count == 5) {
                break;
            }
        }
        if (count == 0) {
            return "已在本馆数据库中找到相关图书，但尚未登记具体书架位置。";
        }
        return answer.append("。").toString();
    }

    private String summarizeCatalog(List<Map<String, Object>> rows) {
        Set<String> shelves = new LinkedHashSet<>();
        for (Map<String, Object> row : rows) {
            String name = text(row.get("bookshelfName"), "");
            String location = text(row.get("location"), "");
            if (!name.isBlank()) {
                shelves.add(location.isBlank() ? name : name + "（" + location + "）");
            }
        }
        String shelfText = shelves.isEmpty() ? "暂未登记书架" : String.join("、", shelves);
        return "本馆数据库中共登记 " + rows.size() + " 种图书，涉及 " + shelves.size()
                + " 个书架：" + shelfText + "。"
                + System.lineSeparator() + summarize(rows);
    }

    private String summarizeUsers(List<Map<String, Object>> rows) {
        StringBuilder answer = new StringBuilder("系统中共查到 ").append(rows.size()).append(" 个用户：");
        for (Map<String, Object> row : visibleRows(rows)) {
            answer.append(System.lineSeparator()).append("• ").append(text(row.get("userName"), "未命名用户"))
                    .append("（账号：").append(text(row.get("userAccount"), "未记录")).append("，角色：")
                    .append(number(row.get("userRole")) == 1 ? "管理员" : "读者").append("）");
        }
        return answer.toString();
    }

    private String summarizeBorrows(List<Map<String, Object>> rows, String title) {
        StringBuilder answer = new StringBuilder(title).append("共 ").append(rows.size()).append(" 条：");
        for (Map<String, Object> row : visibleRows(rows)) {
            boolean returned = booleanValue(row.get("status"));
            answer.append(System.lineSeparator()).append("• ").append(text(row.get("userName"), "当前读者"))
                    .append("借阅《").append(text(row.get("bookName"), "未知图书")).append("》，应还时间：")
                    .append(text(row.get("dueDate"), "未记录")).append("，状态：")
                    .append(returned ? "已归还" : "借阅中");
        }
        return answer.toString();
    }

    private String summarizeReturns(List<Map<String, Object>> rows) {
        StringBuilder answer = new StringBuilder("最近共有 ").append(rows.size()).append(" 条归还记录：");
        for (Map<String, Object> row : visibleRows(rows)) {
            answer.append(System.lineSeparator()).append("• ").append(text(row.get("userName"), "未知读者"))
                    .append("归还了《").append(text(row.get("bookName"), "未知图书")).append("》，归还时间：")
                    .append(text(row.get("returnTime"), "未记录"));
        }
        return answer.toString();
    }

    private String summarizeDueSoon(List<Map<String, Object>> rows, int days) {
        StringBuilder answer = new StringBuilder("未来 ").append(days).append(" 天内共有 ").append(rows.size()).append(" 条借阅即将到期：");
        for (Map<String, Object> row : visibleRows(rows)) {
            answer.append(System.lineSeparator()).append("• 请提醒 ").append(text(row.get("userName"), "当前读者"))
                    .append("归还《").append(text(row.get("bookName"), "未知图书")).append("》，应还时间：")
                    .append(text(row.get("dueDate"), "未记录"));
        }
        return answer.toString();
    }

    private String summarizeReviews(List<Map<String, Object>> rows) {
        StringBuilder answer = new StringBuilder("数据库中共查到 ").append(rows.size()).append(" 条书评：");
        for (Map<String, Object> row : visibleRows(rows)) {
            answer.append(System.lineSeparator()).append("• 《").append(text(row.get("bookName"), "未知图书")).append("》")
                    .append("，评分：").append(number(row.get("rating"))).append("/5，")
                    .append(text(row.get("userName"), "匿名读者")).append("：")
                    .append(text(row.get("content"), "未填写内容"));
        }
        return answer.toString();
    }

    private String summarizeFeedback(List<Map<String, Object>> rows) {
        StringBuilder answer = new StringBuilder("数据库中共查到 ").append(rows.size()).append(" 条反馈：");
        for (Map<String, Object> row : visibleRows(rows)) {
            answer.append(System.lineSeparator()).append("• ").append(text(row.get("userName"), "当前读者")).append("：")
                    .append(text(row.get("content"), "未填写内容")).append("；处理状态：")
                    .append(number(row.get("status")) == 1 ? "已回复" : "待处理");
            if (row.get("reply") != null) {
                answer.append("；回复：").append(text(row.get("reply"), ""));
            }
        }
        return answer.toString();
    }

    private List<Map<String, Object>> visibleRows(List<Map<String, Object>> rows) {
        return rows.subList(0, Math.min(rows.size(), 8));
    }

    private boolean booleanValue(Object value) {
        return Boolean.TRUE.equals(value) || number(value) == 1;
    }

    private boolean isExistenceQuestion(String question) {
        String normalized = question == null ? "" : question.toLowerCase(Locale.ROOT);
        return normalized.contains("有没有") || normalized.contains("是否有")
                || normalized.contains("有无") || normalized.matches(".*有.+吗[?？]?$");
    }

    private boolean isAvailable(Map<String, Object> row) {
        return number(row.get("availableCount")) > 0;
    }

    private int number(Object value) {
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        try {
            return value == null ? 0 : Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException ignored) {
            return 0;
        }
    }

    private String text(Object value, String fallback) {
        return value == null || String.valueOf(value).isBlank() ? fallback : String.valueOf(value);
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}

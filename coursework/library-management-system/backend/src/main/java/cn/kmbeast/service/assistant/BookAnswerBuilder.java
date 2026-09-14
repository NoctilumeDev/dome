package cn.kmbeast.service.assistant;

import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Locale;
import java.util.Map;

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

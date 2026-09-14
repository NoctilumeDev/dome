package cn.kmbeast.service.assistant;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class BookQueryPlan {
    private BookIntent intent = BookIntent.SEARCH_BOOK;
    private String title;
    private String author;
    private String category;
    private String publisher;
    private List<String> keywords = new ArrayList<>();
    private Boolean availableOnly;
    private Integer limit = 20;
    private String planningNote;

    public boolean hasSearchCondition() {
        return hasContentCondition()
                || availableOnly != null;
    }

    public boolean hasContentCondition() {
        return hasText(title)
                || hasText(author)
                || hasText(category)
                || hasText(publisher)
                || (keywords != null && keywords.stream().anyMatch(BookQueryPlan::hasText));
    }

    public String primarySubject() {
        if (hasText(title)) {
            return title;
        }
        if (hasText(author)) {
            return author;
        }
        if (hasText(category)) {
            return category;
        }
        if (hasText(publisher)) {
            return publisher;
        }
        if (keywords != null) {
            for (String keyword : keywords) {
                if (hasText(keyword)) {
                    return keyword;
                }
            }
        }
        return "当前条件";
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}

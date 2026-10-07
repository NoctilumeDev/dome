package cn.kmbeast.service.assistant;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class BookQueryPlan {
    private String action = "QUERY";
    private String reason;
    private String timeOption = "ALL";
    private BookIntent intent = BookIntent.SEARCH_BOOK;
    private String title;
    private String author;
    private String category;
    private String publisher;
    private String userName;
    private List<String> keywords = new ArrayList<>();
    private Boolean availableOnly;
    private Boolean unreturnedOnly;
    private Integer days;
    private Integer limit = 20;
    private String planningNote;
    private String planningSource = "LOCAL_RULE";
    private Boolean modelCalled = false;

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
        if (hasText(userName)) {
            return userName;
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

    public boolean requiresAdmin() {
        return intent == BookIntent.LIST_USERS
                || intent == BookIntent.BORROW_OVERVIEW
                || intent == BookIntent.RECENT_RETURNS
                || intent == BookIntent.DUE_SOON
                || intent == BookIntent.OVERDUE_BORROWS
                || intent == BookIntent.FEEDBACK_OVERVIEW;
    }

    public boolean isBookIntent() {
        return intent == BookIntent.SEARCH_BOOK
                || intent == BookIntent.FIND_AUTHOR
                || intent == BookIntent.FIND_CATEGORY
                || intent == BookIntent.CHECK_AVAILABILITY
                || intent == BookIntent.RECOMMEND_BOOK
                || intent == BookIntent.FIND_LOCATION
                || intent == BookIntent.LIST_CATALOG;
    }

    public boolean isPersonal() {
        return intent == BookIntent.MY_BORROWS || intent == BookIntent.MY_DUE_SOON
                || intent == BookIntent.MY_REVIEWS || intent == BookIntent.MY_FEEDBACK;
    }

    /** Stored consent cannot be changed by a caller or a late planner. */
    public BookQueryPlan snapshot() {
        BookQueryPlan p = new BookQueryPlan();
        p.action = action; p.reason = reason; p.timeOption = timeOption; p.intent = intent;
        p.title = title; p.author = author; p.category = category; p.publisher = publisher;
        p.userName = userName; p.keywords = List.copyOf(keywords); p.availableOnly = availableOnly;
        p.unreturnedOnly = unreturnedOnly; p.days = days; p.limit = limit;
        p.planningNote = planningNote; p.planningSource = planningSource; p.modelCalled = modelCalled;
        return p;
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}

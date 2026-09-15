package cn.kmbeast.service.assistant;

import java.util.Locale;

public enum BookIntent {
    SEARCH_BOOK,
    FIND_AUTHOR,
    FIND_CATEGORY,
    CHECK_AVAILABILITY,
    RECOMMEND_BOOK,
    FIND_LOCATION,
    LIST_CATALOG,
    LIST_USERS,
    BORROW_OVERVIEW,
    MY_BORROWS,
    RECENT_RETURNS,
    DUE_SOON,
    MY_DUE_SOON,
    OVERDUE_BORROWS,
    SEARCH_REVIEWS,
    MY_REVIEWS,
    FEEDBACK_OVERVIEW,
    MY_FEEDBACK;

    public static BookIntent fromModelValue(String value) {
        if (value == null || value.isBlank()) {
            return SEARCH_BOOK;
        }
        try {
            return valueOf(value.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ignored) {
            return SEARCH_BOOK;
        }
    }
}

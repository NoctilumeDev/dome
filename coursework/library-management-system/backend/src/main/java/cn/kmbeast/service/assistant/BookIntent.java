package cn.kmbeast.service.assistant;

import java.util.Locale;

public enum BookIntent {
    SEARCH_BOOK,
    FIND_AUTHOR,
    FIND_CATEGORY,
    CHECK_AVAILABILITY,
    RECOMMEND_BOOK,
    FIND_LOCATION;

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

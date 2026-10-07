package cn.kmbeast.service.assistant;

import java.util.Set;

/** Finite capability checks; no interpretation of the original sentence. */
public final class BookPlanPolicy {
    private BookPlanPolicy() {}

    public static String check(BookQueryPlan p) {
        if (p == null || p.getAction() == null || !Set.of("QUERY", "CLARIFY", "REJECT").contains(p.getAction())) return "INVALID_PLAN";
        if (!"QUERY".equals(p.getAction())) return p.getReason();
        if (p.getIntent() == null || p.requiresAdmin() || p.getUserName() != null) return "FORBIDDEN";
        if (!p.isBookIntent() && !p.isPersonal() && p.getIntent() != BookIntent.SEARCH_REVIEWS) return "FORBIDDEN";
        if (p.getLimit() == null || p.getLimit() < 1 || p.getLimit() > 50) return "INVALID_PLAN";
        if (p.getKeywords() == null || p.getKeywords().size() > 3) return "INVALID_PLAN";
        for (String v : p.getKeywords()) if (!validText(v)) return "INVALID_PLAN";
        for (String v : new String[]{p.getTitle(), p.getAuthor(), p.getCategory(), p.getPublisher()})
            if (v != null && !validText(v)) return "INVALID_PLAN";
        boolean due = p.getIntent() == BookIntent.MY_DUE_SOON;
        if (due) {
            if (!"DUE_WITHIN".equals(p.getTimeOption()) || p.getDays() == null || p.getDays() < 1 || p.getDays() > 30) return "UNSUPPORTED_FILTER";
        } else if (!"ALL".equals(p.getTimeOption()) || p.getDays() != null) return "UNSUPPORTED_FILTER";
        if (p.isBookIntent()) {
            if (p.getUnreturnedOnly() != null) return "UNSUPPORTED_FILTER";
            if (p.getIntent() != BookIntent.LIST_CATALOG && !p.hasSearchCondition()) return "AMBIGUOUS";
        } else {
            if (p.getAuthor() != null || p.getCategory() != null || p.getPublisher() != null || !p.getKeywords().isEmpty() || p.getAvailableOnly() != null) return "UNSUPPORTED_FILTER";
            if (p.getIntent() == BookIntent.MY_FEEDBACK && p.getTitle() != null) return "UNSUPPORTED_FILTER";
            if (p.getUnreturnedOnly() != null && (p.getIntent() != BookIntent.MY_BORROWS || !p.getUnreturnedOnly())) return "UNSUPPORTED_FILTER";
        }
        return null;
    }
    private static boolean validText(String v) { return v != null && !v.isBlank() && v.length() <= 64; }

    public static String describe(BookQueryPlan p) {
        String label = switch (p.getIntent()) {
            case MY_BORROWS -> "当前账号的借阅记录";
            case MY_DUE_SOON -> "当前账号未来 " + p.getDays() + " 天内未归还、即将到期的借阅";
            case MY_REVIEWS -> "当前账号的书评";
            case MY_FEEDBACK -> "当前账号的反馈";
            case SEARCH_REVIEWS -> "公开书评";
            case FIND_LOCATION -> "馆藏位置";
            case CHECK_AVAILABILITY -> "馆藏可借状态";
            case RECOMMEND_BOOK -> "按馆藏匹配与可借数量排序";
            case LIST_CATALOG -> "馆藏总览";
            default -> "馆藏检索";
        };
        StringBuilder s = new StringBuilder(label);
        append(s, "书名包含", p.getTitle()); append(s, "作者包含", p.getAuthor());
        append(s, "分类包含", p.getCategory()); append(s, "出版社包含", p.getPublisher());
        if (!p.getKeywords().isEmpty()) s.append(" · 六项馆藏字段匹配任一关键词 ").append(p.getKeywords());
        if (p.getAvailableOnly() != null) s.append(p.getAvailableOnly() ? " · 当前有可借册" : " · 当前无可借册");
        if (Boolean.TRUE.equals(p.getUnreturnedOnly())) s.append(" · 仅未归还");
        if (p.isPersonal() && p.getIntent() != BookIntent.MY_DUE_SOON) s.append(" · 不按日期筛选");
        if (p.isPersonal() && p.getTitle() == null) s.append(" · 不按书名筛选");
        if (p.getIntent() == BookIntent.MY_BORROWS && p.getUnreturnedOnly() == null) s.append(" · 全部归还状态");
        return s.append(" · 最多返回 ").append(p.getLimit()).append(" 条，并显示匹配总数").toString();
    }
    private static void append(StringBuilder s, String label, String value) {
        if (value != null) s.append(" · ").append(label).append("「").append(value).append("」");
    }
}

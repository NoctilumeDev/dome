package cn.kmbeast.service.assistant;

import org.springframework.stereotype.Component;

import java.util.Locale;
import java.text.Normalizer;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 本地范围守卫，不调用大模型。
 */
@Component
public class BookScopeGuard {
    private static final Pattern QUOTED_TITLE = Pattern.compile(
            "《([^》]{1,64})》|“([^”]{1,64})”|『([^』]{1,64})』|\"([^\"]{1,64})\"|'([^']{1,64})'"
    );
    private static final Pattern EXISTENCE_TITLE = Pattern.compile(
            "^(?:请问|麻烦|帮我查一下|请帮我查一下)?\\s*(?:本馆|图书馆里?)?\\s*"
                    + "(?:有没有|是否有|有无)\\s*[《“『\"']?(.+?)[》”』\"']?"
                    + "(?:这本|这部)?(?:书|图书|书籍)?(?:吗|么|呢|吧)?[?？。!！]*$"
    );
    private static final Pattern QUALIFIED_TITLE = Pattern.compile(
            "^(.{2,40}?)(?:这本书)?(?:能借|可借|有库存|在哪里|在哪|放在哪里|放在哪)"
                    + "(?:吗|么|呢|吧)?[?？。!！]*$"
    );
    private static final Pattern LIBRARY_QUERY = Pattern.compile(
            "(?i)(图书馆|本馆|馆藏|图书|书籍|书名|作者|出版社|isbn|分类|类别|借阅|书架|用户|读者|"
                    + "还书|归还|借了|借过|没还|未还|还没还|未归还|尚未归还|借阅中|逾期|到期|反馈|意见|书评|评论|评分|"
                    + "小说|教材|著作|(?:推荐|查找|查询|搜索).{0,12}(?:书|读物)|"
                    + "(?:写的|著的|创作的)(?:书|作品)|(?:关于|相关|有关|方面|类).{0,12}(?:书|读物)|"
                    + "(?:可借|能借|库存).{0,12}(?:书|图书|书籍)|"
                    + "(?:书|图书|书籍).{0,12}(?:可借|能借|库存))"
    );
    private static final String[] OUT_OF_SCOPE_MARKERS = {
            "天气", "气温", "下雨", "新闻", "股票", "基金", "汇率", "彩票", "电影",
            "球赛", "比分", "笑话", "八卦", "课表", "考试答案", "作业答案", "感情",
            "写代码", "编程题", "写诗", "翻译", "菜谱", "路线导航", "你好", "谢谢",
            "你是谁", "聊天"
    };
    private static final String[] NON_TITLE_MARKERS = {
            "什么", "怎么", "为什么", "如何", "哪些", "所有", "全部", "推荐", "关于", "相关", "作者", "分类",
            "出版社", "可借", "库存", "借阅", "哪里", "在哪", "有没有", "是否",
            "写的书", "著的书", "创作的书", "写的作品", "著作", "书架", "用户", "读者",
            "还书", "归还", "没还", "未还", "还没还", "未归还", "尚未归还", "借阅中",
            "逾期", "到期", "反馈", "意见", "书评", "评论", "评分", "的图书", "的书籍"
    };

    public boolean isAllowed(String question) {
        if (question == null || question.trim().isEmpty()) {
            return false;
        }
        question = normalize(question);
        String normalized = question.toLowerCase(Locale.ROOT);
        if (hasQuotedTitle(question) || LIBRARY_QUERY.matcher(question).find()) {
            return true;
        }
        if (containsAny(normalized, OUT_OF_SCOPE_MARKERS)) {
            return false;
        }
        return extractDeterministicTitle(question) != null;
    }

    public String normalize(String question) {
        return Normalizer.normalize(question == null ? "" : question, Normalizer.Form.NFKC)
                .replaceAll("\\p{Cf}", "").trim();
    }

    /** Titles remain literal parameters, never instructions or executable SQL. */
    public String rejectionReason(String question) {
        String outsideTitles = withoutTitles(question);
        if (Pattern.compile("(?i)(密码(?!学)|密钥|api.?key|secret|access.?token|连接串|"
                + "忽略.{0,8}(规则|指令|限制)|绕过.{0,8}(权限|限制)|最高权限|最高管理员|程序创始人|"
                + "清空.{0,12}(数据库|数据|表)|删除.{0,12}(数据|用户|图书|记录)|"
                + "(?:执行|运行|输出|生成).{0,8}sql|drop\\s+table|delete\\s+from|truncate\\s+table|"
                + "insert\\s+into|update\\s+\\w+\\s+set)").matcher(outsideTitles).find()) {
            return "我只能查询图书馆记录，不能提供密码、变更身份或执行修改和删除操作。";
        }
        Matcher titles = QUOTED_TITLE.matcher(normalize(question));
        Set<String> distinct = new LinkedHashSet<>();
        while (titles.find()) distinct.add(titles.group());
        boolean borrows = Pattern.compile("借阅|借了|借过|未还|没还|归还|还书|逾期|到期").matcher(outsideTitles).find();
        int kinds = (borrows ? 1 : 0) + (outsideTitles.contains("反馈") ? 1 : 0)
                + (outsideTitles.matches("(?s).*(书评|评论).*") ? 1 : 0);
        if (distinct.size() > 1 || kinds > 1) {
            return "请一次查询一本书或一种记录。我会分别核对，避免遗漏你的其他问题。";
        }
        return null;
    }

    public String withoutTitles(String question) {
        return QUOTED_TITLE.matcher(normalize(question)).replaceAll("");
    }

    public String extractDeterministicTitle(String question) {
        if (question == null) {
            return null;
        }
        Matcher quotedMatcher = QUOTED_TITLE.matcher(question);
        if (quotedMatcher.find()) {
            for (int index = 1; index <= quotedMatcher.groupCount(); index++) {
                String value = quotedMatcher.group(index);
                if (value != null && !value.isBlank()) {
                    return value.trim();
                }
            }
        }

        String trimmed = question.trim();
        Matcher existenceMatcher = EXISTENCE_TITLE.matcher(trimmed);
        if (existenceMatcher.matches()) {
            String candidate = cleanTitleCandidate(existenceMatcher.group(1));
            if (candidate != null && !candidate.startsWith("关于") && !candidate.startsWith("有关")) {
                return candidate;
            }
        }
        Matcher qualifiedMatcher = QUALIFIED_TITLE.matcher(trimmed);
        if (qualifiedMatcher.matches()) {
            return cleanTitleCandidate(qualifiedMatcher.group(1));
        }

        String compact = trimmed.replaceAll("\\s+", " ");
        if (compact.length() < 2 || compact.length() > 40
                || !compact.matches("^[\\u4e00-\\u9fffA-Za-z0-9·\\-\\s]+$")
                || containsAny(compact.toLowerCase(Locale.ROOT), NON_TITLE_MARKERS)
                || containsAny(compact.toLowerCase(Locale.ROOT), OUT_OF_SCOPE_MARKERS)) {
            return null;
        }
        return compact;
    }

    public String refusalMessage() {
        return "抱歉，我目前只能回答本馆图书、书架、用户、借阅归还、逾期、反馈和书评相关问题。"
                + "你可以试试：有哪些馆藏、我借了哪些书、谁快要逾期了。";
    }

    private boolean hasQuotedTitle(String question) {
        return question != null && QUOTED_TITLE.matcher(question).find();
    }

    private String cleanTitleCandidate(String value) {
        if (value == null) {
            return null;
        }
        String cleaned = value.trim()
                .replaceAll("^(?:一本|一部|这本|这部)", "")
                .replaceAll("(?:这本|这部)?(?:书|图书|书籍)$", "")
                .trim();
        return cleaned.length() < 2 ? null : cleaned;
    }

    private boolean containsAny(String text, String... markers) {
        for (String marker : markers) {
            if (text.contains(marker.toLowerCase(Locale.ROOT))) {
                return true;
            }
        }
        return false;
    }
}

package cn.kmbeast.service.assistant;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonParser;
import cn.kmbeast.context.LocalThreadHolder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * DeepSeek 只负责语义解析，不生成答案，也不直接执行 SQL。
 */
@Component
public class DeepSeekBookQueryPlanner {
    private static final String DEFAULT_API_KEY = "123456789";
    private static final int MAX_FILTER_LENGTH = 64;
    private static final Set<String> FIELDS = Set.of("intent", "title", "author", "category", "publisher",
            "userName", "keywords", "availableOnly", "days", "limit");
    private static final String FENCE = String.valueOf((char) 96).repeat(3);
    private static final Pattern CODE_BLOCK = Pattern.compile(
            "(?s)" + Pattern.quote(FENCE) + "(?:json)?\\s*(.*?)\\s*" + Pattern.quote(FENCE)
    );
    private static final Pattern TOPIC_PATTERN = Pattern.compile(
            "(?:有关于|有没有关于|有没关于|关于|有关)\\s*(.+?)(?:的)?"
                    + "(?:书籍|图书|书本|书|著作|教材|资料)(?:吗|么|呢|吧|啊|呀)?[?？。!！]*$",
            Pattern.CASE_INSENSITIVE
    );
    private static final Pattern AUTHOR_PATTERN = Pattern.compile(
            "(.{1,32}?)(?:写的|著的|创作的)(?:书|图书|作品|著作)"
    );
    private static final Pattern RECOMMEND_PATTERN = Pattern.compile(
            "推荐(?:给我)?(?:几本|一些|一点|点)?\\s*(.+?)(?:类)?(?:书籍|图书|书|教材)[?？。!！]*$"
    );
    private static final Pattern LABELED_AUTHOR_PATTERN = Pattern.compile(
            "(?:作者是|作者叫|作者为|作者)\\s*[:：]?\\s*([^，。！？!?]{1,32})"
    );
    private static final Pattern LABELED_CATEGORY_PATTERN = Pattern.compile(
            "(?:分类是|类别是|分类|类别)\\s*[:：]?\\s*([^，。！？!?]{1,32})"
    );
    private static final Pattern LABELED_PUBLISHER_PATTERN = Pattern.compile(
            "(?:出版社是|出版社叫|出版社为|出版社)\\s*[:：]?\\s*([^，。！？!?]{1,32})"
    );
    private static final Pattern USER_BORROW_PATTERN = Pattern.compile(
            "([\\u4e00-\\u9fffA-Za-z0-9_]{1,20})(?:最近|刚才|目前)?(?:借了|借过|借阅了|借阅过)"
    );
    private static final Pattern USER_UNRETURNED_PATTERN = Pattern.compile(
            "^\\s*([\\u4e00-\\u9fffA-Za-z0-9_]{1,20}?)(?:有)?(?:哪些|哪几本|什么)"
                    + "(?:书|图书|书籍)?(?:还没还|没还|未还|未归还|尚未归还)"
    );
    private static final Pattern DAYS_PATTERN = Pattern.compile("(?:未来|接下来)?\\s*(\\d{1,2})\\s*天");

    @Value("$" + "{deepseek.api-url}")
    private String apiUrl;

    @Value("$" + "{deepseek.api-key:123456789}")
    private String apiKey;

    @Value("$" + "{deepseek.model:deepseek-chat}")
    private String model;

    @Value("${deepseek.timeout-ms:5000}")
    private long timeoutMillis = 5000;

    @Resource
    private ObjectMapper objectMapper;

    @Resource
    private BookScopeGuard scopeGuard;

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    private final Semaphore modelSlots = new Semaphore(4);
    private final Set<Integer> modelUsers = ConcurrentHashMap.newKeySet();

    public BookQueryPlan plan(String question) {
        BookQueryPlan localPlan = planWithoutModel(question);

        if (isDemoApiKey(apiKey)) {
            return localPlan;
        }
        Integer userId = LocalThreadHolder.getUserId();
        if (userId == null || !modelUsers.add(userId)) return busyPlan(localPlan);
        if (!modelSlots.tryAcquire()) {
            modelUsers.remove(userId);
            return busyPlan(localPlan);
        }
        try {
            BookQueryPlan modelPlan = planByModel(question);
            modelPlan = normalizeAndGround(modelPlan, localPlan, question);
            modelPlan.setPlanningSource("DEEPSEEK");
            modelPlan.setModelCalled(true);
            modelPlan.setPlanningNote("DeepSeek 已完成语义解析；答案仅来自数据库查询结果");
            return modelPlan;
        } catch (Exception ignored) {
            localPlan.setPlanningSource("DEEPSEEK_FALLBACK");
            localPlan.setModelCalled(true);
            localPlan.setPlanningNote("DeepSeek 暂时不可用，已使用本地安全解析；本次模型调用未成功");
            return localPlan;
        } finally {
            modelSlots.release();
            modelUsers.remove(userId);
        }
    }

    private BookQueryPlan busyPlan(BookQueryPlan plan) {
        plan.setPlanningSource("LOCAL_BUSY");
        plan.setPlanningNote("模型查询繁忙，已使用本地规则；本次未调用模型");
        return plan;
    }

    private BookQueryPlan planWithoutModel(String question) {
        BookQueryPlan systemPlan = planSystemQuery(question);
        if (systemPlan != null) {
            systemPlan.setPlanningSource("LOCAL_BUSINESS");
            systemPlan.setModelCalled(false);
            systemPlan.setPlanningNote(localBusinessNote(systemPlan));
            return systemPlan;
        }
        if (isCatalogOverviewQuestion(question)) {
            BookQueryPlan plan = new BookQueryPlan();
            plan.setIntent(BookIntent.LIST_CATALOG);
            plan.setLimit(50);
            plan.setPlanningSource("LOCAL_BUSINESS");
            plan.setModelCalled(false);
            plan.setPlanningNote("已识别为馆藏总览查询；本次未调用 DeepSeek，API 调用 0 次");
            return plan;
        }
        String deterministicTitle = scopeGuard.extractDeterministicTitle(question);
        if (deterministicTitle != null) {
            BookQueryPlan plan = new BookQueryPlan();
            plan.setTitle(deterministicTitle);
            if (containsAny(question, "哪里", "在哪", "位置", "放在")) {
                plan.setIntent(BookIntent.FIND_LOCATION);
            } else if (containsAny(question, "可借", "能借", "库存", "借完")) {
                plan.setIntent(BookIntent.CHECK_AVAILABILITY);
            }
            plan.setAvailableOnly(containsAny(question, "可借", "能借") ? Boolean.TRUE : null);
            plan.setPlanningSource("LOCAL_TITLE");
            plan.setModelCalled(false);
            plan.setPlanningNote("已使用本地精准书名解析；本次未调用 DeepSeek，API 调用 0 次");
            return plan;
        }
        BookQueryPlan fallback = planLocally(question);
        fallback.setPlanningSource("LOCAL_FALLBACK");
        fallback.setModelCalled(false);
        fallback.setPlanningNote("DeepSeek 密钥未配置，已使用本地安全解析；API 调用 0 次");
        return fallback;
    }

    private BookQueryPlan planByModel(String question) throws Exception {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("model", model);
        payload.put("temperature", 0);
        payload.put("max_tokens", 400);
        payload.put("messages", List.of(
                Map.of("role", "system", "content", buildSystemPrompt()),
                Map.of("role", "user", "content", question)
        ));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .timeout(Duration.ofMillis(timeoutMillis))
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(payload)))
                .build();

        CompletableFuture<HttpResponse<String>> future = httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString());
        HttpResponse<String> response;
        try {
            response = future.get(timeoutMillis, TimeUnit.MILLISECONDS);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw exception;
        } finally {
            if (!future.isDone()) future.cancel(true);
        }
        if (response.statusCode() / 100 != 2) {
            throw new IllegalStateException("模型服务响应异常");
        }

        JsonNode root = objectMapper.readTree(response.body());
        if (!"stop".equals(root.path("choices").path(0).path("finish_reason").asText())) {
            throw new IllegalStateException("模型输出未完整结束");
        }
        String content = root.path("choices").path(0).path("message").path("content").asText("");
        if (content.isBlank()) {
            throw new IllegalStateException("模型未返回查询计划");
        }
        Matcher matcher = CODE_BLOCK.matcher(content.trim());
        String json = matcher.matches() ? matcher.group(1) : content.trim();
        JsonNode node;
        try (JsonParser parser = objectMapper.getFactory().createParser(json)) {
            parser.enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
            node = objectMapper.readTree(parser);
            if (parser.nextToken() != null) throw new IllegalArgumentException("多个模型计划");
        }
        validateNode(node);

        BookQueryPlan plan = new BookQueryPlan();
        plan.setIntent(BookIntent.fromModelValue(node.get("intent").textValue()));
        plan.setTitle(textValue(node, "title"));
        plan.setAuthor(textValue(node, "author"));
        plan.setCategory(textValue(node, "category"));
        plan.setPublisher(textValue(node, "publisher"));
        plan.setUserName(textValue(node, "userName"));
        plan.setKeywords(readKeywords(node.path("keywords")));
        if (node.has("availableOnly") && !node.get("availableOnly").isNull()) {
            plan.setAvailableOnly(node.get("availableOnly").asBoolean());
        }
        plan.setLimit(node.path("limit").asInt(20));
        plan.setDays(Math.max(1, Math.min(node.path("days").asInt(3), 30)));
        return plan;
    }

    private void validateNode(JsonNode node) {
        if (node == null || !node.isObject() || !node.has("intent") || !node.get("intent").isTextual()) {
            throw new IllegalArgumentException("无效模型计划");
        }
        node.fieldNames().forEachRemaining(field -> {
            if (!FIELDS.contains(field)) throw new IllegalArgumentException("额外字段");
        });
        BookIntent.fromModelValue(node.get("intent").textValue());
        for (String field : List.of("title", "author", "category", "publisher", "userName")) {
            JsonNode value = node.get(field);
            if (value != null && !value.isNull() && (!value.isTextual()
                    || value.textValue().isBlank() || value.textValue().length() > MAX_FILTER_LENGTH)) {
                throw new IllegalArgumentException("无效文本条件");
            }
        }
        JsonNode keywords = node.get("keywords");
        if (keywords != null && (!keywords.isArray() || keywords.size() > 3)) throw new IllegalArgumentException("无效关键词");
        if (keywords != null) for (JsonNode value : keywords) {
            if (!value.isTextual() || value.textValue().isBlank() || value.textValue().length() > MAX_FILTER_LENGTH) {
                throw new IllegalArgumentException("无效关键词");
            }
        }
        JsonNode available = node.get("availableOnly");
        if (available != null && !available.isNull() && !available.isBoolean()) throw new IllegalArgumentException("无效库存条件");
        for (String field : List.of("limit", "days")) {
            JsonNode value = node.get(field);
            int max = field.equals("limit") ? 50 : 30;
            if (value != null && (!value.isIntegralNumber() || !value.canConvertToInt() || value.intValue() < 1 || value.intValue() > max)) {
                throw new IllegalArgumentException("无效数值条件");
            }
        }
    }

    private BookQueryPlan normalizeAndGround(BookQueryPlan modelPlan, BookQueryPlan localPlan, String question) {
        if (modelPlan.getIntent() != localPlan.getIntent()) throw new IllegalArgumentException("查询意图不一致");
        modelPlan.setTitle(groundedValue(modelPlan.getTitle(), question));
        modelPlan.setAuthor(groundedValue(modelPlan.getAuthor(), question));
        modelPlan.setPublisher(groundedValue(modelPlan.getPublisher(), question));
        modelPlan.setCategory(groundedValue(modelPlan.getCategory(), question));
        modelPlan.setUserName(groundedValue(modelPlan.getUserName(), question));

        Set<String> keywords = new LinkedHashSet<>();
        if (modelPlan.getKeywords() != null) {
            for (String keyword : modelPlan.getKeywords()) {
                String grounded = groundedValue(keyword, question);
                if (grounded != null && keywords.size() < 3) {
                    keywords.add(grounded);
                }
            }
        }
        modelPlan.setKeywords(new ArrayList<>(keywords));
        modelPlan.setLimit(clampLimit(modelPlan.getLimit()));

        if (!containsAny(question, "可借", "能借", "库存", "借完", "不可借", "无库存")) {
            modelPlan.setAvailableOnly(null);
        } else {
            modelPlan.setAvailableOnly(localPlan.getAvailableOnly());
        }
        modelPlan.setTitle(retainKnown(modelPlan.getTitle(), localPlan.getTitle()));
        modelPlan.setAuthor(retainKnown(modelPlan.getAuthor(), localPlan.getAuthor()));
        modelPlan.setPublisher(retainKnown(modelPlan.getPublisher(), localPlan.getPublisher()));
        modelPlan.setCategory(retainKnown(modelPlan.getCategory(), localPlan.getCategory()));
        modelPlan.setUserName(retainKnown(modelPlan.getUserName(), localPlan.getUserName()));
        if (!localPlan.isBookIntent() && (modelPlan.getAuthor() != null || modelPlan.getCategory() != null
                || modelPlan.getPublisher() != null || !modelPlan.getKeywords().isEmpty()
                || (modelPlan.getTitle() != null && localPlan.getTitle() == null)
                || (modelPlan.getUserName() != null && localPlan.getUserName() == null))) {
            throw new IllegalArgumentException("不支持的业务查询条件");
        }
        modelPlan.setIntent(localPlan.getIntent());
        modelPlan.setUnreturnedOnly(localPlan.getUnreturnedOnly());
        if (localPlan.getUserName() != null && !localPlan.getUserName().isBlank()) {
            modelPlan.setUserName(localPlan.getUserName());
        }
        if (localPlan.getDays() != null) {
            modelPlan.setDays(localPlan.getDays());
        }
        if ("编程".equals(localPlan.getCategory())
                && containsAny(question, "计算机", "程序设计", "软件开发")) {
            modelPlan.setCategory("编程");
            modelPlan.setKeywords(new ArrayList<>());
        }
        if (!modelPlan.hasContentCondition() && localPlan.hasContentCondition()) {
            localPlan.setLimit(modelPlan.getLimit());
            return localPlan;
        }
        return modelPlan;
    }

    private String retainKnown(String supplied, String known) {
        if (known == null) return supplied;
        if (supplied != null && !normalizeForGrounding(supplied).equals(normalizeForGrounding(known))) {
            throw new IllegalArgumentException("模型更改已知条件");
        }
        return known;
    }

    private BookQueryPlan planLocally(String question) {
        BookQueryPlan plan = new BookQueryPlan();
        String normalized = question.toLowerCase(Locale.ROOT);

        if (containsAny(normalized, "哪里", "在哪", "位置", "书架", "放在")) {
            plan.setIntent(BookIntent.FIND_LOCATION);
        } else if (containsAny(normalized, "推荐")) {
            plan.setIntent(BookIntent.RECOMMEND_BOOK);
        } else if (containsAny(normalized, "可借", "能借", "库存", "借完")) {
            plan.setIntent(BookIntent.CHECK_AVAILABILITY);
        } else if (containsAny(normalized, "作者", "谁写", "写的书", "著的书")) {
            plan.setIntent(BookIntent.FIND_AUTHOR);
        } else if (containsAny(normalized, "分类", "类别")) {
            plan.setIntent(BookIntent.FIND_CATEGORY);
        }

        if (containsAny(normalized, "可借", "能借", "有库存")) {
            plan.setAvailableOnly(Boolean.TRUE);
        } else if (containsAny(normalized, "不可借", "借完", "无库存")) {
            plan.setAvailableOnly(Boolean.FALSE);
        }

        String topic = firstMatch(TOPIC_PATTERN, question);
        String author = firstMatch(AUTHOR_PATTERN, question);
        if (author == null) {
            author = firstMatch(LABELED_AUTHOR_PATTERN, question);
        }
        String category = firstMatch(LABELED_CATEGORY_PATTERN, question);
        String publisher = firstMatch(LABELED_PUBLISHER_PATTERN, question);
        String recommendation = firstMatch(RECOMMEND_PATTERN, question);

        if (author != null) {
            plan.setAuthor(cleanFilter(author));
        }
        if (category != null) {
            plan.setCategory(cleanTail(category));
        }
        if (publisher != null) {
            plan.setPublisher(cleanTail(publisher));
        }
        if (containsAny(normalized, "计算机", "程序设计", "软件开发")) {
            plan.setCategory("编程");
        }
        if (topic != null) {
            addKeyword(plan, cleanFilter(topic));
        } else if (recommendation != null) {
            addKeyword(plan, cleanFilter(recommendation));
        }

        if (!plan.hasContentCondition()) {
            String keyword = question
                    .replaceAll("^(?:请问|麻烦|请|帮我|能不能|可以)?", "")
                    .replaceAll("(?:有|查询|查找|找一下|找|搜索|看看)", "")
                    .replaceAll("(?:哪些|哪几本|几本|一些|一点|相关的|有关的)", "")
                    .replaceAll("(?:可借的|能借的|目前可借)", "")
                    .replaceAll("(?:书籍|图书|书本|著作|教材|书)(?:吗|么|呢|吧|啊|呀)?[?？。!！]*$", "")
                    .replaceAll("[?？。!！,，]", " ")
                    .trim();
            addKeyword(plan, cleanFilter(keyword));
        }

        plan.setLimit(plan.getIntent() == BookIntent.RECOMMEND_BOOK ? 10 : 20);
        return plan;
    }

    private void addKeyword(BookQueryPlan plan, String keyword) {
        if (keyword != null && !keyword.isBlank()) {
            plan.getKeywords().add(keyword);
        }
    }

    private String groundedValue(String value, String question) {
        String cleaned = cleanFilter(value);
        if (cleaned == null) {
            return null;
        }
        String normalizedQuestion = normalizeForGrounding(question);
        String normalizedValue = normalizeForGrounding(cleaned);
        if (normalizedValue.isBlank() || !normalizedQuestion.contains(normalizedValue)) {
            throw new IllegalArgumentException("模型条件不来自问题");
        }
        return cleaned;
    }

    private String normalizeForGrounding(String value) {
        return value == null ? "" : value.toLowerCase(Locale.ROOT)
                .replaceAll("[\\s《》“”『』\"'，。！？!?、:：]", "");
    }

    private String cleanFilter(String value) {
        if (value == null) {
            return null;
        }
        String cleaned = value.trim()
                .replaceAll("^[\\s《》“”『』\"']+", "")
                .replaceAll("[\\s《》“”『』\"'，。！？!?、:：]+$", "")
                .replaceAll("^(?:可借的|能借的|目前可借的?)", "")
                .replaceAll("(?:相关的|有关的|方面的)$", "")
                .trim();
        if (cleaned.isBlank()) {
            return null;
        }
        return cleaned.length() > MAX_FILTER_LENGTH ? cleaned.substring(0, MAX_FILTER_LENGTH) : cleaned;
    }

    private String cleanTail(String value) {
        String cleaned = cleanFilter(value);
        if (cleaned == null) {
            return null;
        }
        cleaned = cleaned.replaceAll("(?:的)?(?:书籍|图书|书|有哪些|有吗|吗|么|呢)$", "")
                .replaceAll("类$", "")
                .trim();
        return cleaned.isBlank() ? null : cleaned;
    }

    private String firstMatch(Pattern pattern, String value) {
        Matcher matcher = pattern.matcher(value);
        return matcher.find() ? matcher.group(1) : null;
    }

    private List<String> readKeywords(JsonNode node) {
        List<String> values = new ArrayList<>();
        if (node.isArray()) {
            node.forEach(item -> values.add(item.asText("")));
        } else if (node.isTextual()) {
            values.add(node.asText(""));
        }
        return values;
    }

    private String textValue(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value == null || value.isNull() ? null : value.asText(null);
    }

    private int clampLimit(Integer limit) {
        if (limit == null) {
            return 20;
        }
        return Math.max(1, Math.min(limit, 50));
    }

    private boolean isDemoApiKey(String key) {
        return key == null || key.isBlank() || DEFAULT_API_KEY.equals(key.trim());
    }

    private boolean containsAny(String text, String... markers) {
        String normalized = text == null ? "" : text.toLowerCase(Locale.ROOT);
        for (String marker : markers) {
            if (normalized.contains(marker.toLowerCase(Locale.ROOT))) {
                return true;
            }
        }
        return false;
    }

    private boolean isCatalogOverviewQuestion(String question) {
        String normalized = question == null ? "" : question.toLowerCase(Locale.ROOT);
        boolean asksForList = containsAny(normalized, "哪些", "所有", "全部", "都有什么", "有什么");
        boolean mentionsCatalog = containsAny(normalized, "图书", "书籍", "馆藏", "书架");
        return asksForList && mentionsCatalog;
    }

    private BookQueryPlan planSystemQuery(String question) {
        String normalized = scopeGuard.withoutTitles(question).toLowerCase(Locale.ROOT);
        boolean personal = containsAny(normalized, "我借", "我的借", "我还", "我有", "我没还", "我未还",
                "我的反馈", "我的意见", "我的书评", "我的评论", "我快", "我是否");
        BookQueryPlan plan = new BookQueryPlan();
        plan.setTitle(scopeGuard.extractDeterministicTitle(question));

        if (containsAny(normalized, "书评", "图书评论", "读后评价", "图书评分")) {
            plan.setIntent(personal ? BookIntent.MY_REVIEWS : BookIntent.SEARCH_REVIEWS);
            plan.setTitle(scopeGuard.extractDeterministicTitle(question));
            return plan;
        }
        if (containsAny(normalized, "反馈", "意见建议", "读者意见")) {
            plan.setIntent(personal ? BookIntent.MY_FEEDBACK : BookIntent.FEEDBACK_OVERVIEW);
            plan.setUserName(extractUserName(question));
            return plan;
        }
        if (containsAny(normalized, "快要逾期", "即将逾期", "快逾期", "快到期", "即将到期")) {
            plan.setIntent(personal ? BookIntent.MY_DUE_SOON : BookIntent.DUE_SOON);
            plan.setDays(extractDays(question));
            plan.setUserName(extractUserName(question));
            return plan;
        }
        if (containsAny(normalized, "已经逾期", "逾期名单", "谁逾期", "哪些逾期")) {
            plan.setIntent(BookIntent.OVERDUE_BORROWS);
            plan.setUserName(extractUserName(question));
            return plan;
        }
        if (containsAny(normalized, "刚才还书", "最近还书", "最近归还", "谁还书", "谁归还")) {
            plan.setIntent(BookIntent.RECENT_RETURNS);
            plan.setUserName(extractUserName(question));
            return plan;
        }
        if (containsAny(normalized, "没还", "未还", "还没还", "未归还", "尚未归还", "借阅中")) {
            plan.setIntent(personal ? BookIntent.MY_BORROWS : BookIntent.BORROW_OVERVIEW);
            plan.setUserName(extractUnreturnedUserName(question));
            plan.setUnreturnedOnly(true);
            return plan;
        }
        if (containsAny(normalized, "谁借了", "借了什么", "借了哪些", "借阅记录", "借阅情况", "借过什么", "借过哪些", "我借的书")) {
            plan.setIntent(personal ? BookIntent.MY_BORROWS : BookIntent.BORROW_OVERVIEW);
            plan.setUserName(extractUserName(question));
            return plan;
        }
        if (containsAny(normalized, "有哪些用户", "所有用户", "用户列表", "读者名单", "有哪些读者")) {
            plan.setIntent(BookIntent.LIST_USERS);
            return plan;
        }
        return null;
    }

    private String extractUserName(String question) {
        Matcher namedRecord = Pattern.compile("(?:^|[，。\\s])(?:(?:请|只|帮我|查询|查看|查一下|查|给我)\\s*)*"
                + "([\\u4e00-\\u9fffA-Za-z0-9_]{1,20}?)(?:的)?(?:未来\\d{1,2}天|接下来\\d{1,2}天)?"
                + "(?:借阅记录|借阅情况|反馈|借了|借过|快要逾期|即将逾期|快逾期|快到期|即将到期|已经逾期|最近归还|最近还书|刚才还书)").matcher(question);
        if (namedRecord.find()) {
            String subject = namedRecord.group(1);
            return containsAny(subject, "我", "谁", "哪些", "所有") ? null : subject;
        }
        Matcher matcher = USER_BORROW_PATTERN.matcher(question);
        if (!matcher.find()) {
            return null;
        }
        String value = matcher.group(1).trim();
        return containsAny(value, "谁", "哪些", "什么", "我") ? null : value;
    }

    private String extractUnreturnedUserName(String question) {
        String compact = question == null ? "" : question.replaceAll("\\s+", "");
        if (compact.matches("^(?:我)?(?:有)?(?:哪些|哪几本|什么)(?:书|图书|书籍)?"
                + "(?:还没还|没还|未还|未归还|尚未归还)[?？。!！]*$")) {
            return null;
        }
        Matcher matcher = USER_UNRETURNED_PATTERN.matcher(question);
        if (!matcher.find()) {
            return null;
        }
        String value = matcher.group(1).trim();
        return containsAny(value, "谁", "哪些", "什么", "我") ? null : value;
    }

    private String localBusinessNote(BookQueryPlan plan) {
        if (Boolean.TRUE.equals(plan.getUnreturnedOnly())) {
            String subject = plan.getIntent() == BookIntent.MY_BORROWS ? "本人未归还" : "未归还借阅";
            return "已识别为" + subject + "查询；本次未调用 DeepSeek，API 调用 0 次";
        }
        return "已使用本地图书馆业务意图解析；本次未调用 DeepSeek，API 调用 0 次";
    }

    private int extractDays(String question) {
        Matcher matcher = DAYS_PATTERN.matcher(question);
        if (!matcher.find()) {
            return 3;
        }
        return Math.max(1, Math.min(Integer.parseInt(matcher.group(1)), 30));
    }

    private String buildSystemPrompt() {
        return "你是图书馆检索计划解析器，不是问答机器人。禁止回答用户问题，禁止编造书名、作者、分类或任何馆藏事实。"
                + "只提取用户原话中明确出现的查询条件，并且只输出一个 JSON 对象。"
                + "intent 必须是以下枚举之一：" + java.util.Arrays.toString(BookIntent.values()) + "。不得输出任何事实。"
                + "固定结构：{\"intent\":\"SEARCH_BOOK\",\"title\":null,\"author\":null,\"category\":null,"
                + "\"publisher\":null,\"userName\":null,\"keywords\":[],\"availableOnly\":null,\"days\":3,\"limit\":20}。"
                + "title 只放明确书名；author 只放作者名；category 只放明确分类；publisher 只放出版社；"
                + "keywords 最多 3 个，只能来自用户原句；availableOnly 可为 true、false 或 null；limit 范围 1 到 50。"
                + "例如“有关于Java的书籍吗”应把 Java 放入 keywords，不能把整句话作为关键词。"
                + "不要输出 SQL、Markdown、解释、推荐理由或数据库中是否存在该书。";
    }
}

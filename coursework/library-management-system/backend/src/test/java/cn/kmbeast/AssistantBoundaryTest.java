package cn.kmbeast;

import cn.kmbeast.Interceptor.JwtInterceptor;
import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.mapper.UserMapper;
import cn.kmbeast.pojo.entity.User;
import cn.kmbeast.service.assistant.*;
import cn.kmbeast.utils.JwtUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.util.ReflectionTestUtils;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class AssistantBoundaryTest {
    private final ObjectMapper json = new ObjectMapper();
    private final BookScopeGuard scope = new BookScopeGuard();
    private HttpServer server;
    private DeepSeekBookQueryPlanner planner;
    private final AtomicReference<String> payload = new AtomicReference<>();
    private final AtomicReference<String> finish = new AtomicReference<>("stop");
    private final CountDownLatch releaseBody = new CountDownLatch(1);
    private volatile boolean stalled;

    @BeforeEach void setup() throws Exception {
        LocalThreadHolder.setUserId(2, 2);
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/plan", exchange -> {
            exchange.getRequestBody().readAllBytes();
            try {
                if (stalled) {
                    exchange.sendResponseHeaders(200, 0);
                    exchange.getResponseBody().write(' ');
                    exchange.getResponseBody().flush();
                    try { releaseBody.await(3, TimeUnit.SECONDS); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                } else {
                    byte[] body = json.writeValueAsBytes(java.util.Map.of("choices", List.of(java.util.Map.of(
                            "finish_reason", finish.get(), "message", java.util.Map.of("content", payload.get())))));
                    exchange.sendResponseHeaders(200, body.length);
                    exchange.getResponseBody().write(body);
                }
            } finally { exchange.close(); }
        });
        server.start();
        planner = new DeepSeekBookQueryPlanner();
        ReflectionTestUtils.setField(planner, "objectMapper", json);
        ReflectionTestUtils.setField(planner, "scopeGuard", scope);
        ReflectionTestUtils.setField(planner, "apiKey", "fixture-only");
        ReflectionTestUtils.setField(planner, "model", "fixture-model");
        ReflectionTestUtils.setField(planner, "apiUrl", "http://127.0.0.1:" + server.getAddress().getPort() + "/plan");
        ReflectionTestUtils.setField(planner, "timeoutMillis", 800L);
    }

    @AfterEach void cleanup() {
        releaseBody.countDown(); server.stop(0); LocalThreadHolder.clear(); Thread.interrupted();
    }

    private static String plan(String intent, String title) {
        return "{\"action\":\"QUERY\",\"intent\":\"" + intent + "\",\"title\":"
                + (title == null ? "null" : "\"" + title + "\"")
                + ",\"author\":null,\"category\":null,\"publisher\":null,\"keywords\":[],\"availableOnly\":null,\"unreturnedOnly\":null,\"timeOption\":\"ALL\",\"days\":null,\"limit\":20,\"reason\":null}";
    }
    static Stream<String> badPlans() {
        String valid = plan("SEARCH_BOOK", "三体");
        return Stream.of(
                valid.replace("\"title\":\"三体\"", "\"title\":true"),
                valid.replace("\"keywords\":[]", "\"keywords\":\"三体\""),
                valid.replace("\"availableOnly\":null", "\"availableOnly\":\"yes\""),
                valid.replace("\"limit\":20", "\"limit\":\"20\""),
                valid.replace("\"limit\":20", "\"limit\":999999"),
                valid.replace("\"days\":null", "\"days\":0"),
                valid.replace("\"reason\":null", "\"reason\":null,\"userId\":3"),
                valid.replace("\"reason\":null", "\"reason\":null,\"sql\":\"DROP TABLE user\""),
                valid.replace("\"reason\":null", "\"reason\":null,\"userName\":\"李四\""),
                valid.replace("\"reason\":null", "\"reason\":null,\"actions\":[]"),
                valid.replace("\"intent\":\"SEARCH_BOOK\"", "\"intent\":\"SEARCH_BOOK\",\"intent\":\"MY_BORROWS\""),
                valid + valid, "explanation " + valid, "[]", "null", "not JSON");
    }
    @ParameterizedTest @MethodSource("badPlans") void invalidProviderPlanCannotExecuteOrGuessFallback(String value) {
        payload.set(value);
        BookQueryPlan result = planner.plan("请查《三体》的馆藏");
        assertEquals("REJECT", result.getAction());
        assertEquals("INVALID_PLAN", result.getReason());
        assertTrue(result.getModelCalled());
    }
    @Test void validProviderAndWholeFenceRemainSupported() {
        payload.set("```json\n" + plan("SEARCH_BOOK", "三体") + "\n```");
        assertEquals("MODEL", planner.plan("请查《三体》的馆藏").getPlanningSource());
    }
    @Test void openLanguageTypeBelongsToModelAndFinalCapabilityValidation() {
        payload.set(plan("FIND_LOCATION", "三体"));
        BookQueryPlan p = planner.plan("我的借阅记录先不查，只查《三体》放在哪里");
        assertEquals(BookIntent.FIND_LOCATION, p.getIntent());
        assertNull(BookPlanPolicy.check(p));
        payload.set(plan("LIST_USERS", null));
        assertEquals("FORBIDDEN", BookPlanPolicy.check(planner.plan("有哪些用户")));
    }
    @Test void declaredUnsupportedConditionsAreNotDropped() {
        payload.set(plan("MY_BORROWS", "三体").replace("\"timeOption\":\"ALL\"", "\"timeOption\":\"TODAY\""));
        BookQueryPlan p = planner.plan("我今天借了哪些图书");
        assertEquals("TODAY", p.getTimeOption());
        assertEquals("UNSUPPORTED_FILTER", BookPlanPolicy.check(p));
        payload.set(plan("MY_FEEDBACK", "三体"));
        assertEquals("UNSUPPORTED_FILTER", BookPlanPolicy.check(planner.plan("我的三体反馈")));
    }
    @Test void partialGenerationAndStalledBodyClarifyWithoutQuery() {
        payload.set(plan("SEARCH_BOOK", "三体")); finish.set("length");
        assertEquals("CLARIFY", planner.plan("请查《三体》的馆藏").getAction());
        stalled = true; ReflectionTestUtils.setField(planner, "timeoutMillis", 200L);
        long start = System.nanoTime();
        assertEquals("CLARIFY", planner.plan("请查《三体》的馆藏").getAction());
        assertTrue(TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - start) < 1000);
    }
    @Test void interruptionIsRestored() {
        payload.set(plan("SEARCH_BOOK", "三体")); Thread.currentThread().interrupt();
        assertEquals("CLARIFY", planner.plan("请查《三体》的馆藏").getAction());
        assertTrue(Thread.currentThread().isInterrupted());
    }

    @Test void currentDatabaseStateControlsOldJwt() throws Exception {
        JwtUtil config = new JwtUtil(); config.setSecret("test-only-random-session-signing-key-0123456789"); config.setExpiration(60000L);
        String adminToken = JwtUtil.toToken(1, 1);
        UserMapper mapper = mock(UserMapper.class);
        User account = User.builder().id(1).userRole(1).isLogin(false).build();
        when(mapper.getByActive(any())).thenAnswer(invocation -> account);
        JwtInterceptor interceptor = new JwtInterceptor("/api", mapper);
        MockHttpServletRequest request = new MockHttpServletRequest("POST", "/api/user/query");
        request.setAttribute(org.springframework.web.servlet.HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE, "/user/query");
        request.addHeader("token", adminToken);
        assertTrue(interceptor.preHandle(request, new MockHttpServletResponse(), new Object()));
        account.setUserRole(2);
        MockHttpServletResponse denied = new MockHttpServletResponse();
        assertFalse(interceptor.preHandle(request, denied, new Object())); assertEquals(403, denied.getStatus());
        request.setRequestURI("/api/book/assistant/query");
        request.setAttribute(org.springframework.web.servlet.HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE, "/book/assistant/query");
        assertTrue(interceptor.preHandle(request, new MockHttpServletResponse(), new Object()));
        assertEquals(2, LocalThreadHolder.getRoleId());
        account.setIsLogin(true);
        denied = new MockHttpServletResponse();
        assertFalse(interceptor.preHandle(request, denied, new Object())); assertEquals(401, denied.getStatus());
        assertNull(((ThreadLocal<?>) ReflectionTestUtils.getField(LocalThreadHolder.class, "USER_HOLDER")).get());
        when(mapper.getByActive(any())).thenReturn(null);
        assertFalse(interceptor.preHandle(request, new MockHttpServletResponse(), new Object()));
    }

    @Test void scopeRegressionBank() throws Exception {
        var resource = getClass().getResourceAsStream("/assistant-cases.json");
        assertNotNull(resource);
        for (var entry : json.readTree(resource).get("cases")) {
            String question = entry.get("question").asText();
            String reason = scope.rejectionReason(question);
            String actual = reason != null ? (reason.startsWith("请一次") ? "CLARIFY" : "REJECT")
                    : (scope.isAllowed(question) ? "ALLOW" : "REJECT");
            assertEquals(entry.get("expected").asText(), actual, question);
        }
    }
}

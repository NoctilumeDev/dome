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

    static Stream<String> badPlans() {
        return Stream.of(
                "{\"intent\":\"MY_FEEDBACK\",\"title\":\"三体\"}",
                "{\"intent\":\"MY_BORROWS\",\"title\":\"三体\"}",
                "{\"intent\":\"LIST_USERS\",\"title\":\"三体\"}",
                "{\"intent\":\"DELETE_ALL\",\"title\":\"三体\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"title\":\"三体\",\"userId\":3}",
                "{\"intent\":\"SEARCH_BOOK\",\"title\":\"三体\",\"sql\":\"DROP TABLE user\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"intent\":\"MY_FEEDBACK\",\"title\":\"三体\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"title\":\"三体\"} {\"intent\":\"LIST_USERS\"}",
                "explanation {\"intent\":\"SEARCH_BOOK\",\"title\":\"三体\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"title\":true}",
                "{\"intent\":\"SEARCH_BOOK\",\"keywords\":\"三体\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"availableOnly\":\"yes\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"limit\":\"20\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"limit\":999999}",
                "{\"intent\":\"SEARCH_BOOK\",\"days\":0}",
                "{\"intent\":\"SEARCH_BOOK\",\"title\":\"虚构馆藏\"}",
                "{\"intent\":\"SEARCH_BOOK\",\"title\":\"活着\"}",
                "[]", "null", "not JSON");
    }

    @ParameterizedTest @MethodSource("badPlans") void badProviderCannotChangePurpose(String value) {
        payload.set(value);
        BookQueryPlan result = planner.plan("查《三体》");
        assertEquals(BookIntent.SEARCH_BOOK, result.getIntent());
        assertEquals("三体", result.getTitle());
        assertEquals("DEEPSEEK_FALLBACK", result.getPlanningSource());
        assertTrue(result.getModelCalled());
    }

    @Test void validProviderAndWholeFenceRemainSupported() {
        payload.set("```json\n{\"intent\":\"SEARCH_BOOK\",\"title\":\"三体\",\"keywords\":[],\"availableOnly\":null,\"limit\":20}\n```");
        assertEquals("DEEPSEEK", planner.plan("查《三体》").getPlanningSource());
    }
    @Test void catalogCanRetainAnExplicitAuthorFilter() {
        payload.set("{\"intent\":\"LIST_CATALOG\",\"author\":\"不存在的人\"}");
        BookQueryPlan result = planner.plan("作者是不存在的人，本馆有哪些图书？");
        assertEquals("DEEPSEEK", result.getPlanningSource());
        assertEquals("不存在的人", result.getAuthor());
    }

    @Test void partialGenerationAndStalledBodyFallBack() {
        payload.set("{\"intent\":\"SEARCH_BOOK\",\"title\":\"三体\"}");
        finish.set("length");
        assertEquals("DEEPSEEK_FALLBACK", planner.plan("查《三体》").getPlanningSource());
        stalled = true;
        ReflectionTestUtils.setField(planner, "timeoutMillis", 200L);
        long start = System.nanoTime();
        assertEquals("DEEPSEEK_FALLBACK", planner.plan("查《三体》").getPlanningSource());
        assertTrue(TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - start) < 1000);
    }

    @Test void interruptionIsRestored() {
        payload.set("{\"intent\":\"SEARCH_BOOK\"}");
        Thread.currentThread().interrupt();
        assertEquals("DEEPSEEK_FALLBACK", planner.plan("查《三体》").getPlanningSource());
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
        request.addHeader("token", adminToken);
        assertTrue(interceptor.preHandle(request, new MockHttpServletResponse(), new Object()));
        account.setUserRole(2);
        MockHttpServletResponse denied = new MockHttpServletResponse();
        assertFalse(interceptor.preHandle(request, denied, new Object())); assertEquals(403, denied.getStatus());
        request.setRequestURI("/api/book/assistant/query");
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

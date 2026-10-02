package cn.kmbeast;

import cn.kmbeast.Interceptor.JwtInterceptor;
import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.mapper.UserMapper;
import cn.kmbeast.pojo.entity.User;
import cn.kmbeast.utils.JwtUtil;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.util.pattern.PathPatternParser;

import java.net.URI;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.test.web.servlet.setup.MockMvcBuilders.standaloneSetup;

class RouteAuthorizationTest {
    private UserMapper users;
    private String readerToken;
    private String adminToken;

    @BeforeEach void setup() {
        JwtUtil jwt = new JwtUtil();
        jwt.setSecret("local-route-regression-signing-key-0123456789");
        jwt.setExpiration(60000L);
        users = mock(UserMapper.class);
        when(users.getByActive(any())).thenAnswer(call -> {
            User query = call.getArgument(0);
            return User.builder().id(query.getId()).userRole(query.getId() == 1 ? 1 : 2).isLogin(false).build();
        });
        readerToken = JwtUtil.toToken(2, 2);
        adminToken = JwtUtil.toToken(1, 1);
    }

    @AfterEach void cleanup() { LocalThreadHolder.clear(); }

    @RestController static class Endpoints {
        final AtomicInteger adminCalls = new AtomicInteger();
        @PostMapping("/user/query") String query() { adminCalls.incrementAndGet(); return "admin-only"; }
        @PutMapping("/user/backUpdate") String update() { adminCalls.incrementAndGet(); return "updated"; }
        @PutMapping("/book/update") String book() { adminCalls.incrementAndGet(); return "updated"; }
        @PutMapping("/user/freeze/{id}") String freeze(@PathVariable String id) { adminCalls.incrementAndGet(); return "frozen"; }
        @PostMapping("/book/assistant/query") String assistant() { return "reader-allowed"; }
        @PostMapping("/user/login") String login() { return "login-allowed"; }
    }

    @Test void readerCannotReachAdminHandlersThroughAlternatePaths() throws Exception {
        for (boolean parsed : new boolean[]{false, true}) {
            Endpoints controller = new Endpoints();
            var builder = standaloneSetup(controller).addInterceptors(new JwtInterceptor("/api", users));
            if (parsed) builder.setPatternParser(new PathPatternParser());
            MockMvc mvc = builder.build();
            for (String path : new String[]{"/user/query", "/user/query;x", "/user;x/query;y", "/user/query/", "/user/%71uery"})
                mvc.perform(post(URI.create("/api" + path)).contextPath("/api").header("token", readerToken))
                        .andExpect(status().isForbidden());
            for (String path : new String[]{"/user/backUpdate;x", "/book/update;x", "/user/freeze/3;x"})
                mvc.perform(put(URI.create("/api" + path)).contextPath("/api").header("token", readerToken))
                        .andExpect(status().isForbidden());
            assertEquals(0, controller.adminCalls.get());
        }
    }

    @Test void adminReaderAndPublicControlsRemainAvailable() throws Exception {
        for (boolean parsed : new boolean[]{false, true}) {
            Endpoints controller = new Endpoints();
            var builder = standaloneSetup(controller).addInterceptors(new JwtInterceptor("/api", users));
            if (parsed) builder.setPatternParser(new PathPatternParser());
            MockMvc mvc = builder.build();
            mvc.perform(post("/api/user/query").contextPath("/api").header("token", adminToken))
                    .andExpect(status().isOk()).andExpect(content().string("admin-only"));
            mvc.perform(post("/api/book/assistant/query").contextPath("/api").header("token", readerToken))
                    .andExpect(status().isOk()).andExpect(content().string("reader-allowed"));
            mvc.perform(post("/api/user/login").contextPath("/api"))
                    .andExpect(status().isOk()).andExpect(content().string("login-allowed"));
            mvc.perform(post("/api/user/query").contextPath("/api"))
                    .andExpect(status().isUnauthorized());
            assertEquals(1, controller.adminCalls.get());
        }
    }
}

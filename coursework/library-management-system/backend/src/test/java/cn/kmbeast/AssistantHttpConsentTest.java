package cn.kmbeast;

import cn.kmbeast.Interceptor.JwtInterceptor;
import cn.kmbeast.controller.BookController;
import cn.kmbeast.mapper.UserMapper;
import cn.kmbeast.pojo.entity.User;
import cn.kmbeast.service.assistant.*;
import cn.kmbeast.service.impl.BookAssistantServiceImpl;
import cn.kmbeast.utils.JwtUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.test.web.servlet.setup.MockMvcBuilders.standaloneSetup;

class AssistantHttpConsentTest {
    @Test void authenticatedConfirmationExecutesDisplayedPlanAndFreshAccountState() throws Exception {
        AssistantFactsTest fixture = new AssistantFactsTest();
        ReflectionTestUtils.invokeMethod(fixture, "setup");
        try {
            BookAssistantServiceImpl service = (BookAssistantServiceImpl) ReflectionTestUtils.getField(fixture, "service");
            DeepSeekBookQueryPlanner planner = mock(DeepSeekBookQueryPlanner.class);
            BookQueryPlan p = new BookQueryPlan(); p.setIntent(BookIntent.MY_BORROWS); p.setPlanningSource("MODEL");
            when(planner.plan(anyString())).thenReturn(p); ReflectionTestUtils.setField(service, "queryPlanner", planner);
            BookController controller = new BookController(); ReflectionTestUtils.setField(controller, "bookAssistantService", service);
            UserMapper users = mock(UserMapper.class);
            User current = User.builder().id(2).userRole(2).isLogin(false).build();
            when(users.getByActive(any())).thenAnswer(c -> current);
            JwtUtil config = new JwtUtil(); config.setSecret("http-scope-fixture-signing-key-0123456789"); config.setExpiration(60000L);
            String token = JwtUtil.toToken(2, 2);
            var mvc = standaloneSetup(controller).addInterceptors(new JwtInterceptor("/api", users)).build();
            ObjectMapper json = new ObjectMapper();
            String body = mvc.perform(post("/api/book/assistant/query").contextPath("/api").header("token", token)
                    .contentType("application/json").content("{\"question\":\"查询我今天的借阅记录\"}"))
                    .andExpect(status().isOk()).andExpect(jsonPath("$.data.status").value("CONFIRM_SCOPE"))
                    .andExpect(jsonPath("$.data.records").isEmpty()).andReturn().getResponse().getContentAsString();
            String consent = json.readTree(body).path("data").path("confirmationToken").asText();
            String confirm = json.writeValueAsString(java.util.Map.of("confirmationToken", consent));
            mvc.perform(post("/api/book/assistant/confirm").contextPath("/api").contentType("application/json").content(confirm))
                    .andExpect(status().isUnauthorized());
            current.setIsLogin(true);
            mvc.perform(post("/api/book/assistant/confirm").contextPath("/api").header("token", token).contentType("application/json").content(confirm))
                    .andExpect(status().isUnauthorized());
            current.setIsLogin(false);
            mvc.perform(post("/api/book/assistant/confirm").contextPath("/api").header("token", token).contentType("application/json").content(confirm))
                    .andExpect(jsonPath("$.data.status").value("QUERY")).andExpect(jsonPath("$.data.total").value(1));
            mvc.perform(post("/api/book/assistant/confirm").contextPath("/api").header("token", token).contentType("application/json").content(confirm))
                    .andExpect(jsonPath("$.code").value(400));
            verify(planner, times(1)).plan(anyString());
        } finally { ReflectionTestUtils.invokeMethod(fixture, "cleanup"); }
    }
}

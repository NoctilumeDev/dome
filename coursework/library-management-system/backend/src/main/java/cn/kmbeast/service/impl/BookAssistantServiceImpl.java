package cn.kmbeast.service.impl;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookAssistantQueryDto;
import cn.kmbeast.pojo.vo.BookAssistantVO;
import cn.kmbeast.service.BookAssistantService;
import cn.kmbeast.service.assistant.BookAnswerBuilder;
import cn.kmbeast.service.assistant.BookQueryPlan;
import cn.kmbeast.service.assistant.BookQueryRepository;
import cn.kmbeast.service.assistant.BookScopeGuard;
import cn.kmbeast.service.assistant.DeepSeekBookQueryPlanner;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 图书智能问答编排层。
 */
@Service
public class BookAssistantServiceImpl implements BookAssistantService {
    private static final int MAX_QUESTION_LENGTH = 120;

    @Resource
    private BookScopeGuard scopeGuard;

    @Resource
    private DeepSeekBookQueryPlanner queryPlanner;

    @Resource
    private BookQueryRepository queryRepository;

    @Resource
    private BookAnswerBuilder answerBuilder;

    @Override
    public Result<BookAssistantVO> ask(BookAssistantQueryDto dto) {
        if (dto == null || dto.getQuestion() == null || dto.getQuestion().trim().isEmpty()) {
            return ApiResult.error("问题不能为空");
        }

        String question = dto.getQuestion().trim();
        if (question.length() > MAX_QUESTION_LENGTH) {
            return ApiResult.error("问题过长，请控制在 " + MAX_QUESTION_LENGTH + " 个字符内");
        }

        if (!scopeGuard.isAllowed(question)) {
            BookAssistantVO refused = new BookAssistantVO();
            refused.setQuestion(question);
            refused.setIntent("OUT_OF_SCOPE");
            refused.setDatabaseVerified(false);
            refused.setGeneratedSql("");
            refused.setModelNote("已由本地范围规则拒绝，未调用 DeepSeek");
            refused.setAnswer(scopeGuard.refusalMessage());
            refused.setTotal(0);
            refused.setBooks(new ArrayList<>());
            return ApiResult.success(refused);
        }

        BookQueryPlan plan = queryPlanner.plan(question);
        Integer currentUserId = LocalThreadHolder.getUserId();
        boolean isAdmin = Integer.valueOf(1).equals(LocalThreadHolder.getRoleId());
        if (plan.requiresAdmin() && !isAdmin) {
            BookAssistantVO denied = new BookAssistantVO();
            denied.setQuestion(question);
            denied.setIntent("FORBIDDEN");
            denied.setDatabaseVerified(false);
            denied.setGeneratedSql("");
            denied.setModelNote("已在执行 SQL 前完成角色权限拦截");
            denied.setAnswer("该问题涉及其他读者的身份或借阅记录，仅管理员可以查询。你可以查询自己的借阅、反馈和书评。");
            denied.setTotal(0);
            denied.setBooks(new ArrayList<>());
            return ApiResult.success(denied);
        }
        try {
            BookQueryRepository.QueryResult queryResult = queryRepository.query(plan, currentUserId, isAdmin);
            List<Map<String, Object>> rows = queryResult.getRows();

            BookAssistantVO response = new BookAssistantVO();
            response.setQuestion(question);
            response.setIntent(plan.getIntent().name());
            response.setDatabaseVerified(true);
            response.setGeneratedSql(queryResult.getDisplaySql());
            response.setModelNote(plan.getPlanningNote());
            response.setAnswer(answerBuilder.build(question, plan, rows));
            response.setTotal(rows.size());
            response.setBooks(plan.isBookIntent() ? rows : new ArrayList<>());
            return ApiResult.success(response);
        } catch (IllegalStateException exception) {
            return ApiResult.error("馆藏数据库查询失败，请稍后重试");
        }
    }
}

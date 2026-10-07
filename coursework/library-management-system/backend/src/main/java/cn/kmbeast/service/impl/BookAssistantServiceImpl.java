package cn.kmbeast.service.impl;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.pojo.api.*;
import cn.kmbeast.pojo.dto.query.extend.BookAssistantQueryDto;
import cn.kmbeast.pojo.vo.BookAssistantVO;
import cn.kmbeast.service.BookAssistantService;
import cn.kmbeast.service.assistant.*;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import java.util.*;

/** Interpretation, capability qualification, consent and fixed facts are separate steps. */
@Service
public class BookAssistantServiceImpl implements BookAssistantService {
    @Resource private BookScopeGuard scopeGuard;
    @Resource private DeepSeekBookQueryPlanner queryPlanner;
    @Resource private BookQueryRepository queryRepository;
    @Resource private BookAnswerBuilder answerBuilder;
    @Resource private BookScopeConsents consents;

    @Override public Result<BookAssistantVO> ask(BookAssistantQueryDto dto) { return ask(dto, null); }
    @Override public Result<BookAssistantVO> ask(BookAssistantQueryDto dto, String session) {
        Integer actor = LocalThreadHolder.getUserId();
        BookScopeConsents.Ticket ticket = consents.begin(actor, session);
        if (dto == null || dto.getQuestion() == null || dto.getQuestion().isBlank()) return ApiResult.error("问题不能为空");
        String q = scopeGuard.normalize(dto.getQuestion());
        if (q.length() > 2048) return ApiResult.error("问题过长，请控制在 2048 个字符内");
        String rejection = scopeGuard.rejectionReason(q);
        if (rejection != null || !scopeGuard.isAllowed(q)) {
            BookAssistantVO r = empty(q, "REJECT", rejection == null ? "OUT_OF_SCOPE" : "FORBIDDEN", null);
            r.setPlanningSource("LOCAL_SCOPE");
            r.setAnswer(rejection == null ? scopeGuard.refusalMessage() : rejection + " 请单独提交合法查询。");
            return ApiResult.success(r);
        }
        BookQueryPlan proposed = queryPlanner.plan(q);
        String failure = BookPlanPolicy.check(proposed);
        if (proposed == null || !"QUERY".equals(proposed.getAction()) || failure != null) {
            String reason = failure == null ? "INVALID_PLAN" : failure;
            String status = proposed != null && "REJECT".equals(proposed.getAction())
                    || Set.of("FORBIDDEN", "INVALID_PLAN", "OUT_OF_SCOPE").contains(reason) ? "REJECT" : "CLARIFY";
            return ApiResult.success(empty(q, status, reason, proposed));
        }
        BookQueryPlan plan = proposed.snapshot();
        if (plan.isPersonal() && !"STANDARD_COMMAND".equals(plan.getPlanningSource())) {
            BookScopeConsents.Offered offer = consents.offer(ticket, q, plan);
            if (offer == null) return ApiResult.success(empty(q, "CLARIFY", "STALE_OR_UNAVAILABLE", plan));
            BookAssistantVO r = empty(q, "CONFIRM_SCOPE", null, plan);
            r.setInterpretation(BookPlanPolicy.describe(plan));
            r.setConfirmationToken(offer.token()); r.setConfirmationExpiresAt(offer.expiresAt().toString());
            r.setAnswer("请核对上面的实际查询范围。确认后才读取个人记录；不是这个意思可以修改问题或到对应记录页面查询。");
            return ApiResult.success(r);
        }
        return execute(q, plan, actor);
    }

    @Override public Result<BookAssistantVO> confirm(Map<String, Object> dto, String session) {
        if (dto == null || !dto.keySet().equals(Set.of("confirmationToken"))
                || !(dto.get("confirmationToken") instanceof String) || ((String) dto.get("confirmationToken")).length() > 64)
            return ApiResult.error("确认只能提交当前范围令牌");
        Integer actor = LocalThreadHolder.getUserId();
        BookScopeConsents.Confirmed confirmed = consents.consume(actor, session, (String) dto.get("confirmationToken"));
        if (confirmed == null) return ApiResult.error("确认已过期、已使用或不属于当前会话，请重新提问");
        return execute(confirmed.question(), confirmed.plan(), actor);
    }

    private Result<BookAssistantVO> execute(String q, BookQueryPlan p, Integer actor) {
        if (BookPlanPolicy.check(p) != null) return ApiResult.success(empty(q, "REJECT", "INVALID_PLAN", p));
        try {
            // Admin status cannot change the capabilities of this entry point.
            BookQueryRepository.QueryResult facts = queryRepository.query(p, actor, false);
            List<Map<String, Object>> rows = facts.getRows();
            BookAssistantVO r = empty(q, "QUERY", null, p);
            r.setInterpretation(BookPlanPolicy.describe(p)); r.setDatabaseVerified(true);
            String answer = answerBuilder.build(q, p, rows);
            if (p.getIntent() == BookIntent.LIST_CATALOG) answer = "本馆共登记 " + facts.getCatalogCount()
                    + " 种图书，已登记 " + facts.getShelfCount() + " 个书架。\n" + answer;
            if (facts.getTotal() > rows.size()) answer = "符合条件共 " + facts.getTotal() + " 条，本次仅返回前 " + rows.size() + " 条。\n" + answer;
            r.setAnswer(answer); r.setTotal(facts.getTotal()); r.setReturnedCount(rows.size());
            r.setTruncated(facts.getTotal() > rows.size());
            r.setBooks(p.isBookIntent() ? rows : List.of()); r.setRecords(p.isBookIntent() ? List.of() : rows);
            return ApiResult.success(r);
        } catch (IllegalStateException e) { return ApiResult.error("馆藏数据库查询失败，请稍后重试"); }
    }
    private BookAssistantVO empty(String q, String status, String reason, BookQueryPlan p) {
        BookAssistantVO r = new BookAssistantVO(); r.setQuestion(q); r.setStatus(status); r.setReason(reason);
        r.setIntent(p != null && p.getIntent() != null ? p.getIntent().name() : status);
        r.setDatabaseVerified(false); r.setGeneratedSql(""); r.setBooks(List.of()); r.setRecords(List.of());
        r.setTotal(0); r.setReturnedCount(0); r.setTruncated(false); r.setModelCalled(p != null && Boolean.TRUE.equals(p.getModelCalled()));
        if (p != null) { r.setModelNote(p.getPlanningNote()); r.setPlanningSource(p.getPlanningSource()); }
        r.setAnswer(switch (reason == null ? "" : reason) {
            case "UNSUPPORTED_FILTER" -> "我理解了查询，但当前不支持其中的筛选条件，没有删除条件后扩大查询。请到对应记录页面查询或明确改用支持的范围。";
            case "MULTIPLE_ACTIONS" -> "你保留了多个业务查询，请一次提交一个。";
            case "AMBIGUOUS" -> "尚不能确定唯一查询或对象，请说清楚你现在想查什么。";
            case "FORBIDDEN" -> "助手只能查公开信息和当前账号自己的记录，管理查询请使用工作台。";
            case "INVALID_PLAN" -> "查询计划不符合能力协议，未执行。请重新提问。";
            case "OUT_OF_SCOPE" -> scopeGuard.refusalMessage();
            case "SERVICE_UNAVAILABLE" -> "语义服务暂不可用，未猜测备用查询。可以使用“我的借阅记录”“馆藏总览”或“查《书名》”等标准命令。";
            case "STALE_OR_UNAVAILABLE" -> "本次计划已失效或确认服务繁忙，请重新提交。";
            default -> "";
        }); return r;
    }
}

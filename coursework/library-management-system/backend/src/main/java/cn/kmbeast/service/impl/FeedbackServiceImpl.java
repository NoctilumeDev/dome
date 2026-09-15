package cn.kmbeast.service.impl;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.mapper.FeedbackMapper;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.PageResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.FeedbackQueryDto;
import cn.kmbeast.pojo.entity.Feedback;
import cn.kmbeast.pojo.vo.FeedbackVO;
import cn.kmbeast.service.FeedbackService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class FeedbackServiceImpl implements FeedbackService {
    @Resource
    private FeedbackMapper feedbackMapper;

    @Override
    public Result<Void> submit(Feedback feedback) {
        if (feedback == null || feedback.getContent() == null || feedback.getContent().trim().isEmpty()) {
            return ApiResult.error("反馈内容不能为空");
        }
        String content = feedback.getContent().trim();
        if (content.length() > 500) {
            return ApiResult.error("反馈内容不能超过500个字符");
        }
        Feedback record = Feedback.builder()
                .userId(LocalThreadHolder.getUserId())
                .content(content)
                .status(0)
                .createTime(LocalDateTime.now())
                .build();
        feedbackMapper.insert(record);
        return ApiResult.success("反馈提交成功");
    }

    @Override
    public Result<List<FeedbackVO>> query(FeedbackQueryDto dto) {
        if (!Integer.valueOf(1).equals(LocalThreadHolder.getRoleId())) {
            return ApiResult.error("仅管理员可以查询全部反馈");
        }
        FeedbackQueryDto query = dto == null ? new FeedbackQueryDto() : dto;
        return PageResult.success(feedbackMapper.query(query), feedbackMapper.queryCount(query));
    }

    @Override
    public Result<List<FeedbackVO>> queryMine(FeedbackQueryDto dto) {
        FeedbackQueryDto query = dto == null ? new FeedbackQueryDto() : dto;
        query.setUserId(LocalThreadHolder.getUserId());
        return PageResult.success(feedbackMapper.query(query), feedbackMapper.queryCount(query));
    }

    @Override
    public Result<Void> reply(Feedback feedback) {
        if (!Integer.valueOf(1).equals(LocalThreadHolder.getRoleId())) {
            return ApiResult.error("仅管理员可以回复反馈");
        }
        if (feedback == null || feedback.getId() == null) {
            return ApiResult.error("反馈记录不存在");
        }
        if (feedback.getReply() == null || feedback.getReply().trim().isEmpty()) {
            return ApiResult.error("回复内容不能为空");
        }
        String reply = feedback.getReply().trim();
        if (reply.length() > 500) {
            return ApiResult.error("回复内容不能超过500个字符");
        }
        feedback.setReply(reply);
        feedback.setStatus(1);
        feedback.setReplyTime(LocalDateTime.now());
        return feedbackMapper.reply(feedback) == 1
                ? ApiResult.success("反馈回复成功")
                : ApiResult.error("反馈记录不存在");
    }

    @Override
    public Result<Void> delete(Integer id) {
        if (!Integer.valueOf(1).equals(LocalThreadHolder.getRoleId())) {
            return ApiResult.error("仅管理员可以删除反馈");
        }
        if (id == null || feedbackMapper.deleteById(id) == 0) {
            return ApiResult.error("反馈记录不存在");
        }
        return ApiResult.success("反馈删除成功");
    }
}

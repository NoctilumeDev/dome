package cn.kmbeast.service;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.FeedbackQueryDto;
import cn.kmbeast.pojo.entity.Feedback;
import cn.kmbeast.pojo.vo.FeedbackVO;

import java.util.List;

public interface FeedbackService {
    Result<Void> submit(Feedback feedback);
    Result<List<FeedbackVO>> query(FeedbackQueryDto dto);
    Result<List<FeedbackVO>> queryMine(FeedbackQueryDto dto);
    Result<Void> reply(Feedback feedback);
    Result<Void> delete(Integer id);
}

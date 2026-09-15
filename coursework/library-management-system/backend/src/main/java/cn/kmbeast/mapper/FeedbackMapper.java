package cn.kmbeast.mapper;

import cn.kmbeast.pojo.dto.query.extend.FeedbackQueryDto;
import cn.kmbeast.pojo.entity.Feedback;
import cn.kmbeast.pojo.vo.FeedbackVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface FeedbackMapper {
    void insert(Feedback feedback);
    List<FeedbackVO> query(FeedbackQueryDto dto);
    Integer queryCount(FeedbackQueryDto dto);
    int reply(Feedback feedback);
    int deleteById(@Param("id") Integer id);
}

package cn.kmbeast.pojo.dto.query.extend;

import cn.kmbeast.pojo.dto.query.base.QueryDto;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class FeedbackQueryDto extends QueryDto {
    private Integer userId;
    private String userName;
    private String keyword;
    private Integer status;
}

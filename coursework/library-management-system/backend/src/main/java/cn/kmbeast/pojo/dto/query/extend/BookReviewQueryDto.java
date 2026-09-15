package cn.kmbeast.pojo.dto.query.extend;

import cn.kmbeast.pojo.dto.query.base.QueryDto;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class BookReviewQueryDto extends QueryDto {
    private Integer userId;
    private Integer bookId;
    private Integer rating;
    private String userName;
    private String bookName;
    private String keyword;
}

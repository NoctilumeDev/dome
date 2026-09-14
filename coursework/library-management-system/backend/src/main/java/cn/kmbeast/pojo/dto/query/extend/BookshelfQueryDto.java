package cn.kmbeast.pojo.dto.query.extend;

import cn.kmbeast.pojo.dto.query.base.QueryDto;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 书架查询DTO
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class BookshelfQueryDto extends QueryDto {
    /**
     * 书架名称
     */
    private String name;
}

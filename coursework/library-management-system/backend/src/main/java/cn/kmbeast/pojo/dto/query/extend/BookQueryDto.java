package cn.kmbeast.pojo.dto.query.extend;

import cn.kmbeast.pojo.dto.query.base.QueryDto;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 图书查询DTO
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class BookQueryDto extends QueryDto {
    /**
     * 图书名称
     */
    private String name;
    /**
     * 作者
     */
    private String author;
    /**
     * 分类
     */
    private String category;
}

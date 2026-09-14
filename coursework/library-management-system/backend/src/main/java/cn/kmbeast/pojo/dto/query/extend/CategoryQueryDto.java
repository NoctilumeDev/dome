package cn.kmbeast.pojo.dto.query.extend;

import cn.kmbeast.pojo.dto.query.base.QueryDto;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 分类查询DTO
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class CategoryQueryDto extends QueryDto {
    /**
     * 分类名称
     */
    private String name;
}
package cn.kmbeast.pojo.dto.query.base;

import lombok.*;

import java.time.LocalDateTime;

/**
 * 查询参数接收实体类基类，含有四项基础参数，使用时可以拓展
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@ToString
@Builder
public class QueryDto {
    /**
     * 当前页
     */
    private Integer current;
    /**
     * 页面数据大小
     */
    private Integer size;
    /**
     * 开始时间
     */
    private LocalDateTime startTime;
    /**
     * 结束时间
     */
    private LocalDateTime endTime;

    /**
     * SQL 分页偏移量：前端传的是页码(1开始)，SQL 需要的是偏移量
     * current=1 → offset=0, current=2 → offset=size
     */
    public Integer getOffset() {
        if (current == null || current <= 1) {
            return 0;
        }
        int pageSize = (size == null || size <= 0) ? 10 : size;
        return (current - 1) * pageSize;
    }
}


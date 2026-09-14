package cn.kmbeast.pojo.entity;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 借阅记录实体
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class BorrowRecord {
    /**
     * 记录ID
     */
    private Integer id;
    /**
     * 用户ID
     */
    private Integer userId;
    /**
     * 图书ID
     */
    private Integer bookId;
    /**
     * 借阅时间
     */
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime borrowTime;
    /**
     * 应还日期
     */
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime dueDate;
    /**
     * 归还时间
     */
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime returnTime;
    /**
     * 借阅状态：false=借阅中，true=已归还
     */
    private Boolean status;
    /**
     * 逾期罚款金额（元），归还时计算
     */
    private BigDecimal fineAmount;
}

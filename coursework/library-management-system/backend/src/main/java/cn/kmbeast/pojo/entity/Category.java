package cn.kmbeast.pojo.entity;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 图书分类实体
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class Category {
    /**
     * 分类ID
     */
    private Integer id;
    /**
     * 分类名称
     */
    private String name;
    /**
     * 创建时间
     */
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
}
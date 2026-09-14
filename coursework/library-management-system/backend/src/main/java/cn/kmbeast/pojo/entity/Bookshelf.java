package cn.kmbeast.pojo.entity;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 书架实体
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class Bookshelf {
    /**
     * 书架ID
     */
    private Integer id;
    /**
     * 书架名称
     */
    private String name;
    /**
     * 所在位置
     */
    private String location;
    /**
     * 容量
     */
    private Integer capacity;
    /**
     * 备注
     */
    private String description;
    /**
     * 创建时间
     */
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
}

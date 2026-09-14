package cn.kmbeast.pojo.entity;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;
import java.time.LocalDateTime;

/**
 * 图书实体
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class Book {

    private Integer id;

    @NotBlank(message = "图书名称不能为空")
    private String name;

    @NotBlank(message = "作者不能为空")
    private String author;

    @Pattern(regexp = "^$|^\\d{13}$|^\\d{10}$", message = "ISBN格式不正确")
    private String isbn;

    private String publisher;

    private String category;

    private Integer bookshelfId;

    private String bookshelfName;

    private String location;

    private Integer totalCount;

    private Integer availableCount;

    private String cover;

    private String description;

    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
}

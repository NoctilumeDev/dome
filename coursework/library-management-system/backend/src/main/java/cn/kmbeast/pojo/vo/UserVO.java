package cn.kmbeast.pojo.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 用户VO
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserVO {

    private Integer id;

    private String userAccount;

    private String userName;

    private String userAvatar;

    private Integer userRole;

    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
}

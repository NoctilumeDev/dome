package cn.kmbeast.pojo.dto.update;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.Email;
import javax.validation.constraints.Size;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserUpdateDTO {
    /**
     * 用户账号
     */
    private String userAccount;

    /**
     * 用户昵称
     */
    @Size(min = 2, max = 20, message = "用户名长度2-20个字符")
    private String userName;

    /**
     * 用户密码（修改密码时使用）
     */
    private String userPwd;

    /**
     * 用户头像
     */
    private String userAvatar;

    /**
     * 用户邮箱
     */
    @Email(message = "邮箱格式不正确")
    private String userEmail;
}
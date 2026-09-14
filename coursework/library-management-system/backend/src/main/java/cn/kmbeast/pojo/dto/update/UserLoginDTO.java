package cn.kmbeast.pojo.dto.update;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.NotBlank;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserLoginDTO {
    /**
     * 账号
     */
    @NotBlank(message = "账号不能为空")
    private String userAccount;

    /**
     * 密码
     */
    @NotBlank(message = "密码不能为空")
    private String userPwd;
}
package cn.kmbeast.pojo.dto.query.extend;

import cn.kmbeast.pojo.dto.query.base.QueryDto;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 用户查询DTO参数
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class UserQueryDto extends QueryDto {

    private String userAccount;

    private String userName;

    private Boolean isLogin;
}

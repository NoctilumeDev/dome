package cn.kmbeast.pojo.em;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 用户角色枚举（5级权限）
 */
@Getter
@AllArgsConstructor
public enum RoleEnum {

    SUPER_ADMIN(0, "超级管理员"),
    ADMIN(1, "管理员"),
    READER(2, "读者"),
    ACQUISITIONS(3, "采购员"),
    LOGISTICS(4, "物流员");

    /**
     * 角色编码
     */
    private final Integer role;
    /**
     * 角色名
     */
    private final String name;

    /**
     * 由角色编码获取角色名
     *
     * @param role 角色编码
     * @return String 角色名
     */
    public static String ROLE(Integer role) {
        for (RoleEnum value : RoleEnum.values()) {
            if (value.getRole().equals(role)) {
                return value.name;
            }
        }
        return null;
    }

    /**
     * 由角色名获取角色编码
     */
    public static Integer getRoleByName(String name) {
        for (RoleEnum value : RoleEnum.values()) {
            if (value.getName().equals(name)) {
                return value.getRole();
            }
        }
        return null;
    }
}
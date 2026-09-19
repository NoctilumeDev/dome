package cn.kmbeast.pojo.api;

/**
 * 请求响应码
 */
public enum ResultCode {
    /**
     * 请求成功码
     */
    REQUEST_SUCCESS(200),
    /**
     * 未提供有效登录凭据
     */
    AUTHENTICATION_REQUIRED(401),
    /**
     * 已认证但无权执行当前操作
     */
    ACCESS_DENIED(403),
    /**
     * 请求失败码
     */
    REQUEST_ERROR(400);

    private Integer code;

    @Override
    public String toString() {
        return "ResultCode{" +
                "code=" + code +
                '}';
    }

    public Integer getCode() {
        return code;
    }

    public void setCode(Integer code) {
        this.code = code;
    }

    ResultCode(Integer code) {
        this.code = code;
    }
}

package cn.kmbeast.Interceptor;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.api.ResultCode;
import cn.kmbeast.utils.JwtUtil;
import com.alibaba.fastjson2.JSONObject;
import io.jsonwebtoken.Claims;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.Writer;
import java.util.Arrays;
import java.util.List;

/**
 * token拦截器，做请求拦截
 * <p>
 * 职责：
 * 1. 放行白名单（登录/注册/文件读取）
 * 2. 校验 JWT token，解析用户身份写入 ThreadLocal
 * 3. 管理接口必须管理员角色（0=超级管理员, 1=管理员），读者(2)调用直接拒绝
 */
public class JwtInterceptor implements HandlerInterceptor {

    private final String apiPrefix;

    private static final AntPathMatcher PATH_MATCHER = new AntPathMatcher();

    /**
     * 仅管理员可访问的接口（写操作/敏感操作）
     */
    private static final List<String> ADMIN_ONLY_PATHS = Arrays.asList(
            // 用户管理
            "/user/query", "/user/batchDelete", "/user/backUpdate", "/user/freeze/**", "/user/unfreeze/**", "/user/insert", "/user/daysQuery/**",
            // 图书管理
            "/book/save", "/book/update", "/book/batchDelete",
            // 分类管理
            "/category/save", "/category/update", "/category/batchDelete",
            // 书架管理
            "/bookshelf/save", "/bookshelf/update", "/bookshelf/batchDelete"
    );

    public JwtInterceptor(String apiPrefix) {
        this.apiPrefix = apiPrefix;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String requestMethod = request.getMethod();
        // 放行预检请求
        if ("OPTIONS".equals(requestMethod)) {
            return true;
        }
        String requestURI = request.getRequestURI();
        // 白名单路径（不需要登录）
        if (requestURI.startsWith(apiPrefix + "/user/login")
                || requestURI.startsWith(apiPrefix + "/user/register")
                || requestURI.startsWith(apiPrefix + "/file/upload")
                || requestURI.startsWith(apiPrefix + "/file/video/upload")
                || requestURI.startsWith(apiPrefix + "/file/getFile")
                || requestURI.startsWith(apiPrefix + "/error")) {
            return true;
        }
        String token = request.getHeader("token");
        Claims claims = JwtUtil.fromToken(token);
        if (claims == null) {
            return reject(
                    response,
                    HttpServletResponse.SC_UNAUTHORIZED,
                    ResultCode.AUTHENTICATION_REQUIRED,
                    "身份认证异常，请先登录"
            );
        }
        Integer userId = claims.get("id", Integer.class);
        Integer roleId = claims.get("role", Integer.class);
        if (userId == null || roleId == null) {
            return reject(
                    response,
                    HttpServletResponse.SC_UNAUTHORIZED,
                    ResultCode.AUTHENTICATION_REQUIRED,
                    "身份认证异常，请先登录"
            );
        }
        // 管理接口角色校验：管理员(0/1)可访问，读者(2+)拒绝
        if (isAdminOnlyPath(requestURI) && roleId > 1) {
            return reject(
                    response,
                    HttpServletResponse.SC_FORBIDDEN,
                    ResultCode.ACCESS_DENIED,
                    "无权限操作，该接口仅管理员可用"
            );
        }
        LocalThreadHolder.setUserId(userId, roleId);
        return true;
    }

    /**
     * 判断当前请求路径是否为仅管理员可访问的接口
     */
    private boolean isAdminOnlyPath(String requestURI) {
        for (String path : ADMIN_ONLY_PATHS) {
            if (PATH_MATCHER.match(apiPrefix + path, requestURI)) {
                return true;
            }
        }
        return false;
    }

    private boolean reject(
            HttpServletResponse response,
            int httpStatus,
            ResultCode resultCode,
            String msg
    ) throws Exception {
        Result<String> error = ApiResult.error(resultCode, msg);
        response.setContentType("application/json;charset=UTF-8");
        response.setStatus(httpStatus);
        Writer stream = response.getWriter();
        stream.write(JSONObject.toJSONString(error));
        stream.flush();
        stream.close();
        return false;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        LocalThreadHolder.clear();
    }
}

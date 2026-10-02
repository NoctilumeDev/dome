package cn.kmbeast.Interceptor;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.mapper.UserMapper;
import cn.kmbeast.pojo.entity.User;
import cn.kmbeast.pojo.em.RoleEnum;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.api.ResultCode;
import cn.kmbeast.utils.JwtUtil;
import com.alibaba.fastjson2.JSONObject;
import io.jsonwebtoken.Claims;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.HandlerMapping;

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

    private final UserMapper userMapper;

    private static final AntPathMatcher PATH_MATCHER = new AntPathMatcher();
    private static final List<String> PUBLIC_PATHS = Arrays.asList(
            "/user/login", "/user/register", "/file/upload", "/file/video/upload", "/file/getFile", "/error"
    );

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

    public JwtInterceptor(String apiPrefix, UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        LocalThreadHolder.clear();
        String requestMethod = request.getMethod();
        // 放行预检请求
        if ("OPTIONS".equals(requestMethod)) {
            return true;
        }
        // 使用 Spring 已解析的实际接口映射，与路由共享矩阵参数、编码与尾斜杠语义。
        Object mapping = request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        String route = mapping instanceof String ? (String) mapping : null;
        if (route != null && route.length() > 1 && route.endsWith("/")) {
            route = route.substring(0, route.length() - 1);
        }
        if (PUBLIC_PATHS.contains(route)) {
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
        Integer userId;
        try {
            userId = claims.get("id", Integer.class);
            if (claims.get("role", Integer.class) == null) throw new IllegalArgumentException("角色字段缺失");
        } catch (RuntimeException exception) {
            return reject(response, HttpServletResponse.SC_UNAUTHORIZED,
                    ResultCode.AUTHENTICATION_REQUIRED, "身份认证异常，请先登录");
        }
        User current = userId == null ? null : userMapper.getByActive(User.builder().id(userId).build());
        if (current == null || !Boolean.FALSE.equals(current.getIsLogin())
                || current.getUserRole() == null || RoleEnum.ROLE(current.getUserRole()) == null) {
            return reject(
                    response,
                    HttpServletResponse.SC_UNAUTHORIZED,
                    ResultCode.AUTHENTICATION_REQUIRED,
                    "账号不存在或已被禁用，请重新登录"
            );
        }
        Integer roleId = current.getUserRole();
        if (route == null) {
            return reject(response, HttpServletResponse.SC_FORBIDDEN,
                    ResultCode.ACCESS_DENIED, "无法确认接口权限");
        }
        // 管理接口角色校验：管理员(0/1)可访问，读者(2+)拒绝
        if (isAdminOnlyPath(route) && roleId > 1) {
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
    private boolean isAdminOnlyPath(String route) {
        for (String path : ADMIN_ONLY_PATHS) {
            if (PATH_MATCHER.match(path, route)) {
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

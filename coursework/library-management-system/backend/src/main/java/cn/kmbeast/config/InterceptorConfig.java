package cn.kmbeast.config;

import cn.kmbeast.Interceptor.JwtInterceptor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * API拦截器配置
 * <p>
 * 关键：拦截器只拦截 API 路径（apiPrefix + /**），
 * 静态资源（index.html/js/css 等前端页面）不能被 JWT 拦截，
 * 否则浏览器打开首页会被拦成 403，整个前端无法使用。
 */
@Configuration
public class InterceptorConfig implements WebMvcConfigurer {

    @Value("${my-server.api-context-path}")
    private String API;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // JWT Token 拦截器：只拦截后端 API，静态资源放行
        // 注意：MappedInterceptor 用 lookupPath(不含 context-path)匹配路径，
        // 因此 pattern 必须用相对路径 "/**"，而不能用 apiPrefix + "/**"
        registry.addInterceptor(new JwtInterceptor(API))
                .addPathPatterns("/**")
                .excludePathPatterns(
                        "/user/login",
                        "/user/register",
                        "/file/upload",
                        "/file/video/upload",
                        "/file/getFile",
                        "/error",
                        "/",
                        "/index.html",
                        "/logo.png",
                        "/favicon.ico",
                        "/css/**",
                        "/js/**",
                        "/fonts/**",
                        "/img/**"
                );
    }
}

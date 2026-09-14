package cn.kmbeast.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtBuilder;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;

/**
 * jwt token 工具类 (jjwt 0.11.5)
 *
 * @author 【B站：程序员晨星】
 */
@Component
public class JwtUtil {
    private static String secret;
    private static Long expiration;

    @Value("${jwt.secret}")
    public void setSecret(String val) {
        secret = val;
    }

    @Value("${jwt.expiration}")
    public void setExpiration(Long val) {
        expiration = val;
    }

    private static SecretKey getKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * 生成 token
     *
     * @param id   用户ID
     * @param role 用户角色
     * @return String
     */
    public static String toToken(Integer id, Integer role) {
        JwtBuilder jwtBuilder = Jwts.builder();
        return jwtBuilder.setHeaderParam("typ", "JWT")
                .setHeaderParam("alg", "HS256")
                .claim("id", id)
                .claim("role", role)
                .setSubject("用户认证")
                .setExpiration(new Date(System.currentTimeMillis() + expiration))
                .setId(UUID.randomUUID().toString())
                .signWith(getKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    /**
     * 解密TOKEN
     *
     * @param token token信息
     */
    public static Claims fromToken(String token) {
        JwtParser jwtParser = Jwts.parserBuilder().setSigningKey(getKey()).build();
        try {
            return jwtParser.parseClaimsJws(token).getBody();
        } catch (Exception e) {
            return null;
        }
    }
}
package com.dorm.demo.web;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.http.converter.HttpMessageNotReadableException;

import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

  @ExceptionHandler(RuntimeException.class)
  public ResponseEntity<?> handleRuntime(RuntimeException e) {
    String msg = e.getMessage() == null ? "操作失败" : e.getMessage();
    HttpStatus status = HttpStatus.BAD_REQUEST;

    if ("未登录".equals(msg)) {
      status = HttpStatus.UNAUTHORIZED;
    } else if ("权限不足".equals(msg)) {
      status = HttpStatus.FORBIDDEN;
    }

    return ResponseEntity.status(status).body(Map.of("message", msg));
  }

  @ExceptionHandler(HttpMessageNotReadableException.class)
  public ResponseEntity<?> handleHttpMessageNotReadable(HttpMessageNotReadableException e) {
    return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "请求参数格式错误"));
  }

  @ExceptionHandler(MethodArgumentTypeMismatchException.class)
  public ResponseEntity<?> handleMethodArgumentTypeMismatch(MethodArgumentTypeMismatchException e) {
    return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "请求参数类型错误"));
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<?> handleUnknown(Exception e) {
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "服务端异常"));
  }
}

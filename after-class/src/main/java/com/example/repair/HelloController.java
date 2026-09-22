package com.example.repair;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController // 给 Spring 留个记号，不然它不知道这里能回话
public class HelloController {

    @GetMapping("/hello") // 还得写清楚地址，Spring 才知道 /hello 该找谁
    public String hello() {
        return "你好"; // 把这句话交给 Spring，再送回浏览器
    }
}

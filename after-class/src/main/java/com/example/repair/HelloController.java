package com.example.repair;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController // 给 Spring 留个记号，不然它不知道这里能回话
public class HelloController {

    @GetMapping("/hello") // 还得写清楚：找 /hello 的该去哪里
    public String hello(@RequestParam("name") String name) { // 浏览器带来的 name，要有地方接住
        return "你好，" + name; // 把名字接到问候后面，再交给浏览器
    }
}

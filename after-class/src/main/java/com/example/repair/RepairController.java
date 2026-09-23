package com.example.repair;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController // Spring 得先知道，这里也能回话
public class RepairController {

    @GetMapping("/repair") // 找 /repair 的，交给下面这段
    public Repair repair() {
        Repair repair = new Repair(); // 先拿一张空的报修单
        repair.setRoom("3-412"); // 填上宿舍号
        repair.setContent("水龙头漏水"); // 填上坏了什么
        return repair; // 这次交出去的是整张报修单
    }
}

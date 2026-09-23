package com.example.repair;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController // Spring 得先知道，这里也能回话
public class RepairController {

    @GetMapping("/repair") // 找 /repair 的，交给下面这段
    public Repair repair(
            @RequestParam("room") String room,
            @RequestParam("content") String content) {
        Repair repair = new Repair(); // 先拿一张空的报修单
        repair.setRoom(room); // 把浏览器带来的宿舍号填进去
        repair.setContent(content); // 再填上报修内容
        return repair; // 整张报修单交回去
    }
}

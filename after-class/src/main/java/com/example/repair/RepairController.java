package com.example.repair;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController // Spring 得先知道，这里也能回话
public class RepairController {

    private final RepairMapper repairMapper; // 去 MySQL 找报修要用它

    public RepairController(RepairMapper repairMapper) {
        this.repairMapper = repairMapper; // Spring 创建 Controller 时，把 Mapper 放进来
    }

    @GetMapping("/repair") // 找 /repair 的，交给下面这段
    public Repair repair(@RequestParam("id") Long id) {
        return repairMapper.findById(id); // 拿编号去 MySQL 找，再交给浏览器
    }
}

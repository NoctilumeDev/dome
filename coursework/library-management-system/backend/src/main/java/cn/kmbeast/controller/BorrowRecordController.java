package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BorrowRecordQueryDto;
import cn.kmbeast.pojo.vo.BorrowRecordVO;
import cn.kmbeast.service.BorrowRecordService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

/**
 * 借阅记录控制器
 */
@RestController
@RequestMapping("/borrowRecord")
public class BorrowRecordController {

    @Resource
    private BorrowRecordService borrowRecordService;

    @PostMapping("/borrow/{bookId}")
    public Result<Void> borrow(@PathVariable Integer bookId) {
        return borrowRecordService.borrow(bookId);
    }

    @PostMapping("/return/{recordId}")
    public Result<Void> returnBook(@PathVariable Integer recordId) {
        return borrowRecordService.returnBook(recordId);
    }

    @PostMapping("/query")
    public Result<List<BorrowRecordVO>> query(@RequestBody BorrowRecordQueryDto dto) {
        return borrowRecordService.query(dto);
    }
}

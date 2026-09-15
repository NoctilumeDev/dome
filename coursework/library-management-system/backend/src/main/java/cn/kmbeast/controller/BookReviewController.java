package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookReviewQueryDto;
import cn.kmbeast.pojo.entity.BookReview;
import cn.kmbeast.pojo.vo.BookReviewVO;
import cn.kmbeast.service.BookReviewService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

@RestController
@RequestMapping("/review")
public class BookReviewController {
    @Resource private BookReviewService bookReviewService;

    @PostMapping("/submit")
    public Result<Void> submit(@RequestBody BookReview review) { return bookReviewService.submit(review); }
    @PutMapping
    public Result<Void> update(@RequestBody BookReview review) { return bookReviewService.update(review); }
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Integer id) { return bookReviewService.delete(id); }
    @PostMapping("/query")
    public Result<List<BookReviewVO>> query(@RequestBody BookReviewQueryDto dto) { return bookReviewService.query(dto); }
    @PostMapping("/mine")
    public Result<List<BookReviewVO>> queryMine(@RequestBody BookReviewQueryDto dto) { return bookReviewService.queryMine(dto); }
}

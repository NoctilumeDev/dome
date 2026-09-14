package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookshelfQueryDto;
import cn.kmbeast.pojo.entity.Bookshelf;
import cn.kmbeast.service.BookshelfService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;

/**
 * 书架控制器
 */
@RestController
@RequestMapping("/bookshelf")
public class BookshelfController {

    @Resource
    private BookshelfService bookshelfService;

    @PostMapping("/save")
    public Result<Void> save(@Valid @RequestBody Bookshelf bookshelf) {
        return bookshelfService.save(bookshelf);
    }

    @PutMapping("/update")
    public Result<Void> update(@Valid @RequestBody Bookshelf bookshelf) {
        return bookshelfService.update(bookshelf);
    }

    @PostMapping("/batchDelete")
    public Result<Void> batchDelete(@RequestBody List<Integer> ids) {
        return bookshelfService.batchDelete(ids);
    }

    @PostMapping("/query")
    public Result<List<Bookshelf>> query(@RequestBody BookshelfQueryDto dto) {
        return bookshelfService.query(dto);
    }

    @GetMapping("/queryAll")
    public Result<List<Bookshelf>> queryAll() {
        return bookshelfService.queryAll();
    }
}

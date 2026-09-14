package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookAssistantQueryDto;
import cn.kmbeast.pojo.dto.query.extend.BookQueryDto;
import cn.kmbeast.pojo.entity.Book;
import cn.kmbeast.pojo.vo.ChartVO;
import cn.kmbeast.pojo.vo.BookAssistantVO;
import cn.kmbeast.service.BookService;
import cn.kmbeast.service.BookAssistantService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;

/**
 * 图书控制器
 */
@RestController
@RequestMapping("/book")
public class BookController {

    @Resource
    private BookService bookService;
    @Resource
    private BookAssistantService bookAssistantService;

    @PostMapping("/save")
    @ResponseBody
    public Result<Void> save(@Valid @RequestBody Book book) {
        return bookService.save(book);
    }

    @PutMapping("/update")
    @ResponseBody
    public Result<Void> update(@Valid @RequestBody Book book) {
        return bookService.update(book);
    }

    @PostMapping("/batchDelete")
    @ResponseBody
    public Result<Void> batchDelete(@RequestBody List<Integer> ids) {
        return bookService.batchDelete(ids);
    }

    @PostMapping("/query")
    @ResponseBody
    public Result<List<Book>> query(@RequestBody BookQueryDto dto) {
        return bookService.query(dto);
    }

    @PostMapping("/assistant/query")
    @ResponseBody
    public Result<BookAssistantVO> askBookByQuestion(@RequestBody BookAssistantQueryDto dto) {
        return bookAssistantService.ask(dto);
    }

    @GetMapping("/daysQuery/{day}")
    @ResponseBody
    public Result<List<ChartVO>> daysQuery(@PathVariable Integer day) {
        return bookService.daysQuery(day);
    }
}

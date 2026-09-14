package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.CategoryQueryDto;
import cn.kmbeast.pojo.entity.Category;
import cn.kmbeast.service.CategoryService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;

/**
 * 分类控制器
 */
@RestController
@RequestMapping("/category")
public class CategoryController {

    @Resource
    private CategoryService categoryService;

    @PostMapping("/save")
    public Result<Void> save(@Valid @RequestBody Category category) {
        return categoryService.save(category);
    }

    @PutMapping("/update")
    public Result<Void> update(@Valid @RequestBody Category category) {
        return categoryService.update(category);
    }

    @PostMapping("/batchDelete")
    public Result<Void> batchDelete(@RequestBody List<Integer> ids) {
        return categoryService.batchDelete(ids);
    }

    @PostMapping("/query")
    public Result<List<Category>> query(@RequestBody CategoryQueryDto dto) {
        return categoryService.query(dto);
    }

    @GetMapping("/queryAll")
    public Result<List<Category>> queryAll() {
        return categoryService.queryAll();
    }
}

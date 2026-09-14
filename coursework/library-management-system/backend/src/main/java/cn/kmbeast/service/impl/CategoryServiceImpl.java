package cn.kmbeast.service.impl;

import cn.kmbeast.mapper.CategoryMapper;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.PageResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.CategoryQueryDto;
import cn.kmbeast.pojo.entity.Category;
import cn.kmbeast.service.CategoryService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 分类服务实现
 */
@Service
public class CategoryServiceImpl implements CategoryService {

    @Resource
    private CategoryMapper categoryMapper;

    @Override
    public Result<Void> save(Category category) {
        category.setCreateTime(LocalDateTime.now());
        categoryMapper.insert(category);
        return ApiResult.success("新增分类成功");
    }

    @Override
    public Result<Void> update(Category category) {
        categoryMapper.update(category);
        return ApiResult.success("修改分类成功");
    }

    @Override
    public Result<Void> batchDelete(List<Integer> ids) {
        categoryMapper.batchDelete(ids);
        return ApiResult.success("删除分类成功");
    }

    @Override
    public Result<List<Category>> query(CategoryQueryDto dto) {
        List<Category> list = categoryMapper.query(dto);
        Integer total = categoryMapper.queryCount(dto);
        return PageResult.success(list, total);
    }

    @Override
    public Result<List<Category>> queryAll() {
        List<Category> list = categoryMapper.queryAll();
        return ApiResult.success(list);
    }
}
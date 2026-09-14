package cn.kmbeast.service;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.CategoryQueryDto;
import cn.kmbeast.pojo.entity.Category;

import java.util.List;

/**
 * 分类服务接口
 */
public interface CategoryService {

    Result<Void> save(Category category);

    Result<Void> update(Category category);

    Result<Void> batchDelete(List<Integer> ids);

    Result<List<Category>> query(CategoryQueryDto dto);

    Result<List<Category>> queryAll();
}
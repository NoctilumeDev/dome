package cn.kmbeast.mapper;

import cn.kmbeast.pojo.dto.query.extend.CategoryQueryDto;
import cn.kmbeast.pojo.entity.Category;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 分类持久化接口
 */
@Mapper
public interface CategoryMapper {

    void insert(Category category);

    void update(Category category);

    void batchDelete(@Param("ids") List<Integer> ids);

    List<Category> query(CategoryQueryDto dto);

    Integer queryCount(CategoryQueryDto dto);

    Category getById(Integer id);

    List<Category> queryAll();
}
package cn.kmbeast.mapper;

import cn.kmbeast.pojo.dto.query.extend.BookshelfQueryDto;
import cn.kmbeast.pojo.entity.Bookshelf;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 书架持久化接口
 */
@Mapper
public interface BookshelfMapper {

    void insert(Bookshelf bookshelf);

    void update(Bookshelf bookshelf);

    void batchDelete(@Param("ids") List<Integer> ids);

    List<Bookshelf> query(BookshelfQueryDto dto);

    Integer queryCount(BookshelfQueryDto dto);

    Bookshelf getById(Integer id);

    List<Bookshelf> queryAll();
}

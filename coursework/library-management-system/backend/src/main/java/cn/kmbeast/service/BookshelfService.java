package cn.kmbeast.service;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookshelfQueryDto;
import cn.kmbeast.pojo.entity.Bookshelf;

import java.util.List;

/**
 * 书架服务接口
 */
public interface BookshelfService {

    Result<Void> save(Bookshelf bookshelf);

    Result<Void> update(Bookshelf bookshelf);

    Result<Void> batchDelete(List<Integer> ids);

    Result<List<Bookshelf>> query(BookshelfQueryDto dto);

    Result<List<Bookshelf>> queryAll();
}

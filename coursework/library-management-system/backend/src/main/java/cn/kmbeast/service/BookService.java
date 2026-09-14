package cn.kmbeast.service;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookQueryDto;
import cn.kmbeast.pojo.entity.Book;
import cn.kmbeast.pojo.vo.ChartVO;

import java.util.List;

/**
 * 图书服务接口
 */
public interface BookService {

    Result<Void> save(Book book);

    Result<Void> update(Book book);

    Result<Void> batchDelete(List<Integer> ids);

    Result<List<Book>> query(BookQueryDto dto);

    Result<List<ChartVO>> daysQuery(Integer day);
}

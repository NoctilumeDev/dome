package cn.kmbeast.service.impl;

import cn.kmbeast.mapper.BookshelfMapper;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.PageResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookshelfQueryDto;
import cn.kmbeast.pojo.entity.Bookshelf;
import cn.kmbeast.service.BookshelfService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 书架服务实现
 */
@Service
public class BookshelfServiceImpl implements BookshelfService {

    @Resource
    private BookshelfMapper bookshelfMapper;

    @Override
    public Result<Void> save(Bookshelf bookshelf) {
        bookshelf.setCreateTime(LocalDateTime.now());
        bookshelfMapper.insert(bookshelf);
        return ApiResult.success("新增书架成功");
    }

    @Override
    public Result<Void> update(Bookshelf bookshelf) {
        bookshelfMapper.update(bookshelf);
        return ApiResult.success("修改书架成功");
    }

    @Override
    public Result<Void> batchDelete(List<Integer> ids) {
        bookshelfMapper.batchDelete(ids);
        return ApiResult.success("删除书架成功");
    }

    @Override
    public Result<List<Bookshelf>> query(BookshelfQueryDto dto) {
        List<Bookshelf> list = bookshelfMapper.query(dto);
        Integer total = bookshelfMapper.queryCount(dto);
        return PageResult.success(list, total);
    }

    @Override
    public Result<List<Bookshelf>> queryAll() {
        List<Bookshelf> list = bookshelfMapper.queryAll();
        return ApiResult.success(list);
    }
}

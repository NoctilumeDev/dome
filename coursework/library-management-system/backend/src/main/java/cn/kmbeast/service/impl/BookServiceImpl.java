package cn.kmbeast.service.impl;

import cn.kmbeast.mapper.BookMapper;
import cn.kmbeast.mapper.BorrowRecordMapper;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.PageResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.base.QueryDto;
import cn.kmbeast.pojo.dto.query.extend.BookQueryDto;
import cn.kmbeast.pojo.entity.Book;
import cn.kmbeast.pojo.vo.ChartVO;
import cn.kmbeast.service.BookService;
import cn.kmbeast.utils.DateUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 图书业务逻辑实现
 */
@Slf4j
@Service
public class BookServiceImpl implements BookService {

    @Resource
    private BookMapper bookMapper;

    @Resource
    private BorrowRecordMapper borrowRecordMapper;

    @Override
    public Result<Void> save(Book book) {
        book.setCreateTime(LocalDateTime.now());
        book.setAvailableCount(book.getTotalCount());
        bookMapper.insert(book);
        return ApiResult.success();
    }

    @Override
    public Result<Void> update(Book book) {
        if (bookMapper.getById(book.getId()) == null) {
            return ApiResult.error("图书不存在");
        }
        bookMapper.update(book);
        return ApiResult.success();
    }

    @Override
    public Result<Void> batchDelete(List<Integer> ids) {
        // 有未归还借阅记录的图书不能删除，否则借阅记录会悬空
        int activeCount = borrowRecordMapper.countActiveByBookIds(ids);
        if (activeCount > 0) {
            return ApiResult.error("存在未归还的借阅记录，无法删除该图书");
        }
        bookMapper.batchDelete(ids);
        return ApiResult.success();
    }

    @Override
    public Result<List<Book>> query(BookQueryDto dto) {
        List<Book> bookList = bookMapper.query(dto);
        Integer totalCount = bookMapper.queryCount(dto);
        return PageResult.success(bookList, totalCount);
    }

    @Override
    public Result<List<ChartVO>> daysQuery(Integer day) {
        QueryDto queryDto = DateUtil.startAndEndTime(day);
        BookQueryDto bookQueryDto = new BookQueryDto();
        bookQueryDto.setStartTime(queryDto.getStartTime());
        bookQueryDto.setEndTime(queryDto.getEndTime());
        List<Book> bookList = bookMapper.query(bookQueryDto);
        List<LocalDateTime> localDateTimes = bookList.stream().map(Book::getCreateTime).collect(Collectors.toList());
        List<ChartVO> chartVOS = DateUtil.countDatesWithinRange(day, localDateTimes);
        return ApiResult.success(chartVOS);
    }
}

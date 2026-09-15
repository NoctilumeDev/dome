package cn.kmbeast.service.impl;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.mapper.BookMapper;
import cn.kmbeast.mapper.BookReviewMapper;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.PageResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookReviewQueryDto;
import cn.kmbeast.pojo.entity.BookReview;
import cn.kmbeast.pojo.vo.BookReviewVO;
import cn.kmbeast.service.BookReviewService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class BookReviewServiceImpl implements BookReviewService {
    @Resource private BookReviewMapper bookReviewMapper;
    @Resource private BookMapper bookMapper;

    @Override
    public Result<Void> submit(BookReview review) {
        String error = validate(review);
        if (error != null) return ApiResult.error(error);
        Integer userId = LocalThreadHolder.getUserId();
        if (bookMapper.getById(review.getBookId()) == null) return ApiResult.error("图书不存在");
        if (bookReviewMapper.getByUserAndBook(userId, review.getBookId()) != null) return ApiResult.error("你已经评价过这本书，可以修改原书评");
        review.setUserId(userId);
        review.setContent(review.getContent().trim());
        review.setCreateTime(LocalDateTime.now());
        review.setUpdateTime(LocalDateTime.now());
        bookReviewMapper.insert(review);
        return ApiResult.success("书评发布成功");
    }

    @Override
    public Result<Void> update(BookReview review) {
        String error = validate(review);
        if (error != null || review.getId() == null) return ApiResult.error(error == null ? "书评不存在" : error);
        BookReview stored = bookReviewMapper.getById(review.getId());
        if (stored == null) return ApiResult.error("书评不存在");
        boolean admin = Integer.valueOf(1).equals(LocalThreadHolder.getRoleId());
        if (!admin && !stored.getUserId().equals(LocalThreadHolder.getUserId())) return ApiResult.error("只能修改自己的书评");
        review.setContent(review.getContent().trim());
        review.setUpdateTime(LocalDateTime.now());
        bookReviewMapper.update(review);
        return ApiResult.success("书评修改成功");
    }

    @Override
    public Result<Void> delete(Integer id) {
        BookReview stored = bookReviewMapper.getById(id);
        if (stored == null) return ApiResult.error("书评不存在");
        boolean admin = Integer.valueOf(1).equals(LocalThreadHolder.getRoleId());
        if (!admin && !stored.getUserId().equals(LocalThreadHolder.getUserId())) return ApiResult.error("只能删除自己的书评");
        bookReviewMapper.deleteById(id);
        return ApiResult.success("书评删除成功");
    }

    @Override
    public Result<List<BookReviewVO>> query(BookReviewQueryDto dto) {
        BookReviewQueryDto query = dto == null ? new BookReviewQueryDto() : dto;
        return PageResult.success(bookReviewMapper.query(query), bookReviewMapper.queryCount(query));
    }

    @Override
    public Result<List<BookReviewVO>> queryMine(BookReviewQueryDto dto) {
        BookReviewQueryDto query = dto == null ? new BookReviewQueryDto() : dto;
        query.setUserId(LocalThreadHolder.getUserId());
        return PageResult.success(bookReviewMapper.query(query), bookReviewMapper.queryCount(query));
    }

    private String validate(BookReview review) {
        if (review == null || review.getBookId() == null) return "请选择图书";
        if (review.getRating() == null || review.getRating() < 1 || review.getRating() > 5) return "评分必须在1到5之间";
        if (review.getContent() == null || review.getContent().trim().isEmpty()) return "书评内容不能为空";
        return review.getContent().trim().length() > 500 ? "书评内容不能超过500个字符" : null;
    }
}

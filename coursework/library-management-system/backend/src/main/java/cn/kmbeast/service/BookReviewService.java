package cn.kmbeast.service;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookReviewQueryDto;
import cn.kmbeast.pojo.entity.BookReview;
import cn.kmbeast.pojo.vo.BookReviewVO;

import java.util.List;

public interface BookReviewService {
    Result<Void> submit(BookReview review);
    Result<Void> update(BookReview review);
    Result<Void> delete(Integer id);
    Result<List<BookReviewVO>> query(BookReviewQueryDto dto);
    Result<List<BookReviewVO>> queryMine(BookReviewQueryDto dto);
}

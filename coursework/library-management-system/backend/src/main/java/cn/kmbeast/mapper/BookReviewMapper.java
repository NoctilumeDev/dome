package cn.kmbeast.mapper;

import cn.kmbeast.pojo.dto.query.extend.BookReviewQueryDto;
import cn.kmbeast.pojo.entity.BookReview;
import cn.kmbeast.pojo.vo.BookReviewVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface BookReviewMapper {
    int insert(BookReview review);
    int update(BookReview review);
    int deleteById(@Param("id") Integer id);
    BookReview getById(@Param("id") Integer id);
    BookReview getByUserAndBook(@Param("userId") Integer userId, @Param("bookId") Integer bookId);
    List<BookReviewVO> query(BookReviewQueryDto dto);
    Integer queryCount(BookReviewQueryDto dto);
}

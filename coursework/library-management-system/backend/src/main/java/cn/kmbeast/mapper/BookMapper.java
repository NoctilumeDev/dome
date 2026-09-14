package cn.kmbeast.mapper;

import cn.kmbeast.pojo.dto.query.extend.BookQueryDto;
import cn.kmbeast.pojo.entity.Book;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

/**
 * 图书持久化接口
 */
@Mapper
public interface BookMapper {

    void insert(Book book);

    void update(Book book);

    void batchDelete(@Param(value = "ids") List<Integer> ids);

    List<Book> query(BookQueryDto dto);

    Integer queryCount(BookQueryDto dto);

    Book getById(Integer id);

    List<Book> queryLowStock(@Param("threshold") Integer threshold);

    List<Map<String, Object>> categoryStats();

    /**
     * 原子扣减可借数量（高并发防超借）：
     * 只有可借数量大于0时才扣减，返回受影响行数
     */
    int deductAvailableCount(@Param("id") Integer id);

    /**
     * 原子回补可借数量（归还时使用，不超过总数量防数据异常）
     */
    int increaseAvailableCount(@Param("id") Integer id);
}

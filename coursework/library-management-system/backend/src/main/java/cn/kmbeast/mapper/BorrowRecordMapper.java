package cn.kmbeast.mapper;

import cn.kmbeast.pojo.dto.query.extend.BorrowRecordQueryDto;
import cn.kmbeast.pojo.entity.BorrowRecord;
import cn.kmbeast.pojo.vo.BorrowRecordVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

/**
 * 借阅记录持久化接口
 */
@Mapper
public interface BorrowRecordMapper {

    void insert(BorrowRecord record);

    void update(BorrowRecord record);

    List<BorrowRecordVO> query(BorrowRecordQueryDto dto);

    Integer queryCount(BorrowRecordQueryDto dto);

    BorrowRecord getById(@Param("id") Integer id);

    List<BorrowRecord> getActiveByUserIdAndBookId(@Param("userId") Integer userId,
                                                   @Param("bookId") Integer bookId);

    int getActiveCountByUserId(@Param("userId") Integer userId);

    /**
     * 条件更新归还：只有状态为借阅中(0)时才允许归还，防止并发重复还书
     *
     * @return 受影响行数，0 表示记录不存在或已归还
     */
    int returnBook(BorrowRecord record);

    /**
     * 统计指定图书中处于借阅中(未归还)的记录数
     */
    int countActiveByBookIds(@Param("bookIds") List<Integer> bookIds);

    List<BorrowRecordVO> monthlyBorrowStats(@Param("year") Integer year,
                                            @Param("month") Integer month);

    List<Map<String, Object>> hotBookStats(@Param("limit") Integer limit);
}

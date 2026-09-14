package cn.kmbeast.service;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BorrowRecordQueryDto;
import cn.kmbeast.pojo.vo.BorrowRecordVO;

import java.util.List;

/**
 * 借阅记录服务接口
 */
public interface BorrowRecordService {

    /**
     * 借书
     *
     * @param bookId 图书ID
     * @return Result<Void>
     */
    Result<Void> borrow(Integer bookId);

    /**
     * 还书
     *
     * @param recordId 记录ID
     * @return Result<Void>
     */
    Result<Void> returnBook(Integer recordId);

    /**
     * 分页查询借阅记录
     *
     * @param dto 查询参数
     * @return Result<List<BorrowRecordVO>>
     */
    Result<List<BorrowRecordVO>> query(BorrowRecordQueryDto dto);
}

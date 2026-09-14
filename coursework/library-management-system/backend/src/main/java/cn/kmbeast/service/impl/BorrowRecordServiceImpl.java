package cn.kmbeast.service.impl;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.mapper.BookMapper;
import cn.kmbeast.mapper.BorrowRecordMapper;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.PageResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BorrowRecordQueryDto;
import cn.kmbeast.pojo.entity.Book;
import cn.kmbeast.pojo.entity.BorrowRecord;
import cn.kmbeast.pojo.vo.BorrowRecordVO;
import cn.kmbeast.service.BorrowRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;

/**
 * 借阅记录业务逻辑实现
 * <p>
 * 高并发安全设计（核心）：
 * 1. 借书：先原子扣减库存（UPDATE ... WHERE available_count > 0），扣减失败即库存不足，
 * 杜绝"先查后改"造成的并发超借；插入借阅记录失败时事务回滚，库存自动恢复。
 * 2. 还书：条件更新（WHERE status = 0）防止并发重复还书；库存回补同样走原子 SQL。
 * 3. 逾期罚款：归还时按逾期天数 × 单价计算，写入 fine_amount。
 */
@Slf4j
@Service
public class BorrowRecordServiceImpl implements BorrowRecordService {

    @Resource
    private BorrowRecordMapper borrowRecordMapper;

    @Resource
    private BookMapper bookMapper;

    @Value("${borrow.max-count:5}")
    private int maxBorrowCount;

    @Value("${borrow.fine-per-day:0.5}")
    private BigDecimal finePerDay;

    /**
     * 借书（事务：扣库存 + 插记录要么都成功，要么都回滚）
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Void> borrow(Integer bookId) {
        Integer userId = LocalThreadHolder.getUserId();
        // 1. 检查借阅数量限制
        int activeCount = borrowRecordMapper.getActiveCountByUserId(userId);
        if (activeCount >= maxBorrowCount) {
            return ApiResult.error("借阅数量已达上限（" + maxBorrowCount + "本），请先归还部分图书");
        }
        // 2. 检查是否已借阅该书（防重复借阅）
        List<BorrowRecord> activeRecords = borrowRecordMapper.getActiveByUserIdAndBookId(userId, bookId);
        if (activeRecords != null && !activeRecords.isEmpty()) {
            return ApiResult.error("您已借阅该图书，请勿重复借阅");
        }
        // 3. 图书是否存在
        Book book = bookMapper.getById(bookId);
        if (book == null) {
            return ApiResult.error("图书不存在");
        }
        // 4. 原子扣减库存：只有库存 > 0 才扣减成功（高并发下不会超借）
        int rows = bookMapper.deductAvailableCount(bookId);
        if (rows == 0) {
            return ApiResult.error("图书库存不足，无法借阅");
        }
        // 5. 插入借阅记录（失败抛异常 → 事务回滚，库存自动恢复）
        BorrowRecord record = BorrowRecord.builder()
                .userId(userId)
                .bookId(bookId)
                .borrowTime(LocalDateTime.now())
                .dueDate(LocalDateTime.now().plusDays(30))
                .status(false)
                .fineAmount(BigDecimal.ZERO)
                .build();
        borrowRecordMapper.insert(record);
        log.info("借阅成功: userId={}, bookId={}", userId, bookId);
        return ApiResult.success("借阅成功");
    }

    /**
     * 还书（事务：条件更新记录 + 原子回补库存）
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Void> returnBook(Integer recordId) {
        Integer userId = LocalThreadHolder.getUserId();
        // 1. 查询借阅记录
        BorrowRecord record = borrowRecordMapper.getById(recordId);
        if (record == null) {
            return ApiResult.error("借阅记录不存在");
        }
        if (!record.getUserId().equals(userId)) {
            return ApiResult.error("该借阅记录不属于当前用户，无法归还");
        }
        // 2. 计算逾期罚款（按时归还未逾期则为 0）
        LocalDateTime now = LocalDateTime.now();
        BigDecimal fine = BigDecimal.ZERO;
        if (record.getDueDate() != null && now.isAfter(record.getDueDate())) {
            long overdueDays = ChronoUnit.DAYS.between(record.getDueDate(), now);
            fine = BigDecimal.valueOf(overdueDays).multiply(finePerDay);
        }
        // 3. 条件更新归还：只有状态为借阅中(0)才允许，防止并发重复还书
        BorrowRecord updateRecord = BorrowRecord.builder()
                .id(recordId)
                .status(true)
                .returnTime(now)
                .fineAmount(fine)
                .build();
        int rows = borrowRecordMapper.returnBook(updateRecord);
        if (rows == 0) {
            return ApiResult.error("该图书已归还，请勿重复操作");
        }
        // 4. 原子回补库存（不超过总数量）
        bookMapper.increaseAvailableCount(record.getBookId());
        if (fine.compareTo(BigDecimal.ZERO) > 0) {
            log.info("逾期归还: recordId={}, overdueDays={}, fine={}", recordId, fine, record.getBookId());
        }
        return ApiResult.success("归还成功" + (fine.compareTo(BigDecimal.ZERO) > 0 ? "，逾期罚款 " + fine + " 元" : ""));
    }

    /**
     * 分页查询借阅记录
     */
    @Override
    public Result<List<BorrowRecordVO>> query(BorrowRecordQueryDto dto) {
        List<BorrowRecordVO> recordList = borrowRecordMapper.query(dto);
        Integer totalCount = borrowRecordMapper.queryCount(dto);
        return PageResult.success(recordList, totalCount);
    }
}

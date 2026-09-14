package cn.kmbeast.service;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.BookAssistantQueryDto;
import cn.kmbeast.pojo.vo.BookAssistantVO;

/**
 * 图书智能问答服务
 */
public interface BookAssistantService {
    Result<BookAssistantVO> ask(BookAssistantQueryDto dto);
}

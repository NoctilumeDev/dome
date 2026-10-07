package cn.kmbeast.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * 图书智能问答返回结构
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BookAssistantVO {
    private String status;
    private String reason;
    private String interpretation;
    private String confirmationToken;
    private String confirmationExpiresAt;
    private String question;
    private String generatedSql;
    private String modelNote;
    private String answer;
    private Integer total;
    private Integer returnedCount;
    private Boolean truncated;
    private List<Map<String, Object>> books;
    private List<Map<String, Object>> records;
    private String intent;
    private Boolean databaseVerified;
    private String planningSource;
    private Boolean modelCalled;
}

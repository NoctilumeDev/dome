package cn.kmbeast;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.pojo.dto.query.extend.BookAssistantQueryDto;
import cn.kmbeast.pojo.vo.BookAssistantVO;
import cn.kmbeast.service.assistant.*;
import cn.kmbeast.service.impl.BookAssistantServiceImpl;
import org.h2.jdbcx.JdbcDataSource;
import org.junit.jupiter.api.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.util.ReflectionTestUtils;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class AssistantFactsTest {
    private BookAssistantServiceImpl service;
    private BookQueryRepository repository;
    private JdbcTemplate db;

    @BeforeEach void setup() {
        JdbcDataSource source = new JdbcDataSource();
        source.setURL("jdbc:h2:mem:" + UUID.randomUUID() + ";MODE=MySQL;DATABASE_TO_UPPER=FALSE;NON_KEYWORDS=USER;DB_CLOSE_DELAY=-1");
        db = new JdbcTemplate(source);
        db.execute("CREATE TABLE bookshelf(id INT PRIMARY KEY,name VARCHAR(64),location VARCHAR(64))");
        db.execute("CREATE TABLE book(id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(64),author VARCHAR(64),isbn VARCHAR(64),publisher VARCHAR(64),category VARCHAR(64),total_count INT,available_count INT,cover VARCHAR(64),description VARCHAR(64),create_time TIMESTAMP,bookshelf_id INT)");
        db.execute("CREATE TABLE user(id INT PRIMARY KEY,user_account VARCHAR(64),user_name VARCHAR(64),user_role INT,is_login BOOLEAN,create_time TIMESTAMP)");
        db.execute("CREATE TABLE borrow_record(id INT AUTO_INCREMENT PRIMARY KEY,user_id INT,book_id INT,borrow_time TIMESTAMP,due_date TIMESTAMP,return_time TIMESTAMP,status INT,fine_amount DECIMAL)");
        db.execute("CREATE TABLE feedback(id INT AUTO_INCREMENT PRIMARY KEY,user_id INT,content VARCHAR(100),reply VARCHAR(100),status INT,create_time TIMESTAMP,reply_time TIMESTAMP)");
        db.execute("CREATE TABLE book_review(id INT AUTO_INCREMENT PRIMARY KEY,user_id INT,book_id INT,rating INT,content VARCHAR(100),create_time TIMESTAMP,update_time TIMESTAMP)");
        db.update("INSERT INTO user(id,user_account,user_name,user_role,is_login) VALUES(1,'admin','管理员',1,FALSE),(2,'zhangsan','张三',2,FALSE),(3,'lisi','李四',2,FALSE)");
        db.update("INSERT INTO bookshelf VALUES(1,'一号','一层'),(2,'二号','二层'),(3,'空书架','三层')");
        for (int i = 1; i <= 55; i++) db.update("INSERT INTO book(id,name,author,category,total_count,available_count,bookshelf_id) VALUES(?,?,?,?,?,?,?)", i, i == 1 ? "Java入门" : i == 2 ? "三体" : "馆藏" + i, "演示作者", "编程", 3, 2, 1);
        db.update("INSERT INTO borrow_record(user_id,book_id,borrow_time,due_date,status) VALUES(2,1,NOW(),DATEADD('DAY',2,NOW()),0),(3,2,NOW(),DATEADD('DAY',2,NOW()),0)");
        for (int i = 0; i < 12; i++) db.update("INSERT INTO borrow_record(user_id,book_id,borrow_time,due_date,return_time,status) VALUES(3,2,NOW(),DATEADD('DAY',2,NOW()),NOW(),1)");
        db.update("INSERT INTO feedback(user_id,content,status) VALUES(2,'张三自己的反馈',0),(3,'PRIVATE_LISI_CANARY',0)");
        repository = new BookQueryRepository();
        ReflectionTestUtils.setField(repository, "dataSource", source);
        BookScopeGuard scope = new BookScopeGuard();
        DeepSeekBookQueryPlanner planner = new DeepSeekBookQueryPlanner();
        ReflectionTestUtils.setField(planner, "scopeGuard", scope);
        ReflectionTestUtils.setField(planner, "apiKey", "");
        service = new BookAssistantServiceImpl();
        ReflectionTestUtils.setField(service, "scopeGuard", scope);
        ReflectionTestUtils.setField(service, "queryPlanner", planner);
        ReflectionTestUtils.setField(service, "queryRepository", repository);
        ReflectionTestUtils.setField(service, "answerBuilder", new BookAnswerBuilder());
        LocalThreadHolder.setUserId(2, 2);
    }

    @AfterEach void cleanup() { db.execute("DROP ALL OBJECTS"); LocalThreadHolder.clear(); }

    private BookAssistantVO ask(String question) {
        BookAssistantQueryDto dto = new BookAssistantQueryDto(); dto.setQuestion(question);
        var response = service.ask(dto); assertEquals(200, response.getCode()); return response.getData();
    }

    @Test void catalogCountsAllBooksAndEmptyShelvesAndDisclosesTruncation() {
        BookAssistantVO result = ask("有哪些馆藏");
        assertEquals(55, result.getTotal()); assertEquals(50, result.getReturnedCount());
        assertTrue(result.getTruncated()); assertTrue(result.getAnswer().contains("3 个书架"));
        assertTrue(result.getAnswer().contains("仅返回前 50 条"));
    }

    @Test void personalLoansStayIsolatedAndHonorBookCondition() {
        BookAssistantVO all = ask("我借了哪些书");
        assertEquals("MY_BORROWS", all.getIntent()); assertEquals(1, all.getTotal());
        assertEquals("Java入门", all.getRecords().get(0).get("bookName"));
        assertEquals(0, ask("我的《三体》借阅记录").getTotal());
        assertEquals("FORBIDDEN", ask("李四借阅记录").getIntent());
        assertEquals("FORBIDDEN", ask("李四的反馈").getIntent());
        assertEquals("CLARIFY", ask("李四的反馈和我的借阅记录").getIntent());
        assertFalse(ask("我的反馈").getAnswer().contains("PRIVATE_LISI_CANARY"));
    }

    @Test void allReturnedBusinessRowsAreVisibleAndAdminFilterIsRetained() {
        LocalThreadHolder.setUserId(1, 1);
        BookAssistantVO returns = ask("谁最近还书了");
        assertEquals(12, returns.getTotal()); assertEquals(12, returns.getRecords().size());
        assertEquals(12, returns.getReturnedCount()); assertFalse(returns.getTruncated());
        assertEquals(12, returns.getAnswer().split("三体", -1).length - 1);
        BookAssistantVO feedback = ask("李四的反馈");
        assertEquals(1, feedback.getTotal()); assertTrue(feedback.getAnswer().contains("PRIVATE_LISI_CANARY"));
        assertFalse(feedback.getAnswer().contains("张三自己的反馈"));
    }

    @Test void wildcardsAndSqlLookingTitlesRemainLiteralReadOnlyParameters() {
        for (String value : new String[]{"%", "_", "' OR 1=1 --"}) {
            BookQueryPlan plan = new BookQueryPlan(); plan.setTitle(value);
            assertEquals(0, repository.query(plan, 2, false).getTotal());
        }
        assertEquals(55, db.queryForObject("SELECT COUNT(*) FROM book", Integer.class));
        db.update("INSERT INTO book(name,total_count,available_count) VALUES('100%_完美!',1,1)");
        BookQueryPlan literal = new BookQueryPlan(); literal.setTitle("%_");
        assertEquals(1, repository.query(literal, 2, false).getTotal());
    }

    @Test void namedDueAndReturnQueriesRetainTheirOwner() {
        LocalThreadHolder.setUserId(1, 1);
        assertEquals(1, ask("张三未来3天快要逾期了吗？").getTotal());
        assertEquals(0, ask("张三最近归还了哪些书？").getTotal());
    }

    @Test void superAdminKeepsItsAuthorizedAssistantWorkflow() {
        LocalThreadHolder.setUserId(1, 0);
        assertEquals("LIST_USERS", ask("有哪些用户").getIntent());
        assertEquals(12, ask("谁最近还书了").getTotal());
    }

    @Test void filteredCatalogDoesNotClaimTheWholeLibraryIsEmpty() {
        DeepSeekBookQueryPlanner planner = mock(DeepSeekBookQueryPlanner.class);
        BookQueryPlan plan = new BookQueryPlan(); plan.setIntent(BookIntent.LIST_CATALOG);
        plan.setAuthor("不存在的人");
        when(planner.plan(anyString())).thenReturn(plan);
        ReflectionTestUtils.setField(service, "queryPlanner", planner);
        BookAssistantVO result = ask("作者是不存在的人，本馆有哪些图书？");
        assertEquals(0, result.getTotal());
        assertTrue(result.getAnswer().contains("共登记 55 种图书"));
        assertFalse(result.getAnswer().contains("暂未登记图书"));
    }
}

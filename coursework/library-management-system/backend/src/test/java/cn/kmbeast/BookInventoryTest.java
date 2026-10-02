package cn.kmbeast;

import cn.kmbeast.mapper.BookMapper;
import cn.kmbeast.pojo.entity.Book;
import cn.kmbeast.service.impl.BookServiceImpl;
import org.apache.ibatis.builder.xml.XMLMapperBuilder;
import org.apache.ibatis.mapping.Environment;
import org.apache.ibatis.session.*;
import org.apache.ibatis.transaction.jdbc.JdbcTransactionFactory;
import org.h2.jdbcx.JdbcDataSource;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class BookInventoryTest {
    @Test void serviceRejectsInvalidCountsBeforeWriting() {
        BookMapper mapper = mock(BookMapper.class);
        BookServiceImpl service = new BookServiceImpl();
        ReflectionTestUtils.setField(service, "bookMapper", mapper);
        when(mapper.getById(1)).thenReturn(Book.builder().id(1).totalCount(6).availableCount(5).build());
        for (Book invalid : new Book[]{Book.builder().build(), Book.builder().totalCount(-1).build()})
            assertNotEquals(200, service.save(invalid).getCode());
        for (Book invalid : new Book[]{
                Book.builder().id(1).totalCount(1).availableCount(99).build(),
                Book.builder().id(1).availableCount(-1).build(),
                Book.builder().id(1).totalCount(4).build()})
            assertNotEquals(200, service.update(invalid).getCode());
        verify(mapper, never()).insert(any());
        verify(mapper, never()).update(any());
        when(mapper.update(any())).thenReturn(1);
        assertEquals(200, service.update(Book.builder().id(1).totalCount(7).availableCount(6).build()).getCode());
        Book zero = Book.builder().totalCount(0).availableCount(99).build();
        assertEquals(200, service.save(zero).getCode());
        assertEquals(0, zero.getAvailableCount());
    }

    @Test void mapperAtomicallyGuardsCountsIncludingPartialEdits() throws Exception {
        JdbcDataSource source = new JdbcDataSource();
        source.setURL("jdbc:h2:mem:" + UUID.randomUUID() + ";MODE=MySQL;DB_CLOSE_DELAY=-1");
        JdbcTemplate db = new JdbcTemplate(source);
        db.execute("CREATE TABLE book(id INT PRIMARY KEY,name VARCHAR(64),total_count INT,available_count INT)");
        db.update("INSERT INTO book VALUES(1,'三体',6,5)");
        Configuration configuration = new Configuration(new Environment("inventory", new JdbcTransactionFactory(), source));
        try (var xml = getClass().getResourceAsStream("/mapper/BookMapper.xml")) {
            assertNotNull(xml);
            new XMLMapperBuilder(xml, configuration, "mapper/BookMapper.xml", configuration.getSqlFragments()).parse();
        }
        try (SqlSession session = new SqlSessionFactoryBuilder().build(configuration).openSession(true)) {
            BookMapper mapper = session.getMapper(BookMapper.class);
            for (Book invalid : new Book[]{
                    Book.builder().id(1).totalCount(1).availableCount(99).build(),
                    Book.builder().id(1).availableCount(-1).build(),
                    Book.builder().id(1).totalCount(-1).build(),
                    Book.builder().id(1).totalCount(4).build()})
                assertEquals(0, mapper.update(invalid));
            assertEquals(5, db.queryForObject("SELECT available_count FROM book WHERE id=1", Integer.class));
            assertEquals(1, mapper.update(Book.builder().id(1).name("三体新版").build()));
            assertEquals(1, mapper.update(Book.builder().id(1).totalCount(7).availableCount(6).build()));
            assertEquals(6, db.queryForObject("SELECT available_count FROM book WHERE id=1", Integer.class));
        } finally {
            db.execute("DROP ALL OBJECTS");
        }
    }
}

package cn.kmbeast;

import cn.kmbeast.service.assistant.*;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import java.time.*;
import static org.junit.jupiter.api.Assertions.*;

class AssistantConsentTest {
    @Test void snapshotExpirySessionAndRequestGenerationStayBound() {
        BookScopeConsents c = new BookScopeConsents();
        Clock clock = Clock.fixed(Instant.parse("2026-10-08T00:00:00Z"), ZoneOffset.UTC);
        ReflectionTestUtils.setField(c, "clock", clock);
        BookQueryPlan p = new BookQueryPlan(); p.setIntent(BookIntent.MY_BORROWS); p.setTitle("三体");
        var older = c.begin(2, "session"); var newer = c.begin(2, "session");
        assertNull(c.offer(older, "old", p));
        var offer = c.offer(newer, "new", p); p.setTitle("修改后");
        assertNull(c.consume(3, "session", offer.token())); assertNull(c.consume(2, "other", offer.token()));
        assertEquals("三体", c.consume(2, "session", offer.token()).plan().getTitle());
        assertNull(c.consume(2, "session", offer.token()));
        var expiring = c.offer(c.begin(2, "session"), "new", p);
        ReflectionTestUtils.setField(c, "clock", Clock.offset(clock, Duration.ofMinutes(5)));
        assertNull(c.consume(2, "session", expiring.token()));
        assertNull(c.begin(2, null));
    }
    @Test void openingAnyNewQuestionInvalidatesTheOldOffer() {
        BookScopeConsents c = new BookScopeConsents();
        var offer = c.offer(c.begin(2, "A"), "old", new BookQueryPlan());
        c.begin(2, "A"); assertNull(c.consume(2, "A", offer.token()));
        // The other session's state is independent.
        var independent = c.offer(c.begin(2, "B"), "B", new BookQueryPlan());
        c.begin(2, "A"); assertNotNull(c.consume(2, "B", independent.token()));
    }
}

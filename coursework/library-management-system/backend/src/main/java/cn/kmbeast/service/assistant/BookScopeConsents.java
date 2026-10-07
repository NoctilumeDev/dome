package cn.kmbeast.service.assistant;

import org.springframework.stereotype.Component;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.*;
import java.util.*;

/** Single-instance, bounded, expiring consent; no secrets or records are stored. Restart invalidates it. */
@Component
public class BookScopeConsents {
    private Clock clock = Clock.systemUTC();
    private final Map<String, State> sessions = new HashMap<>();
    private static final int MAX_SESSIONS = 1000;
    private static final Duration TTL = Duration.ofMinutes(5);
    public record Ticket(String owner, UUID generation) {}
    public record Offered(String token, Instant expiresAt) {}
    public record Confirmed(String question, BookQueryPlan plan) {}
    private record Offer(String token, String question, BookQueryPlan plan) {}
    private record State(UUID generation, Instant expiresAt, Offer offer) {}

    public synchronized Ticket begin(Integer actor, String session) {
        prune();
        if (actor == null || session == null || session.isBlank()) return null;
        String owner = owner(actor, session);
        if (!sessions.containsKey(owner) && sessions.size() >= MAX_SESSIONS) return null;
        UUID generation = UUID.randomUUID();
        sessions.put(owner, new State(generation, clock.instant().plus(TTL), null));
        return new Ticket(owner, generation);
    }
    public synchronized Offered offer(Ticket ticket, String question, BookQueryPlan plan) {
        prune();
        if (ticket == null) return null;
        State state = sessions.get(ticket.owner());
        if (state == null || !state.generation().equals(ticket.generation())) return null;
        String token = UUID.randomUUID().toString();
        Instant expires = clock.instant().plus(TTL);
        sessions.put(ticket.owner(), new State(state.generation(), expires, new Offer(token, question, plan.snapshot())));
        return new Offered(token, expires);
    }
    public synchronized Confirmed consume(Integer actor, String session, String token) {
        prune();
        if (actor == null || session == null || token == null) return null;
        String owner = owner(actor, session); State state = sessions.get(owner);
        if (state == null || state.offer() == null || !state.offer().token().equals(token)) return null;
        sessions.put(owner, new State(state.generation(), state.expiresAt(), null));
        return new Confirmed(state.offer().question(), state.offer().plan().snapshot());
    }
    private void prune() { Instant now = clock.instant(); sessions.values().removeIf(s -> !now.isBefore(s.expiresAt())); }
    private String owner(Integer actor, String session) {
        try { return actor + ":" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(session.getBytes(StandardCharsets.UTF_8))); }
        catch (java.security.NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }
}

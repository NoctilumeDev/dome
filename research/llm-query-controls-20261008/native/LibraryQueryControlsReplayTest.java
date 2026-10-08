package cn.kmbeast;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.pojo.dto.query.extend.BookAssistantQueryDto;
import cn.kmbeast.service.assistant.*;
import cn.kmbeast.service.impl.BookAssistantServiceImpl;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.util.ReflectionTestUtils;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** Research-only replay. No provider, live DB, product modification or human participant. */
class LibraryQueryControlsReplayTest extends AssistantFactsTest {
    private final ObjectMapper json = new ObjectMapper().findAndRegisterModules();
    private Object inherited(String name) throws Exception {
        var field = AssistantFactsTest.class.getDeclaredField(name);
        field.setAccessible(true); return field.get(this);
    }
    private String snapshot(JdbcTemplate db) throws Exception {
        var state = new LinkedHashMap<String,Object>();
        for (String table : List.of("book","bookshelf","user","borrow_record","feedback","book_review"))
            state.put(table, db.queryForList("SELECT * FROM " + table + " ORDER BY id"));
        return json.writeValueAsString(state);
    }
    private void fixture(JdbcTemplate db, com.fasterxml.jackson.databind.JsonNode f) {
        for (String table : List.of("borrow_record","feedback","book_review","book","user")) db.update("DELETE FROM " + table);
        var now = LocalDateTime.of(2026,10,8,1,0);
        for (var u : f.path("users")) db.update("INSERT INTO user(id,user_account,user_name,user_role,is_login,create_time) VALUES(?,?,?,?,FALSE,?)", u.path("id").asInt(), "synthetic-"+u.path("id").asInt(), u.path("name").asText(), 2, now);
        for (var b : f.path("books")) db.update("INSERT INTO book(id,name,author,isbn,publisher,category,total_count,available_count,description,bookshelf_id,create_time) VALUES(?,?,?,?,?,?,?,?,?,?,?)", b.path("id").asInt(), b.path("name").asText(), b.path("author").asText(), b.path("isbn").asText(), b.path("publisher").asText(), b.path("category").asText(), b.path("total").asInt(), b.path("available").asInt(), b.path("description").asText(), b.path("shelf").asInt(), now);
        for (int u : new int[]{101,102}) {
            db.update("INSERT INTO borrow_record(id,user_id,book_id,borrow_time,due_date,status) VALUES(?,?,?,?,?,0)", 900+u, u, u==101?201:203, now.minusDays(1), now.plusDays(2));
            db.update("INSERT INTO feedback(id,user_id,content,status,create_time) VALUES(?,?,?,0,?)", u,u,"PRIVATE_OWNER_"+u,now);
        }
        // An orphaned record is not a retained historical book-name snapshot.
        db.update("INSERT INTO borrow_record(id,user_id,book_id,borrow_time,due_date,return_time,status) VALUES(1003,101,299,?,?,?,1)", now.minusDays(50), now.minusDays(40), now.minusDays(41));
    }
    @Test void nativeQueryControls() throws Exception {
        var db=(JdbcTemplate)inherited("db"); var repo=(BookQueryRepository)inherited("repository");
        var service=(BookAssistantServiceImpl)inherited("service");
        var fixed=Clock.fixed(Instant.parse("2026-10-07T17:00:00Z"),ZoneId.of("Asia/Shanghai"));
        ReflectionTestUtils.setField(repo,"clock",fixed);
        ReflectionTestUtils.setField(ReflectionTestUtils.getField(service,"consents"),"clock",fixed);
        var parser=new DeepSeekBookQueryPlanner(); ReflectionTestUtils.setField(parser,"objectMapper",json);
        var fixtures=json.readTree(Files.readString(Path.of(System.getenv("QUERY_CONTROLS_FIXTURES"))));
        var inputs=json.readTree(Files.readString(Path.of(System.getenv("RESEARCH_NATIVE_INPUT"))));
        Path output=Path.of(System.getenv("RESEARCH_NATIVE_OUTPUT")); Files.writeString(output,"");
        var snapshots=new LinkedHashMap<String,Object>();
        for(var input:inputs) {
            if(!"library".equals(input.path("system").asText()))continue;
            String fixtureName=input.path("fixture").asText(); fixture(db,fixtures.path(fixtureName));
            int actor=input.path("actor").asInt(); boolean admin=input.path("admin").asBoolean();
            LocalThreadHolder.setUserId(actor,admin?1:2);
            String before=snapshot(db); snapshots.putIfAbsent(fixtureName,before);
            var queries=new ArrayList<Map<String,Object>>();
            doAnswer(inv->{
                var plan=(BookQueryPlan)inv.getArgument(0); var facts=(BookQueryRepository.QueryResult)inv.callRealMethod();
                var trace=new LinkedHashMap<String,Object>(); trace.put("plan",json.valueToTree(plan));
                trace.put("subjectId",inv.getArgument(1));trace.put("adminParameter",inv.getArgument(2));
                trace.put("sqlAndParameters",facts.getDisplaySql());trace.put("rows",facts.getRows());queries.add(trace);return facts;
            }).when(repo).query(any(),any(),anyBoolean());
            final boolean[] called={false}, parsed={false}, qualified={false};
            final BookQueryPlan[] proposed={null}; var planner=mock(DeepSeekBookQueryPlanner.class);
            when(planner.plan(anyString())).thenAnswer(inv->{
                called[0]=true; var shortcut=parser.shortcut(inv.getArgument(0));
                if(shortcut!=null){proposed[0]=shortcut;return shortcut;}
                if(!input.path("complete").asBoolean())return DeepSeekBookQueryPlanner.decision("CLARIFY","SERVICE_UNAVAILABLE");
                try {
                    String raw=input.path("rawContent").asText().trim();
                    if(raw.startsWith("```json\n")&&raw.endsWith("```"))raw=raw.substring(8,raw.length()-3).trim();
                    var plan=parser.parse(raw);parsed[0]=true;qualified[0]=!"QUERY".equals(plan.getAction())||BookPlanPolicy.check(plan)==null;
                    plan.setModelCalled(true);plan.setPlanningSource("MODEL");proposed[0]=plan;return plan;
                }catch(Exception e){return DeepSeekBookQueryPlanner.decision("REJECT","INVALID_PLAN");}
            });
            ReflectionTestUtils.setField(service,"queryPlanner",planner); clearInvocations(repo);
            var dto=new BookAssistantQueryDto();dto.setQuestion(input.path("question").asText());
            String session="query-controls-"+actor;
            var result=service.ask(dto,session);assertEquals(200,result.getCode());var response=result.getData();
            var record=new LinkedHashMap<String,Object>();record.put("recordId",input.path("recordId").asText());
            record.put("callId",input.path("callId").asText());record.put("system","library");record.put("fixture",fixtureName);
            record.put("actor",actor);record.put("admin",admin);record.put("nativePlannerCalled",called[0]);
            record.put("nativeParseAccepted",parsed[0]);record.put("nativeQualified",qualified[0]);record.put("effectiveNativePlan",proposed[0]);
            record.put("queriesBeforeConfirmation",queries.size());
            if("CONFIRM_SCOPE".equals(response.getStatus())) {
                assertTrue(queries.isEmpty(),"No personal reads before confirmation");
                String token=response.getConfirmationToken();response.setConfirmationToken(null);
                LocalThreadHolder.setUserId(actor==101?102:101,admin?1:2);
                var wrongActor=service.confirm(Map.of("confirmationToken",token),session);
                assertEquals(400,wrongActor.getCode()); assertTrue(queries.isEmpty());
                LocalThreadHolder.setUserId(actor,admin?1:2);
                var wrongSession=service.confirm(Map.of("confirmationToken",token),session+"-other");
                assertEquals(400,wrongSession.getCode()); assertTrue(queries.isEmpty());
                var confirmed=service.confirm(Map.of("confirmationToken",token),session);
                assertEquals(200,confirmed.getCode());record.put("simulatedConfirmation",confirmed.getData());
                int after=queries.size();assertEquals(400,service.confirm(Map.of("confirmationToken",token),session).getCode());assertEquals(after,queries.size());
                verify(planner,times(1)).plan(anyString());
                record.put("crossActorRejected",true);record.put("crossSessionRejected",true);record.put("singleUse",true);
                record.put("simulatedUser","ACCEPT_EXACT_DISPLAYED_SCOPE; NOT_HUMAN_EVIDENCE");
            }
            for(var query:queries) {
                assertEquals(actor,query.get("subjectId"));assertEquals(false,query.get("adminParameter"));
                var plan=(com.fasterxml.jackson.databind.JsonNode)query.get("plan");
                if(plan.path("intent").asText().startsWith("MY_"))for(var row:(List<Map<String,Object>>)query.get("rows"))
                    assertEquals(actor,((Number)row.get("userId")).intValue(),"Read returned another subject");
            }
            record.put("response",response);record.put("queryTrace",queries);
            record.put("snapshotUnchanged",snapshot(db).equals(before));assertEquals(true,record.get("snapshotUnchanged"));
            Files.writeString(output,json.writeValueAsString(record)+"\n",StandardOpenOption.APPEND);
        }
        Files.writeString(Path.of(System.getenv("RESEARCH_NATIVE_SNAPSHOT")),json.writeValueAsString(snapshots));
    }
}

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

class LibraryResearchReplayTest extends AssistantFactsTest {
 private final ObjectMapper json=new ObjectMapper().findAndRegisterModules();
 private Object get(String name) throws Exception{var f=AssistantFactsTest.class.getDeclaredField(name);f.setAccessible(true);return f.get(this);}
 private String snapshot(JdbcTemplate db) throws Exception{var all=new LinkedHashMap<String,Object>();for(String t:List.of("book","bookshelf","user","borrow_record","feedback","book_review"))all.put(t,db.queryForList("SELECT * FROM "+t+" ORDER BY id"));return json.writeValueAsString(all);}
 @Test void nativeFrozenReplay() throws Exception {
  var service=(BookAssistantServiceImpl)get("service");var repository=(BookQueryRepository)get("repository");var db=(JdbcTemplate)get("db");
  var fixed=Clock.fixed(Instant.parse("2026-10-07T17:00:00Z"),ZoneId.of("Asia/Shanghai"));
  ReflectionTestUtils.setField(repository,"clock",fixed);
  ReflectionTestUtils.setField(ReflectionTestUtils.getField(service,"consents"),"clock",fixed);
  var now=LocalDateTime.now(fixed);db.update("UPDATE borrow_record SET borrow_time=?,due_date=?,return_time=CASE WHEN status=1 THEN ? ELSE NULL END",now.minusDays(1),now.plusDays(2),now);
  db.update("UPDATE book SET available_count=1 WHERE id=1");db.update("UPDATE book SET total_count=7,available_count=4,bookshelf_id=2 WHERE id=2");
  String before=snapshot(db);
  Path output=Path.of(System.getenv("RESEARCH_NATIVE_OUTPUT"));Files.writeString(output,"");
  var inputs=json.readTree(Files.readString(Path.of(System.getenv("RESEARCH_NATIVE_INPUT"))));
  var realParser=new DeepSeekBookQueryPlanner();ReflectionTestUtils.setField(realParser,"objectMapper",json);
  for(var input:inputs){
   if(!input.path("system").asText().equals("library"))continue;
   var record=new LinkedHashMap<String,Object>();record.put("callId",input.path("callId").asText());record.put("system","library");
   var planner=mock(DeepSeekBookQueryPlanner.class);final boolean[] parseAccepted={false};final boolean[] qualified={false};final boolean[] plannerCalled={false};
   when(planner.plan(anyString())).thenAnswer(inv->{
    plannerCalled[0]=true;
    var shortcut=realParser.shortcut(inv.getArgument(0));if(shortcut!=null)return shortcut;
    if(!input.path("complete").asBoolean())return DeepSeekBookQueryPlanner.decision("CLARIFY","SERVICE_UNAVAILABLE");
    try{String raw=input.path("rawContent").asText().trim();if(raw.startsWith("```json\n")&&raw.endsWith("```"))raw=raw.substring(8,raw.length()-3).trim();var p=realParser.parse(raw);parseAccepted[0]=true;qualified[0]=!"QUERY".equals(p.getAction())||BookPlanPolicy.check(p)==null;p.setModelCalled(true);p.setPlanningSource("MODEL");return p;}
    catch(Exception e){return DeepSeekBookQueryPlanner.decision("REJECT","INVALID_PLAN");}
   });ReflectionTestUtils.setField(service,"queryPlanner",planner);
   clearInvocations(repository);LocalThreadHolder.setUserId(2,2);
   var dto=new BookAssistantQueryDto();dto.setQuestion(input.path("question").asText());var result=service.ask(dto,"research-session");assertEquals(200,result.getCode());var response=result.getData();
   record.put("nativePlannerCalled",plannerCalled[0]);record.put("nativeParseAccepted",parseAccepted[0]);record.put("nativeQualified",qualified[0]);record.put("repositoryQueriesBeforeConfirm",mockingDetails(repository).getInvocations().stream().filter(v->v.getMethod().getName().equals("query")).count());
   if("CONFIRM_SCOPE".equals(response.getStatus())){
    verify(repository,never()).query(any(),any(),anyBoolean());
    var confirmed=service.confirm(Map.of("confirmationToken",response.getConfirmationToken()),"research-session");assertEquals(200,confirmed.getCode());
    record.put("simulatedConfirmation",confirmed.getData());record.put("simulatedUser","ACCEPT_EXACT_DISPLAYED_SCOPE; not a human");response.setConfirmationToken(null);
   }
   assertFalse(json.writeValueAsString(response).contains("PRIVATE_LISI_CANARY"));
   if(record.containsKey("simulatedConfirmation"))assertFalse(json.writeValueAsString(record.get("simulatedConfirmation")).contains("PRIVATE_LISI_CANARY"));
   record.put("response",response);record.put("databaseUnchanged",snapshot(db).equals(before));assertEquals(true,record.get("databaseUnchanged"));
   Files.writeString(output,json.writeValueAsString(record)+"\n",StandardOpenOption.APPEND);
  }
  Files.writeString(Path.of(System.getenv("RESEARCH_NATIVE_SNAPSHOT")),before);
 }
}

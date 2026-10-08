package cn.qingye;
import cn.qingye.business.*;
import cn.qingye.db.*;
import cn.qingye.integration.*;
import cn.qingye.model.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.*;
import java.net.URI;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import static org.assertj.core.api.Assertions.*;

@SpringBootTest(properties={"qingye.demo-enabled=false","qingye.worker-enabled=false","qingye.redis-enabled=false","qingye.mq-enabled=false","qingye.wx-appid=","qingye.wx-secret=","qingye.llm-url=","qingye.llm-key=","qingye.token-secret=fixture-only-token-secret-more-than-32","spring.datasource.url=jdbc:h2:mem:research_replay;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1","spring.datasource.username=sa","spring.datasource.password="})
@Import(QingyeResearchReplayTest.TimeConfig.class)
class QingyeResearchReplayTest {
 @org.springframework.boot.test.mock.mockito.SpyBean Sql sql;
 @Autowired ActivityStore activities; @Autowired LoanStore loans; @Autowired LoanService loanService; @Autowired ObjectMapper json; @Autowired Clock clock;
 static final List<String> TABLES=List.of("message_task","notification","loan","registration","activity","club_member","club","equipment","app_user");
 @TestConfiguration static class TimeConfig {@Bean @Primary Clock researchClock(){return Clock.fixed(Instant.parse("2026-10-07T17:00:00Z"),ZoneId.of("Asia/Shanghai"));}}
 String snapshot() throws Exception {var out=new LinkedHashMap<String,Object>();for(String t:TABLES)out.put(t,sql.list("SELECT * FROM "+t+" ORDER BY id"));return json.writeValueAsString(out);}
 static class ReplayHttp extends ExternalHttp {
  String raw; boolean complete; int calls;
  ReplayHttp(ObjectMapper j){super(j);}
  @Override public Map<?,?> post(URI u,String k,Map<String,Object> b) throws Exception {calls++;if(!complete)throw new java.io.IOException("RETAINED_PROVIDER_UNAVAILABLE");return Map.of("choices",List.of(Map.of("finish_reason","stop","message",Map.of("content",raw))));}
 }
 static class ReplayPlanner extends LlmPlanner {
  Optional<QueryPlan> last=Optional.empty();
  ReplayPlanner(ExternalHttp h,ObjectMapper j,Clock c){super(h,j,c,"https://unused.invalid","fixture-only","deepseek-flash");}
  @Override public Optional<QueryPlan> plan(String q){last=super.plan(q);return last;}
 }
 @Test void nativeFrozenReplay() throws Exception {
  var now=LocalDateTime.now(clock);
  long uid=sql.insert("INSERT INTO app_user(openid,name,admin) VALUES('research:own','fixture own',false)");
  long oid=sql.insert("INSERT INTO app_user(openid,name,admin) VALUES('research:other','fixture other',false)");
  var actor=new Actor(uid,"fixture own",false);
  long club=sql.insert("INSERT INTO club(name,created_by) VALUES('摄影社',?)",oid);
  long aid=sql.insert("INSERT INTO activity(club_id,created_by,title,category,location,start_time,end_time,signup_deadline,capacity,status) VALUES(?,?,'校园摄影活动','ART','东操场',?,?,?,20,'PUBLISHED')",club,oid,now.plusHours(18),now.plusHours(20),now.plusHours(16));
  sql.insert("INSERT INTO registration(activity_id,user_id,status,joined_at) VALUES(?,?,'REGISTERED',?)",aid,uid,now);
  long eid=loans.createEquipment("相机","摄影","fixture camera","",5,true);
  long own=loans.create(aid,uid,eid,1,now.plusHours(2),now.plusHours(3),"own private","research-own");
  loans.create(aid,oid,eid,1,now.plusHours(3),now.plusHours(4),"PRIVATE_OTHER_CANARY","research-other");
  for(var e:List.of(Map.entry("摄像机",2),Map.entry("手机",4),Map.entry("投影仪",3),Map.entry("相机充电器",1),Map.entry("摄像头",2)))loans.createEquipment(e.getKey(),"fixture","fixture","",e.getValue(),true);
  for(String table:TABLES){var rows=sql.list("SELECT * FROM "+table+" ORDER BY id");if(!rows.isEmpty()&&rows.get(0).containsKey("createdAt"))sql.update("UPDATE "+table+" SET created_at=?",now);}
  String before=snapshot();var http=new ReplayHttp(json);
  var planner=new ReplayPlanner(http,json,clock);
  var service=new AssistantService(activities,loans,loanService,planner,clock);
  Path output=Path.of(System.getenv("RESEARCH_NATIVE_OUTPUT"));Files.writeString(output,"");
  var inputs=json.readTree(Files.readString(Path.of(System.getenv("RESEARCH_NATIVE_INPUT"))));
  for(var input:inputs){
   if(!input.path("system").asText().equals("qingye"))continue;
   http.raw=input.path("rawContent").asText();http.complete=input.path("complete").asBoolean();int calls=http.calls;planner.last=Optional.empty();
   org.mockito.Mockito.clearInvocations(sql);
   var response=new LinkedHashMap<String,Object>(service.ask(actor,input.path("question").asText(),"research-session"));
   var askSql=new ArrayList<String>();boolean mutation=false;
   for(var invocation:org.mockito.Mockito.mockingDetails(sql).getInvocations()){if(Set.of("insert","update").contains(invocation.getMethod().getName()))mutation=true;var a=invocation.getArguments();if(a.length>0&&a[0] instanceof String s)askSql.add(s);}
   assertThat(mutation).as("fixed read path").isFalse();
   var record=new LinkedHashMap<String,Object>();record.put("callId",input.path("callId").asText());record.put("system","qingye");record.put("nativePlannerCalled",http.calls>calls);record.put("askSql",askSql);record.put("mutationAttempt",mutation);
   boolean qualified=false;try{qualified=http.complete&&planner.last.isPresent()&&json.readTree(http.raw).equals(json.valueToTree(planner.last.get()));}catch(Exception ignored){}
   record.put("nativeQualified",qualified);record.put("effectiveNativePlan",planner.last.orElse(null));
   if("CONFIRM_SCOPE".equals(response.get("status"))){
    assertThat(askSql.stream().anyMatch(s->s.contains("FROM loan ")||s.contains("JOIN registration"))).isFalse();
    String token=response.get("confirmationToken").toString();response.remove("confirmationToken");
    var confirmed=service.confirm(actor,token,"research-session");record.put("simulatedConfirmation",confirmed);record.put("simulatedUser","ACCEPT_EXACT_DISPLAYED_SCOPE; not a human");
    if("MY_LOANS".equals(confirmed.get("intent")))for(var row:(List<Map<String,Object>>)confirmed.get("items"))assertThat(((Number)row.get("id")).longValue()).isEqualTo(own);
   }
   String visible=json.writeValueAsString(response);assertThat(visible).doesNotContain("PRIVATE_OTHER_CANARY");
   record.put("response",response);record.put("databaseUnchanged",snapshot().equals(before));assertThat(record.get("databaseUnchanged")).isEqualTo(true);
   Files.writeString(output,json.writeValueAsString(record)+"\n",StandardOpenOption.APPEND);
  }
  Files.writeString(Path.of(System.getenv("RESEARCH_NATIVE_SNAPSHOT")),before);
 }
}

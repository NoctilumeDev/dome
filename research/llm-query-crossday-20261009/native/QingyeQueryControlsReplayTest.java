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

@SpringBootTest(properties={"qingye.demo-enabled=false","qingye.worker-enabled=false","qingye.redis-enabled=false","qingye.mq-enabled=false","qingye.wx-appid=","qingye.wx-secret=","qingye.llm-url=","qingye.llm-key=","qingye.token-secret=fixture-only-token-secret-more-than-32","spring.datasource.url=jdbc:h2:mem:query_controls;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1","spring.datasource.username=sa","spring.datasource.password="})
@Import(QingyeQueryControlsReplayTest.TimeConfig.class)
class QingyeQueryControlsReplayTest {
    @org.springframework.boot.test.mock.mockito.SpyBean Sql sql;
    @Autowired ActivityStore activities; @Autowired LoanStore loans; @Autowired LoanService loanService;
    @Autowired ObjectMapper json; @Autowired Clock clock;
    static final List<String> TABLES=List.of("message_task","notification","loan","registration","activity","club_member","club","equipment","app_user");
    @TestConfiguration static class TimeConfig {
        @Bean @Primary Clock researchClock(){return Clock.fixed(Instant.parse("2026-10-07T17:00:00Z"),ZoneId.of("Asia/Shanghai"));}
    }
    String snapshot() throws Exception {
        var state=new LinkedHashMap<String,Object>();for(String table:TABLES)state.put(table,sql.list("SELECT * FROM "+table+" ORDER BY id"));
        return json.writeValueAsString(state);
    }
    static class ReplayHttp extends ExternalHttp {
        String raw;boolean complete;int calls;ReplayHttp(ObjectMapper j){super(j);}
        @Override public Map<?,?> post(URI u,String key,Map<String,Object> body)throws Exception {
            calls++;if(!complete)throw new java.io.IOException("RETAINED_PROVIDER_UNAVAILABLE");
            return Map.of("choices",List.of(Map.of("finish_reason","stop","message",Map.of("content",raw))));
        }
    }
    static class ReplayPlanner extends LlmPlanner {
        Optional<QueryPlan> last=Optional.empty();ReplayPlanner(ExternalHttp http,ObjectMapper j,Clock c){super(http,j,c,"https://unused.invalid","fixture-only","deepseek-flash");}
        @Override public Optional<QueryPlan> plan(String question){last=super.plan(question);return last;}
    }
    List<Map<String,Object>> trace() {
        var out=new ArrayList<Map<String,Object>>();
        for(var invocation:org.mockito.Mockito.mockingDetails(sql).getInvocations()) {
            assertThat(Set.of("insert","update").contains(invocation.getMethod().getName())).as("No mutation in read/confirm path").isFalse();
            var args=invocation.getArguments();if(args.length>0&&args[0] instanceof String statement) {
                var row=new LinkedHashMap<String,Object>();row.put("sql",statement);row.put("parameters",Arrays.asList(args).subList(1,args.length));out.add(row);
            }
        }return out;
    }
    @Test void nativeQueryControls()throws Exception {
        var now=LocalDateTime.now(clock);
        for(int user:new int[]{101,102})sql.update("INSERT INTO app_user(id,openid,name,admin) VALUES(?,?,?,false)",user,"query-control-"+user,"fixture");
        long club=sql.insert("INSERT INTO club(name,created_by) VALUES('摄影社',102)");
        long aid=sql.insert("INSERT INTO activity(club_id,created_by,title,category,location,start_time,end_time,signup_deadline,capacity,status) VALUES(?,102,'校园摄影活动','ART','东操场',?,?,?,20,'PUBLISHED')",club,now.plusHours(18),now.plusHours(20),now.plusHours(16));
        sql.insert("INSERT INTO registration(activity_id,user_id,status,joined_at) VALUES(?,101,'REGISTERED',?)",aid,now);
        long camera=loans.createEquipment("相机","摄影","fixture camera","",5,true);
        long own=loans.create(aid,101,camera,1,now.plusDays(1),now.plusDays(1).plusHours(2),"PRIVATE_OWNER_101","query-control-101");
        long other=loans.create(aid,102,camera,2,now.plusDays(1),now.plusDays(1).plusHours(2),"PRIVATE_OWNER_102","query-control-102");
        sql.update("UPDATE loan SET status='APPROVED' WHERE id=?",own);
        for(var entry:List.of(Map.entry("摄像机",2),Map.entry("手机",4),Map.entry("投影仪",3),Map.entry("相机充电器",1),Map.entry("摄像头",2)))loans.createEquipment(entry.getKey(),"fixture","fixture","",entry.getValue(),true);
        for(String table:TABLES){var rows=sql.list("SELECT * FROM "+table+" ORDER BY id");if(!rows.isEmpty()&&rows.get(0).containsKey("createdAt"))sql.update("UPDATE "+table+" SET created_at=?",now);}
        var fixtures=json.readTree(Files.readString(Path.of(System.getenv("QUERY_CONTROLS_FIXTURES"))));
        var inputs=json.readTree(Files.readString(Path.of(System.getenv("RESEARCH_NATIVE_INPUT"))));
        var http=new ReplayHttp(json);var planner=new ReplayPlanner(http,json,clock);
        var service=new AssistantService(activities,loans,loanService,planner,clock);
        Path output=Path.of(System.getenv("RESEARCH_NATIVE_OUTPUT"));Files.writeString(output,"");var snapshots=new LinkedHashMap<String,Object>();
        for(var input:inputs) {
            if(!"qingye".equals(input.path("system").asText()))continue;
            String fixtureName=input.path("fixture").asText();var fixture=fixtures.path(fixtureName);
            for(var u:fixture.path("users"))sql.update("UPDATE app_user SET name=? WHERE id=?",u.path("name").asText(),u.path("id").asInt());
            long actorId=input.path("actor").asLong();boolean admin=input.path("admin").asBoolean();
            sql.update("UPDATE app_user SET admin=? WHERE id=?",admin,actorId);
            sql.update("UPDATE app_user SET admin=false WHERE id=?",actorId==101?102:101);
            String before=snapshot();snapshots.putIfAbsent(fixtureName+"/"+actorId+"/"+admin,before);
            var actor=new Actor(actorId,fixture.path("users").get(actorId==101?0:1).path("name").asText(),admin);
            http.raw=input.path("rawContent").asText();http.complete=input.path("complete").asBoolean();int priorCalls=http.calls;planner.last=Optional.empty();
            org.mockito.Mockito.clearInvocations(sql);
            String session="query-controls-"+actorId;
            var response=new LinkedHashMap<String,Object>(service.ask(actor,input.path("question").asText(),session));
            var askTrace=trace();
            var record=new LinkedHashMap<String,Object>();record.put("recordId",input.path("recordId").asText());record.put("callId",input.path("callId").asText());
            record.put("system","qingye");record.put("fixture",fixtureName);record.put("actor",actorId);record.put("admin",admin);
            record.put("nativePlannerCalled",http.calls>priorCalls);boolean qualified=false;
            try{qualified=http.complete&&planner.last.isPresent()&&json.readTree(http.raw).equals(json.valueToTree(planner.last.get()));}catch(Exception ignored){}
            record.put("nativeQualified",qualified);record.put("effectiveNativePlan",planner.last.orElse(null));record.put("askTrace",askTrace);
            if("CONFIRM_SCOPE".equals(response.get("status"))) {
                assertThat(askTrace.stream().anyMatch(row->row.get("sql").toString().contains("FROM loan "))).isFalse();
                String token=response.remove("confirmationToken").toString();
                var wrongActor=service.confirm(new Actor(actorId==101?102:101,"same-or-similar-name",admin),token,session);
                assertThat(wrongActor.get("status")).isEqualTo("CLARIFY");assertThat(trace()).isEqualTo(askTrace);
                assertThat(service.confirm(actor,token,session+"-other").get("status")).isEqualTo("CLARIFY");assertThat(trace()).isEqualTo(askTrace);
                var confirmed=service.confirm(actor,token,session);record.put("simulatedConfirmation",confirmed);var after=trace();
                if("MY_LOANS".equals(confirmed.get("intent")))for(var row:(List<Map<String,Object>>)confirmed.get("items"))assertThat(((Number)row.get("id")).longValue()).isEqualTo(actorId==101?own:other);
                if("MY_REGISTRATIONS".equals(confirmed.get("intent"))) {
                    var rows=(List<Map<String,Object>>)confirmed.get("items");
                    if(actorId==102)assertThat(rows).isEmpty();
                    else for(var row:rows)assertThat(((Number)row.get("id")).longValue()).isEqualTo(aid);
                }
                assertThat(service.confirm(actor,token,session).get("status")).isEqualTo("CLARIFY");assertThat(trace()).isEqualTo(after);
                assertThat(http.calls-priorCalls).isEqualTo(1);record.put("crossActorRejected",true);record.put("crossSessionRejected",true);record.put("singleUse",true);
                record.put("simulatedUser","ACCEPT_EXACT_DISPLAYED_SCOPE; NOT_HUMAN_EVIDENCE");
            }
            if("MY_LOANS".equals(response.get("intent"))&&"QUERY".equals(response.get("status")))for(var row:(List<Map<String,Object>>)response.get("items"))assertThat(((Number)row.get("id")).longValue()).isEqualTo(actorId==101?own:other);
            record.put("queryTrace",trace());record.put("loanOwners",Map.of(Long.toString(own),101,Long.toString(other),102));record.put("response",response);
            record.put("snapshotUnchanged",snapshot().equals(before));assertThat(record.get("snapshotUnchanged")).isEqualTo(true);
            Files.writeString(output,json.writeValueAsString(record)+"\n",StandardOpenOption.APPEND);
        }
        Files.writeString(Path.of(System.getenv("RESEARCH_NATIVE_SNAPSHOT")),json.writeValueAsString(snapshots));
    }
}

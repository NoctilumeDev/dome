package com.dorm.demo.web;

import com.dorm.demo.domain.*;
import com.dorm.demo.repo.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.util.*;
import java.util.stream.Collectors;

@RestController
public class DemoController {

  private final UserRepository userRepository;
  private final BuildingRepository buildingRepository;
  private final FloorRepository floorRepository;
  private final DormitoryRepository dormitoryRepository;
  private final BedRepository bedRepository;
  private final MoveInApplicationRepository moveInRepository;
  private final MoveOutApplicationRepository moveOutRepository;
  private final RepairRepository repairRepository;
  private final BillRepository billRepository;
  private final NoticeRepository noticeRepository;
  private final PasswordEncoder passwordEncoder;

  public DemoController(
      UserRepository userRepository,
      BuildingRepository buildingRepository,
      FloorRepository floorRepository,
      DormitoryRepository dormitoryRepository,
      BedRepository bedRepository,
      MoveInApplicationRepository moveInRepository,
      MoveOutApplicationRepository moveOutRepository,
      RepairRepository repairRepository,
      BillRepository billRepository,
      NoticeRepository noticeRepository,
      PasswordEncoder passwordEncoder
  ) {
    this.userRepository = userRepository;
    this.buildingRepository = buildingRepository;
    this.floorRepository = floorRepository;
    this.dormitoryRepository = dormitoryRepository;
    this.bedRepository = bedRepository;
    this.moveInRepository = moveInRepository;
    this.moveOutRepository = moveOutRepository;
    this.repairRepository = repairRepository;
    this.billRepository = billRepository;
    this.noticeRepository = noticeRepository;
    this.passwordEncoder = passwordEncoder;
  }

  @PostMapping("/api/auth/login")
  public ResponseEntity<?> login(@RequestBody LoginRequest request, HttpServletRequest httpRequest) {
    if (request == null || request.username == null || request.password == null) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "请填写用户名和密码"));
    }
    String username = request.username.trim();
    String password = request.password;
    if (username.isEmpty() || password.isEmpty()) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "请填写用户名和密码"));
    }
    User user = userRepository.findByUsername(username);
    boolean encodedPassword = user != null && user.getPassword() != null && user.getPassword().startsWith("$2");
    boolean passwordMatches = user != null && (encodedPassword
        ? passwordEncoder.matches(password, user.getPassword())
        : Objects.equals(password, user.getPassword()));
    if (!passwordMatches) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of("message", "用户名或密码错误"));
    }
    if (!encodedPassword) {
      user.setPassword(passwordEncoder.encode(password));
      userRepository.save(user);
    }
    HttpSession session = httpRequest.getSession(true);
    session.setAttribute("uid", user.getId());
    return ResponseEntity.ok(Map.of(
        "id", user.getId(),
        "username", user.getUsername(),
        "fullName", user.getFullName(),
        "role", user.getRole().name()
    ));
  }

  @PostMapping("/api/auth/register")
  public ResponseEntity<?> register(@RequestBody Map<String, String> body) {
    String username = body.getOrDefault("username", "").trim();
    String fullName = body.getOrDefault("fullName", "").trim();
    String password = body.getOrDefault("password", "");

    if (username.isEmpty() || fullName.isEmpty() || password.isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("message", "请完整填写用户名、姓名和密码"));
    }
    if (username.length() < 3 || username.length() > 64) {
      return ResponseEntity.badRequest().body(Map.of("message", "用户名长度应为 3～64 个字符"));
    }
    if (fullName.length() > 64) {
      return ResponseEntity.badRequest().body(Map.of("message", "姓名不能超过 64 个字符"));
    }
    if (password.length() < 6 || password.length() > 32) {
      return ResponseEntity.badRequest().body(Map.of("message", "密码长度应为 6～32 个字符"));
    }
    if (userRepository.findByUsername(username) != null) {
      return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", "用户名已存在"));
    }

    User user = new User();
    user.setUsername(username);
    user.setFullName(fullName);
    user.setPassword(passwordEncoder.encode(password));
    user.setRole(UserRole.STUDENT);
    userRepository.save(user);
    return ResponseEntity.ok(Map.of("message", "注册成功，请使用新账号登录"));
  }

  @PostMapping("/api/auth/logout")
  public ResponseEntity<?> logout(HttpServletRequest request) {
    HttpSession session = request.getSession(false);
    if (session != null) {
      session.invalidate();
    }
    return ResponseEntity.ok(Map.of("message", "已退出"));
  }

  @GetMapping("/api/auth/me")
  public ResponseEntity<?> currentUser(HttpServletRequest request) {
    User me = current(request);
    return ResponseEntity.ok(Map.of(
        "id", me.getId(),
        "username", me.getUsername(),
        "fullName", me.getFullName(),
        "role", me.getRole().name()
    ));
  }

  @GetMapping("/api/users")
  public List<Map<String, Object>> users(@RequestParam(required = false) String role, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    if (me.getRole() == UserRole.DORM_MANAGER) {
      return userRepository.findByRole(UserRole.STUDENT).stream()
          .map(this::userToMap).collect(Collectors.toList());
    }
    if (role == null || role.isBlank()) {
      return userRepository.findAll().stream().map(this::userToMap).collect(Collectors.toList());
    }
    return userRepository.findByRole(UserRole.valueOf(role.toUpperCase()))
        .stream().map(this::userToMap).collect(Collectors.toList());
  }

  @PostMapping("/api/users")
  public ResponseEntity<?> addUser(@RequestBody User user, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN);
    if (user.getUsername() == null || user.getUsername().trim().isEmpty()
        || user.getPassword() == null || user.getPassword().isEmpty()
        || user.getFullName() == null || user.getFullName().trim().isEmpty()
        || user.getRole() == null) {
      return ResponseEntity.badRequest().body(Map.of("message", "用户名、密码、姓名和角色不能为空"));
    }
    user.setUsername(user.getUsername().trim());
    user.setFullName(user.getFullName().trim());
    if (userRepository.findByUsername(user.getUsername()) != null) {
      return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", "用户名已存在"));
    }
    user.setId(null);
    user.setPassword(passwordEncoder.encode(user.getPassword()));
    userRepository.save(user);
    return ResponseEntity.ok(Map.of("message", "用户新增成功"));
  }

  @GetMapping("/api/buildings")
  public List<Map<String, Object>> buildings(HttpServletRequest request) {
    current(request);
    return buildingRepository.findAll().stream().map(this::buildingToMap).collect(Collectors.toList());
  }

  @PostMapping("/api/buildings")
  public ResponseEntity<?> addBuilding(@RequestBody Building building, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    buildingRepository.save(building);
    return ResponseEntity.ok(Map.of("message", "宿舍楼添加成功"));
  }

  @PutMapping("/api/buildings/{id}")
  public ResponseEntity<?> updateBuilding(@PathVariable Long id, @RequestBody Map<String, String> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    Building building = buildingRepository.findById(id).orElseThrow(() -> new RuntimeException("宿舍楼不存在"));
    String name = body.get("name");
    String address = body.get("address");
    if (name != null && !name.trim().isEmpty()) {
      building.setName(name.trim());
    }
    if (address != null && !address.trim().isEmpty()) {
      building.setAddress(address.trim());
    }
    buildingRepository.save(building);
    return ResponseEntity.ok(Map.of("message", "宿舍楼更新成功"));
  }

  @DeleteMapping("/api/buildings/{id}")
  public ResponseEntity<?> deleteBuilding(@PathVariable Long id, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    if (!buildingRepository.existsById(id)) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "宿舍楼不存在"));
    }
    if (floorRepository.countByBuildingId(id) > 0) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "请先清空该楼栋下的楼层，再删除楼栋"));
    }
    buildingRepository.deleteById(id);
    return ResponseEntity.ok(Map.of("message", "宿舍楼删除成功"));
  }

  @GetMapping("/api/floors")
  public List<Map<String, Object>> floors(@RequestParam(required = false) Long buildingId, HttpServletRequest request) {
    current(request);
    if (buildingId == null) {
      return floorRepository.findAll().stream().map(this::floorToMap).collect(Collectors.toList());
    }
    return floorRepository.findByBuildingId(buildingId).stream().map(this::floorToMap).collect(Collectors.toList());
  }

  @PostMapping("/api/floors")
  public ResponseEntity<?> addFloor(@RequestBody Floor floor, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    floorRepository.save(floor);
    return ResponseEntity.ok(Map.of("message", "楼层添加成功"));
  }

  @PutMapping("/api/floors/{id}")
  public ResponseEntity<?> updateFloor(@PathVariable Long id, @RequestBody Map<String, String> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    Floor floor = floorRepository.findById(id).orElseThrow(() -> new RuntimeException("楼层不存在"));
    if (body.get("name") != null && !body.get("name").toString().trim().isEmpty()) {
      floor.setName(body.get("name").toString().trim());
    }
    if (body.get("buildingId") != null && !body.get("buildingId").toString().trim().isEmpty()) {
      Long buildingId = Long.valueOf(body.get("buildingId").toString());
      floor.setBuilding(buildingRepository.findById(buildingId).orElseThrow(() -> new RuntimeException("楼栋不存在")));
    }
    floorRepository.save(floor);
    return ResponseEntity.ok(Map.of("message", "楼层更新成功"));
  }

  @DeleteMapping("/api/floors/{id}")
  public ResponseEntity<?> deleteFloor(@PathVariable Long id, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    if (!floorRepository.existsById(id)) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "楼层不存在"));
    }
    if (dormitoryRepository.countByFloorId(id) > 0) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "请先清空该楼层下的宿舍，再删除楼层"));
    }
    floorRepository.deleteById(id);
    return ResponseEntity.ok(Map.of("message", "楼层删除成功"));
  }

  @GetMapping("/api/dormitories")
  public List<Map<String, Object>> dormitories(@RequestParam(required = false) Long buildingId, HttpServletRequest request) {
    current(request);
    if (buildingId == null) {
      return dormitoryRepository.findAll().stream().map(this::dormitoryToMap).collect(Collectors.toList());
    }
    return dormitoryRepository.findByBuildingId(buildingId).stream().map(this::dormitoryToMap).collect(Collectors.toList());
  }

  @PostMapping("/api/dormitories/recommend")
  public ResponseEntity<?> recommendDormitories(@RequestBody Map<String, String> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.STUDENT);
    String atmosphere = preferenceValue(body, "atmosphere", "安静", "活跃");
    String sleepHabit = preferenceValue(body, "sleepHabit", "早睡", "正常", "晚睡");
    String cleanliness = preferenceValue(body, "cleanliness", "整洁", "一般");
    String hobby = preferenceValue(body, "hobby", "阅读", "运动", "游戏", "音乐");
    String studentTags = String.join(",", atmosphere, sleepHabit, cleanliness, hobby);

    List<Map<String, Object>> recommendations = new ArrayList<>();
    for (Dormitory dormitory : dormitoryRepository.findAll()) {
      long vacantBeds = bedRepository.countByDormitoryIdAndStatus(dormitory.getId(), BedState.VACANT);
      if (vacantBeds == 0) {
        continue;
      }

      String dormPreferenceTags = normalizePreferenceTags(dormitory.getPreferenceTags());
      Set<String> dormTags = new HashSet<>(Arrays.asList(dormPreferenceTags.split(",")));
      List<String> matchedTags = new ArrayList<>();
      int score = Math.min((int) vacantBeds, 3) * 5;
      if (dormTags.contains(atmosphere)) {
        score += 30;
        matchedTags.add(atmosphere);
      }
      if (dormTags.contains(sleepHabit)) {
        score += 25;
        matchedTags.add(sleepHabit);
      }
      if (dormTags.contains(cleanliness)) {
        score += 20;
        matchedTags.add(cleanliness);
      }
      if (dormTags.contains(hobby)) {
        score += 10;
        matchedTags.add(hobby);
      }

      Map<String, Object> item = new HashMap<>();
      item.put("id", dormitory.getId());
      item.put("dormCode", dormitory.getDormCode());
      item.put("building", dormitory.getBuilding().getName());
      item.put("floor", dormitory.getFloor().getName());
      item.put("preferenceTags", dormPreferenceTags);
      item.put("vacantBeds", vacantBeds);
      item.put("score", score);
      item.put("reason", matchedTags.isEmpty()
          ? "当前有" + vacantBeds + "张空床"
          : "匹配" + String.join("、", matchedTags) + "；当前有" + vacantBeds + "张空床");
      recommendations.add(item);
    }

    recommendations.sort((left, right) -> {
      int byScore = Integer.compare((Integer) right.get("score"), (Integer) left.get("score"));
      return byScore != 0 ? byScore : Long.compare((Long) left.get("id"), (Long) right.get("id"));
    });
    List<Map<String, Object>> topThree = recommendations.stream().limit(3).collect(Collectors.toList());
    return ResponseEntity.ok(Map.of(
        "preferenceTags", studentTags,
        "recommendations", topThree,
        "message", topThree.isEmpty() ? "当前没有可推荐的空床宿舍" : "推荐仅供参考，请按自己的意愿选择"
    ));
  }

  @PostMapping("/api/dormitories")
  public ResponseEntity<?> addDorm(@RequestBody Dormitory dormitory, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    String preferenceTags = normalizePreferenceTags(dormitory.getPreferenceTags());
    dormitory.setPreferenceTags(preferenceTags.isEmpty() ? "安静,正常,一般,阅读" : preferenceTags);
    dormitoryRepository.save(dormitory);
    return ResponseEntity.ok(Map.of("message", "宿舍添加成功"));
  }

  @PutMapping("/api/dormitories/{id}")
  public ResponseEntity<?> updateDorm(@PathVariable Long id, @RequestBody Map<String, String> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    Dormitory dorm = dormitoryRepository.findById(id).orElseThrow(() -> new RuntimeException("宿舍不存在"));
    if (body.get("dormCode") != null && !body.get("dormCode").toString().trim().isEmpty()) {
      dorm.setDormCode(body.get("dormCode").toString().trim());
    }
    if (body.get("buildingId") != null && !body.get("buildingId").toString().trim().isEmpty()) {
      dorm.setBuilding(buildingRepository.findById(Long.valueOf(body.get("buildingId").toString())).orElseThrow(() -> new RuntimeException("楼栋不存在")));
    }
    if (body.get("floorId") != null && !body.get("floorId").toString().trim().isEmpty()) {
      dorm.setFloor(floorRepository.findById(Long.valueOf(body.get("floorId").toString())).orElseThrow(() -> new RuntimeException("楼层不存在")));
    }
    if (body.get("capacity") != null && !body.get("capacity").toString().trim().isEmpty()) {
      dorm.setCapacity(Integer.valueOf(body.get("capacity").toString()));
    }
    if (body.get("preferenceTags") != null && !body.get("preferenceTags").toString().trim().isEmpty()) {
      dorm.setPreferenceTags(normalizePreferenceTags(body.get("preferenceTags")));
    }
    dormitoryRepository.save(dorm);
    return ResponseEntity.ok(Map.of("message", "宿舍更新成功"));
  }

  @DeleteMapping("/api/dormitories/{id}")
  public ResponseEntity<?> deleteDorm(@PathVariable Long id, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN);
    if (!dormitoryRepository.existsById(id)) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "宿舍不存在"));
    }
    if (bedRepository.countByDormitoryId(id) > 0) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "请先清空该宿舍下的床位，再删除宿舍"));
    }
    dormitoryRepository.deleteById(id);
    return ResponseEntity.ok(Map.of("message", "宿舍删除成功"));
  }

  @GetMapping("/api/beds")
  public List<Map<String, Object>> beds(@RequestParam(required = false) Long dormitoryId,
                                       @RequestParam(required = false) Long buildingId,
                                       HttpServletRequest request) {
    User me = current(request);
    List<Bed> beds;
    if (dormitoryId != null) {
      beds = bedRepository.findByDormitoryId(dormitoryId);
    } else if (buildingId != null) {
      beds = bedRepository.findByDormitoryBuildingId(buildingId);
    } else {
      beds = bedRepository.findAll();
    }

    return beds.stream().map(b -> {
      Map<String, Object> item = new HashMap<>();
      item.put("id", b.getId());
      item.put("bedNo", b.getBedNo());
      item.put("status", b.getStatus().name());
      item.put("notes", b.getNotes());
      item.put("dormitoryId", b.getDormitory().getId());
      item.put("dormitory", b.getDormitory().getDormCode());
      boolean canSeeOccupant = b.getOccupant() != null && (me.getRole() != UserRole.STUDENT
          || b.getOccupant().getId().equals(me.getId()));
      item.put("occupantId", canSeeOccupant ? b.getOccupant().getId() : null);
      item.put("occupantName", canSeeOccupant ? b.getOccupant().getFullName() : null);
      return item;
    }).collect(Collectors.toList());
  }

  @PostMapping("/api/beds")
  public ResponseEntity<?> addBed(@RequestBody Map<String, Object> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN, UserRole.DORM_MANAGER);
    if (body.get("dormitoryId") == null || body.get("bedNo") == null
        || body.get("bedNo").toString().trim().isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("message", "请选择宿舍并填写床位号"));
    }
    Long dormId = Long.valueOf(body.get("dormitoryId").toString());
    String bedNo = body.get("bedNo").toString().trim();
    if (bedRepository.existsByDormitoryIdAndBedNo(dormId, bedNo)) {
      return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", "该宿舍已存在同名床位"));
    }
    Bed bed = new Bed();
    bed.setDormitory(dormitoryRepository.findById(dormId).orElseThrow(() -> new RuntimeException("宿舍不存在")));
    bed.setBedNo(bedNo);
    bed.setStatus(BedState.VACANT);
    bedRepository.save(bed);
    return ResponseEntity.ok(Map.of("message", "床位创建成功"));
  }

  @PutMapping("/api/beds/{id}")
  public ResponseEntity<?> updateBed(@PathVariable Long id, @RequestBody Map<String, String> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN, UserRole.DORM_MANAGER);
    Bed bed = bedRepository.findById(id).orElseThrow(() -> new RuntimeException("床位不存在"));
    String nextBedNo = body.get("bedNo") != null && !body.get("bedNo").trim().isEmpty()
        ? body.get("bedNo").trim() : bed.getBedNo();
    Dormitory nextDormitory = bed.getDormitory();
    if (body.get("dormitoryId") != null && !body.get("dormitoryId").toString().trim().isEmpty()) {
      nextDormitory = dormitoryRepository.findById(Long.valueOf(body.get("dormitoryId").toString()))
          .orElseThrow(() -> new RuntimeException("宿舍不存在"));
    }
    Optional<Bed> duplicate = bedRepository.findByDormitoryIdAndBedNo(nextDormitory.getId(), nextBedNo);
    if (duplicate.isPresent() && !duplicate.get().getId().equals(id)) {
      return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", "该宿舍已存在同名床位"));
    }
    bed.setBedNo(nextBedNo);
    bed.setDormitory(nextDormitory);
    if (body.get("status") != null && !body.get("status").toString().trim().isEmpty()) {
      bed.setStatus(BedState.valueOf(body.get("status").toString().trim().toUpperCase()));
    }
    bedRepository.save(bed);
    return ResponseEntity.ok(Map.of("message", "床位更新成功"));
  }

  @DeleteMapping("/api/beds/{id}")
  public ResponseEntity<?> deleteBed(@PathVariable Long id, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN, UserRole.DORM_MANAGER);
    Bed bed = bedRepository.findById(id).orElseThrow(() -> new RuntimeException("床位不存在"));
    if (bed.getOccupant() != null) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "床位有入住学生，无法删除"));
    }
    if (moveInRepository.existsByAssignedBed_Id(id)) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "床位曾用于入住申请历史，无法删除"));
    }
    if (moveOutRepository.existsByBed_Id(id)) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", "床位已有退宿历史，无法删除"));
    }
    bedRepository.deleteById(id);
    return ResponseEntity.ok(Map.of("message", "床位删除成功"));
  }

  @PatchMapping("/api/beds/{bedId}/state")
  public ResponseEntity<?> updateBedState(@PathVariable Long bedId, @RequestBody Map<String, String> body, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    Bed bed = bedRepository.findById(bedId).orElseThrow(() -> new RuntimeException("床位不存在"));
    BedState status = BedState.valueOf(body.get("status").toString().toUpperCase());
    if (status == BedState.MAINTENANCE && bed.getOccupant() != null) {
      return ResponseEntity.badRequest().body(Map.of("message", "床位有入住学生，请先腾退后再设置为维修中"));
    }
    bed.setStatus(status);
    if (status == BedState.VACANT || status == BedState.MAINTENANCE) {
      bed.setOccupant(null);
    }
    bedRepository.save(bed);
    return ResponseEntity.ok(Map.of("message", "床位状态更新成功"));
  }

  @PatchMapping("/api/beds/{bedId}/occupy")
  public ResponseEntity<?> occupyBed(@PathVariable Long bedId, @RequestBody Map<String, Long> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN, UserRole.DORM_MANAGER);
    Bed bed = bedRepository.findById(bedId).orElseThrow(() -> new RuntimeException("床位不存在"));
    if (bed.getStatus() != BedState.VACANT) {
      return ResponseEntity.badRequest().body(Map.of("message", "该床位当前不可分配（状态：" + bed.getStatus() + "）"));
    }
    User student = userRepository.findById(body.get("studentId")).orElseThrow(() -> new RuntimeException("学生不存在"));
    if (student.getRole() != UserRole.STUDENT) {
      return ResponseEntity.badRequest().body(Map.of("message", "只能分配给学生"));
    }
    if (bedRepository.existsByOccupantId(student.getId())) {
      return ResponseEntity.badRequest().body(Map.of("message", "该学生已经有床位"));
    }
    int updated = bedRepository.occupyIfVacant(bedId, student, BedState.OCCUPIED, BedState.VACANT);
    if (updated == 0) {
      return ResponseEntity.badRequest().body(Map.of("message", "该床位已被其他管理员占用"));
    }
    return ResponseEntity.ok(Map.of("message", "分配成功"));
  }

  @PatchMapping("/api/beds/{bedId}/release")
  public ResponseEntity<?> releaseBed(@PathVariable Long bedId, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN, UserRole.DORM_MANAGER);
    Bed bed = bedRepository.findById(bedId).orElseThrow(() -> new RuntimeException("床位不存在"));
    bed.setStatus(BedState.VACANT);
    bed.setOccupant(null);
    bedRepository.save(bed);
    return ResponseEntity.ok(Map.of("message", "腾退成功"));
  }

  @PostMapping("/api/move-in")
  public ResponseEntity<?> submitMoveIn(@RequestBody Map<String, Object> body, HttpServletRequest request) {
    User me = current(request);
    if (me.getRole() != UserRole.STUDENT) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "只有学生可提交入住申请"));
    }
    if (bedRepository.existsByOccupantId(me.getId())) {
      return ResponseEntity.badRequest().body(Map.of("message", "你已经有床位，无需重复申请入住"));
    }
    if (moveInRepository.existsByStudentIdAndStatus(me.getId(), ProcessState.PENDING)) {
      return ResponseEntity.badRequest().body(Map.of("message", "你已有待审核的入住申请"));
    }
    String reason = body.getOrDefault("reason", "").toString().trim();
    if (reason.isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("message", "请填写入住原因"));
    }
    MoveInApplication app = new MoveInApplication();
    app.setStudent(me);
    app.setReason(reason);
    if (body.get("preferredDormitoryId") != null) {
      Long did = Long.valueOf(body.get("preferredDormitoryId").toString());
      app.setPreferredDormitory(dormitoryRepository.findById(did)
          .orElseThrow(() -> new RuntimeException("意向宿舍不存在")));
    }
    String preferenceTags = normalizePreferenceTags(body.get("preferenceTags"));
    if (!preferenceTags.isEmpty()) {
      app.setPreferenceTags(preferenceTags);
    }
    app.setStatus(ProcessState.PENDING);
    app.setApplyTime(LocalDateTime.now());
    moveInRepository.save(app);
    return ResponseEntity.ok(Map.of("message", "入住申请提交成功"));
  }

  @GetMapping("/api/move-in")
  public List<Map<String, Object>> moveInList(@RequestParam(required = false) Long studentId, HttpServletRequest request) {
    User me = current(request);
    if (me.getRole() == UserRole.STUDENT) {
      return moveInRepository.findByStudentId(me.getId()).stream().map(this::moveInToMap).collect(Collectors.toList());
    }
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    if (studentId != null) {
      return moveInRepository.findByStudentId(studentId).stream().map(this::moveInToMap).collect(Collectors.toList());
    }
    return moveInRepository.findAll().stream().map(this::moveInToMap).collect(Collectors.toList());
  }

  @PatchMapping("/api/move-in/{id}/approve")
  @Transactional
  public ResponseEntity<?> approveMoveIn(@PathVariable Long id, @RequestBody(required = false) Map<String, Object> body, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    MoveInApplication app = moveInRepository.findById(id).orElseThrow(() -> new RuntimeException("申请不存在"));
    if (app.getStatus() != ProcessState.PENDING) {
      return ResponseEntity.badRequest().body(Map.of("message", "该申请已处理"));
    }
    if (bedRepository.existsByOccupantId(app.getStudent().getId())) {
      return ResponseEntity.badRequest().body(Map.of("message", "该学生已经有床位"));
    }
    Bed bed = null;
    if (body != null && body.get("bedId") != null) {
      bed = bedRepository.findById(Long.valueOf(body.get("bedId").toString())).orElse(null);
    } else if (app.getPreferredDormitory() != null) {
      bed = bedRepository.findFirstByDormitoryIdAndStatus(app.getPreferredDormitory().getId(), BedState.VACANT).orElse(null);
    }
    if (bed == null) {
      bed = bedRepository.findFirstByStatusOrderById(BedState.VACANT).orElse(null);
    }
    if (bed == null) {
      return ResponseEntity.badRequest().body(Map.of("message", "无可用空床位"));
    }
    int updated = bedRepository.occupyIfVacant(bed.getId(), app.getStudent(), BedState.OCCUPIED, BedState.VACANT);
    if (updated == 0) {
      return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", "该床位刚被占用，请刷新后重试"));
    }
    app.setAssignedBed(bed);
    app.setStatus(ProcessState.APPROVED);
    app.setApprover(me);
    app.setProcessTime(LocalDateTime.now());
    app.setComment("自动通过/管理员审核通过");
    moveInRepository.save(app);
    return ResponseEntity.ok(Map.of("message", "入住申请已通过"));
  }

  @PatchMapping("/api/move-in/{id}/reject")
  public ResponseEntity<?> rejectMoveIn(@PathVariable Long id, @RequestBody(required = false) Map<String, String> body, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    MoveInApplication app = moveInRepository.findById(id).orElseThrow(() -> new RuntimeException("申请不存在"));
    if (app.getStatus() != ProcessState.PENDING) {
      return ResponseEntity.badRequest().body(Map.of("message", "该申请已处理"));
    }
    app.setStatus(ProcessState.REJECTED);
    app.setApprover(me);
    app.setProcessTime(LocalDateTime.now());
    app.setComment(body != null ? body.getOrDefault("comment", "驳回") : "驳回");
    moveInRepository.save(app);
    return ResponseEntity.ok(Map.of("message", "入住申请已驳回"));
  }

  @PostMapping("/api/move-out")
  public ResponseEntity<?> submitMoveOut(@RequestBody Map<String, Object> body, HttpServletRequest request) {
    User me = current(request);
    if (me.getRole() != UserRole.STUDENT) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "只有学生可提交退宿申请"));
    }
    if (body.get("bedId") == null) {
      return ResponseEntity.badRequest().body(Map.of("message", "当前没有可退宿的床位"));
    }
    String reason = body.getOrDefault("reason", "").toString().trim();
    if (reason.isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("message", "请填写退宿原因"));
    }
    MoveOutApplication app = new MoveOutApplication();
    app.setStudent(me);
    app.setReason(reason);
    Long bedId = Long.valueOf(body.get("bedId").toString());
    Bed bed = bedRepository.findById(bedId).orElseThrow(() -> new RuntimeException("床位不存在"));
    if (bed.getOccupant() == null || !bed.getOccupant().getId().equals(me.getId())) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "只能申请退掉自己的床位"));
    }
    if (moveOutRepository.existsByStudentIdAndStatus(me.getId(), ProcessState.PENDING)) {
      return ResponseEntity.badRequest().body(Map.of("message", "你已有待审核的退宿申请"));
    }
    app.setBed(bed);
    app.setStatus(ProcessState.PENDING);
    app.setApplyTime(LocalDateTime.now());
    moveOutRepository.save(app);
    return ResponseEntity.ok(Map.of("message", "退宿申请提交成功"));
  }

  @GetMapping("/api/move-out")
  public List<Map<String, Object>> moveOutList(@RequestParam(required = false) Long studentId, HttpServletRequest request) {
    User me = current(request);
    if (me.getRole() == UserRole.STUDENT) {
      return moveOutRepository.findByStudentId(me.getId()).stream().map(this::moveOutToMap).collect(Collectors.toList());
    }
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    if (studentId == null) {
      return moveOutRepository.findAll().stream().map(this::moveOutToMap).collect(Collectors.toList());
    }
    return moveOutRepository.findByStudentId(studentId).stream().map(this::moveOutToMap).collect(Collectors.toList());
  }

  @PatchMapping("/api/move-out/{id}/approve")
  @Transactional
  public ResponseEntity<?> approveMoveOut(@PathVariable Long id, @RequestBody(required = false) Map<String, String> body, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    MoveOutApplication app = moveOutRepository.findById(id).orElseThrow(() -> new RuntimeException("申请不存在"));
    if (app.getStatus() != ProcessState.PENDING) {
      return ResponseEntity.badRequest().body(Map.of("message", "该申请已处理"));
    }
    Bed bed = app.getBed();
    if (bed.getOccupant() == null || !bed.getOccupant().getId().equals(app.getStudent().getId())) {
      return ResponseEntity.badRequest().body(Map.of("message", "该学生已不在此床位，请刷新后处理"));
    }
    app.setStatus(ProcessState.APPROVED);
    app.setApprover(me);
    app.setProcessTime(LocalDateTime.now());
    app.setComment(body != null ? body.getOrDefault("comment", "审核通过") : "审核通过");
    bed.setStatus(BedState.VACANT);
    bed.setOccupant(null);
    bedRepository.save(bed);
    moveOutRepository.save(app);
    return ResponseEntity.ok(Map.of("message", "退宿申请通过，已清空床位"));
  }

  @PatchMapping("/api/move-out/{id}/reject")
  public ResponseEntity<?> rejectMoveOut(@PathVariable Long id, @RequestBody(required = false) Map<String, String> body, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    MoveOutApplication app = moveOutRepository.findById(id).orElseThrow(() -> new RuntimeException("申请不存在"));
    if (app.getStatus() != ProcessState.PENDING) {
      return ResponseEntity.badRequest().body(Map.of("message", "该申请已处理"));
    }
    app.setStatus(ProcessState.REJECTED);
    app.setApprover(me);
    app.setProcessTime(LocalDateTime.now());
    app.setComment(body != null ? body.getOrDefault("comment", "驳回") : "驳回");
    moveOutRepository.save(app);
    return ResponseEntity.ok(Map.of("message", "退宿申请驳回"));
  }

  @PostMapping("/api/repairs")
  public ResponseEntity<?> submitRepair(@RequestBody Map<String, String> body, HttpServletRequest request) {
    User me = current(request);
    if (me.getRole() != UserRole.STUDENT) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "只有学生可提交报修"));
    }
    String location = body.getOrDefault("location", "").trim();
    String description = body.getOrDefault("description", "").trim();
    if (location.isEmpty() || description.isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("message", "请填写报修位置和故障描述"));
    }
    Repair repair = new Repair();
    repair.setStudent(me);
    repair.setLocation(location);
    repair.setDescription(description);
    repair.setStatus(RepairState.PENDING);
    repair.setCreateTime(LocalDateTime.now());
    repairRepository.save(repair);
    return ResponseEntity.ok(Map.of("message", "报修提交成功"));
  }

  @GetMapping("/api/repairs")
  public List<Map<String, Object>> repairs(@RequestParam(required = false) String status, HttpServletRequest request) {
    User me = current(request);
    if (me.getRole() == UserRole.STUDENT) {
      return repairRepository.findByStudentId(me.getId()).stream().map(this::repairToMap).collect(Collectors.toList());
    }
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    if (status == null || status.isBlank()) {
      return repairRepository.findAll().stream().map(this::repairToMap).collect(Collectors.toList());
    }
    return repairRepository.findByStatus(RepairState.valueOf(status.toUpperCase())).stream().map(this::repairToMap).collect(Collectors.toList());
  }

  @PatchMapping("/api/repairs/{id}/process")
  public ResponseEntity<?> processRepair(@PathVariable Long id, @RequestBody Map<String, String> body, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    Repair repair = repairRepository.findById(id).orElseThrow(() -> new RuntimeException("报修不存在"));
    RepairState nextStatus = RepairState.valueOf(body.get("status").toUpperCase());
    boolean validTransition = (repair.getStatus() == RepairState.PENDING && nextStatus == RepairState.PROCESSING)
        || (repair.getStatus() == RepairState.PROCESSING && nextStatus == RepairState.DONE);
    if (!validTransition) {
      return ResponseEntity.badRequest().body(Map.of("message", "请按待处理、处理中、已完成的顺序操作"));
    }
    repair.setStatus(nextStatus);
    repair.setHandler(me);
    repair.setComment(body.getOrDefault("comment", ""));
    repair.setHandleTime(LocalDateTime.now());
    repairRepository.save(repair);
    return ResponseEntity.ok(Map.of("message", "报修状态更新成功"));
  }

  @PostMapping("/api/bills")
  public ResponseEntity<?> addBill(@RequestBody Map<String, String> body, HttpServletRequest request) {
    requireRoles(current(request), UserRole.ADMIN, UserRole.DORM_MANAGER);
    if (body.get("studentId") == null || body.get("month") == null) {
      return ResponseEntity.badRequest().body(Map.of("message", "请选择学生并填写账单月份"));
    }
    User student = userRepository.findById(Long.valueOf(body.get("studentId")))
        .orElseThrow(() -> new RuntimeException("学生不存在"));
    if (student.getRole() != UserRole.STUDENT) {
      return ResponseEntity.badRequest().body(Map.of("message", "账单只能录入给学生"));
    }
    String month = body.get("month").trim();
    try {
      YearMonth.parse(month);
    } catch (Exception e) {
      return ResponseEntity.badRequest().body(Map.of("message", "账单月份格式应为 YYYY-MM"));
    }
    BigDecimal water;
    BigDecimal electricity;
    BigDecimal otherFee;
    try {
      water = new BigDecimal(body.getOrDefault("water", "0"));
      electricity = new BigDecimal(body.getOrDefault("electricity", "0"));
      otherFee = new BigDecimal(body.getOrDefault("otherFee", "0"));
    } catch (NumberFormatException e) {
      return ResponseEntity.badRequest().body(Map.of("message", "费用应填写数字"));
    }
    if (water.signum() < 0 || electricity.signum() < 0 || otherFee.signum() < 0) {
      return ResponseEntity.badRequest().body(Map.of("message", "费用不能为负数"));
    }
    Bill bill = new Bill();
    bill.setStudent(student);
    bill.setMonth(month);
    bill.setRecordDate(LocalDate.now());
    bill.setWater(water);
    bill.setElectricity(electricity);
    bill.setOtherFee(otherFee);
    bill.setTotal(bill.getWater().add(bill.getElectricity()).add(bill.getOtherFee()));
    bill.setState(BillState.UNPAID);
    billRepository.save(bill);
    return ResponseEntity.ok(Map.of("message", "账单创建成功"));
  }

  @GetMapping("/api/bills")
  public List<Map<String, Object>> bills(@RequestParam(required = false) Long studentId, HttpServletRequest request) {
    List<Bill> bills;
    User me = current(request);
    if (me.getRole() == UserRole.STUDENT) {
      bills = billRepository.findByStudentId(me.getId());
    } else if (studentId != null) {
      requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
      bills = billRepository.findByStudentId(studentId);
    } else {
      requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
      bills = billRepository.findAll();
    }
    return bills.stream().map(b -> {
      Map<String, Object> item = new HashMap<>();
      item.put("id", b.getId());
      item.put("studentId", b.getStudent().getId());
      item.put("studentName", b.getStudent().getFullName());
      item.put("month", b.getMonth());
      item.put("electricity", b.getElectricity());
      item.put("water", b.getWater());
      item.put("otherFee", b.getOtherFee());
      item.put("total", b.getTotal());
      item.put("recordDate", b.getRecordDate());
      item.put("state", b.getState().name());
      return item;
    }).collect(Collectors.toList());
  }

  @PatchMapping("/api/bills/{id}/pay")
  public ResponseEntity<?> payBill(@PathVariable Long id, HttpServletRequest request) {
    User me = current(request);
    Bill bill = billRepository.findById(id).orElseThrow(() -> new RuntimeException("账单不存在"));
    if (me.getRole() == UserRole.STUDENT && !bill.getStudent().getId().equals(me.getId())) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "只能操作自己账单"));
    }
    if (bill.getState() == BillState.PAID) {
      return ResponseEntity.badRequest().body(Map.of("message", "该账单已经缴费"));
    }
    bill.setState(BillState.PAID);
    billRepository.save(bill);
    return ResponseEntity.ok(Map.of("message", "账单已缴费"));
  }

  @GetMapping("/api/notices")
  public List<Map<String, Object>> notices(HttpServletRequest request) {
    User me = current(request);
    Long userBuildingId = me.getBuilding() != null ? me.getBuilding().getId() : null;
    if (me.getRole() == UserRole.STUDENT) {
      userBuildingId = bedRepository.findByOccupantId(me.getId())
          .map(bed -> bed.getDormitory().getBuilding().getId())
          .orElse(null);
    }
    Long visibleBuildingId = userBuildingId;
    List<Notice> notices = noticeRepository.findAll();
    return notices.stream().filter(n -> {
      if (me.getRole() == UserRole.ADMIN) {
        return true;
      }
      if (n.getScope() == NoticeScope.ALL) {
        return true;
      }
      if (n.getBuilding() == null || visibleBuildingId == null) {
        return false;
      }
      return n.getBuilding().getId().equals(visibleBuildingId);
    }).map(this::noticeToMap).collect(Collectors.toList());
  }

  @PostMapping("/api/notices")
  public ResponseEntity<?> addNotice(@RequestBody Map<String, String> body, HttpServletRequest request) {
    User me = current(request);
    requireRoles(me, UserRole.ADMIN, UserRole.DORM_MANAGER);
    String title = body.getOrDefault("title", "").trim();
    String content = body.getOrDefault("content", "").trim();
    if (title.isEmpty() || content.isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("message", "请填写公告标题和内容"));
    }
    NoticeScope scope = NoticeScope.valueOf(body.getOrDefault("scope", "ALL").toUpperCase());
    Notice notice = new Notice();
    notice.setTitle(title);
    notice.setContent(content);
    notice.setScope(scope);
    notice.setAuthor(me);
    notice.setCreateTime(LocalDateTime.now());
    if (scope == NoticeScope.BUILDING) {
      if (body.get("buildingId") == null || body.get("buildingId").isBlank()) {
        return ResponseEntity.badRequest().body(Map.of("message", "请选择公告楼栋"));
      }
      Building building = buildingRepository.findById(Long.valueOf(body.get("buildingId")))
          .orElseThrow(() -> new RuntimeException("楼栋不存在"));
      if (me.getRole() == UserRole.DORM_MANAGER
          && (me.getBuilding() == null || !me.getBuilding().getId().equals(building.getId()))) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "只能发布本楼栋公告"));
      }
      notice.setBuilding(building);
    }
    noticeRepository.save(notice);
    return ResponseEntity.ok(Map.of("message", "公告发布成功"));
  }

  @GetMapping("/api/dashboard")
  public Map<String, Object> dashboard(HttpServletRequest request) {
    current(request);
    YearMonth currentMonth = YearMonth.now();
    long totalBeds = bedRepository.count();
    long occupied = bedRepository.countByStatus(BedState.OCCUPIED);
    long vacant = bedRepository.countByStatus(BedState.VACANT);
    long maintenance = bedRepository.countByStatus(BedState.MAINTENANCE);
    long pendingMoveIn = moveInRepository.findByStatus(ProcessState.PENDING).size();
    long pendingMoveOut = moveOutRepository.findByStatus(ProcessState.PENDING).size();
    long pendingRepair = repairRepository.findByStatus(RepairState.PENDING).size();
    long monthlyMoveIn = moveInRepository.findAll().stream()
        .filter(app -> app.getApplyTime() != null && YearMonth.from(app.getApplyTime()).equals(currentMonth))
        .count();
    long monthlyMoveOut = moveOutRepository.findAll().stream()
        .filter(app -> app.getApplyTime() != null && YearMonth.from(app.getApplyTime()).equals(currentMonth))
        .count();

    List<Map<String, Object>> buildingStats = buildingRepository.findAll().stream().map(b -> {
      long used = bedRepository.countByDormitoryBuildingIdAndStatus(b.getId(), BedState.OCCUPIED);
      long total = bedRepository.countByDormitoryBuildingId(b.getId());
      Map<String, Object> item = new HashMap<>();
      item.put("buildingId", b.getId());
      item.put("building", b.getName());
      item.put("totalBeds", total);
      item.put("occupiedBeds", used);
      item.put("occupancyRate", total == 0 ? 0 : Math.round((double) used / total * 10000d) / 100d);
      return item;
    }).collect(Collectors.toList());

    Map<String, Object> result = new HashMap<>();
    result.put("totalBeds", totalBeds);
    result.put("occupiedBeds", occupied);
    result.put("vacantBeds", vacant);
    result.put("maintenanceBeds", maintenance);
    result.put("occupancyRate", totalBeds == 0 ? 0 : Math.round((double) occupied / totalBeds * 10000d) / 100d);
    result.put("pendingMoveIn", pendingMoveIn);
    result.put("pendingMoveOut", pendingMoveOut);
    result.put("pendingRepair", pendingRepair);
    result.put("monthlyMoveIn", monthlyMoveIn);
    result.put("monthlyMoveOut", monthlyMoveOut);
    result.put("buildingStats", buildingStats);
    return result;
  }

  private User current(HttpServletRequest request) {
    HttpSession session = request.getSession(false);
    if (session == null || session.getAttribute("uid") == null) {
      throw new RuntimeException("未登录");
    }
    Long uid = (Long) session.getAttribute("uid");
    return userRepository.findById(uid).orElseThrow(() -> new RuntimeException("无效会话"));
  }

  private void requireRoles(User user, UserRole... roles) {
    for (UserRole role : roles) {
      if (user.getRole() == role) {
        return;
      }
    }
    throw new RuntimeException("权限不足");
  }

  private String preferenceValue(Map<String, String> body, String key, String... allowedValues) {
    String value = body.getOrDefault(key, "").trim();
    if (!Arrays.asList(allowedValues).contains(value)) {
      throw new RuntimeException("请完整选择宿舍偏好");
    }
    return value;
  }

  private String normalizePreferenceTags(Object value) {
    if (value == null) {
      return "";
    }
    return Arrays.stream(value.toString().replace("，", ",").split(","))
        .map(String::trim)
        .filter(tag -> !tag.isEmpty())
        .collect(Collectors.joining(","));
  }

  private Map<String, Object> userToMap(User u) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", u.getId());
    item.put("username", u.getUsername());
    item.put("fullName", u.getFullName());
    item.put("role", u.getRole().name());
    item.put("buildingId", u.getBuilding() != null ? u.getBuilding().getId() : null);
    return item;
  }

  private Map<String, Object> floorToMap(Floor f) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", f.getId());
    item.put("name", f.getName());
    item.put("floorNo", f.getName());
    item.put("buildingId", f.getBuilding() != null ? f.getBuilding().getId() : null);
    return item;
  }

  private Map<String, Object> dormitoryToMap(Dormitory d) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", d.getId());
    item.put("dormCode", d.getDormCode());
    item.put("capacity", d.getCapacity());
    item.put("preferenceTags", normalizePreferenceTags(d.getPreferenceTags()));
    item.put("buildingId", d.getBuilding() != null ? d.getBuilding().getId() : null);
    item.put("floorId", d.getFloor() != null ? d.getFloor().getId() : null);
    return item;
  }

  private Map<String, Object> buildingToMap(Building b) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", b.getId());
    item.put("name", b.getName());
    item.put("address", b.getAddress());
    return item;
  }

  private Map<String, Object> moveInToMap(MoveInApplication app) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", app.getId());
    item.put("reason", app.getReason());
    item.put("status", app.getStatus().name());
    item.put("applyTime", app.getApplyTime());
    item.put("processTime", app.getProcessTime());
    item.put("comment", app.getComment());
    item.put("studentId", app.getStudent() != null ? app.getStudent().getId() : null);
    item.put("student", app.getStudent() != null ? app.getStudent().getFullName() : null);
    item.put("approverId", app.getApprover() != null ? app.getApprover().getId() : null);
    item.put("preferredDormitoryId", app.getPreferredDormitory() != null ? app.getPreferredDormitory().getId() : null);
    item.put("preferredDormitory", app.getPreferredDormitory() != null ? app.getPreferredDormitory().getDormCode() : null);
    item.put("preferenceTags", app.getPreferenceTags());
    return item;
  }

  private Map<String, Object> moveOutToMap(MoveOutApplication app) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", app.getId());
    item.put("reason", app.getReason());
    item.put("status", app.getStatus().name());
    item.put("applyTime", app.getApplyTime());
    item.put("processTime", app.getProcessTime());
    item.put("comment", app.getComment());
    item.put("studentId", app.getStudent() != null ? app.getStudent().getId() : null);
    item.put("student", app.getStudent() != null ? app.getStudent().getFullName() : null);
    item.put("bedId", app.getBed() != null ? app.getBed().getId() : null);
    item.put("bed", app.getBed() != null
        ? app.getBed().getDormitory().getDormCode() + " · " + app.getBed().getBedNo()
        : null);
    item.put("approverId", app.getApprover() != null ? app.getApprover().getId() : null);
    return item;
  }

  private Map<String, Object> repairToMap(Repair r) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", r.getId());
    item.put("location", r.getLocation());
    item.put("description", r.getDescription());
    item.put("status", r.getStatus().name());
    item.put("createTime", r.getCreateTime());
    item.put("handleTime", r.getHandleTime());
    item.put("comment", r.getComment());
    item.put("studentId", r.getStudent() != null ? r.getStudent().getId() : null);
    item.put("student", r.getStudent() != null ? r.getStudent().getFullName() : null);
    item.put("handlerId", r.getHandler() != null ? r.getHandler().getId() : null);
    return item;
  }

  private Map<String, Object> noticeToMap(Notice n) {
    Map<String, Object> item = new HashMap<>();
    item.put("id", n.getId());
    item.put("title", n.getTitle());
    item.put("content", n.getContent());
    item.put("scope", n.getScope().name());
    item.put("buildingId", n.getBuilding() != null ? n.getBuilding().getId() : null);
    item.put("building", n.getBuilding() != null ? n.getBuilding().getName() : null);
    item.put("authorId", n.getAuthor() != null ? n.getAuthor().getId() : null);
    item.put("authorName", n.getAuthor() != null ? n.getAuthor().getFullName() : null);
    item.put("createTime", n.getCreateTime());
    return item;
  }

  public static class LoginRequest {
    public String username;
    public String password;
  }
}

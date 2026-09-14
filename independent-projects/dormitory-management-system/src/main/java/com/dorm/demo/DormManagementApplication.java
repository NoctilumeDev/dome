package com.dorm.demo;

import com.dorm.demo.domain.*;
import com.dorm.demo.repo.*;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.time.LocalDateTime;

@SpringBootApplication
public class DormManagementApplication {
  public static void main(String[] args) {
    SpringApplication.run(DormManagementApplication.class, args);
  }

  @Bean
  PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
  }

  @Bean
  CommandLineRunner demoData(
      UserRepository userRepository,
      BuildingRepository buildingRepository,
      FloorRepository floorRepository,
      DormitoryRepository dormitoryRepository,
      BedRepository bedRepository,
      NoticeRepository noticeRepository,
      PasswordEncoder passwordEncoder
  ) {
    return args -> {
      if (userRepository.count() > 0) {
        String[] sampleTags = {
            "安静,早睡,整洁,阅读",
            "活跃,正常,一般,运动",
            "安静,晚睡,整洁,游戏"
        };
        int index = 0;
        for (Dormitory dormitory : dormitoryRepository.findAll()) {
          if (dormitory.getPreferenceTags() == null || dormitory.getPreferenceTags().isBlank()) {
            dormitory.setPreferenceTags(sampleTags[index % sampleTags.length]);
            dormitoryRepository.save(dormitory);
          }
          index++;
        }
        return;
      }

      Building b1 = new Building();
      b1.setName("1号宿舍楼");
      b1.setAddress("理工楼A区");
      buildingRepository.save(b1);

      Building b2 = new Building();
      b2.setName("2号宿舍楼");
      b2.setAddress("理工楼B区");
      buildingRepository.save(b2);

      Floor f1 = new Floor();
      f1.setBuilding(b1);
      f1.setName("1层");
      floorRepository.save(f1);

      Floor f2 = new Floor();
      f2.setBuilding(b1);
      f2.setName("2层");
      floorRepository.save(f2);

      Floor f3 = new Floor();
      f3.setBuilding(b2);
      f3.setName("1层");
      floorRepository.save(f3);

      Dormitory d1 = new Dormitory();
      d1.setDormCode("1-101");
      d1.setBuilding(b1);
      d1.setFloor(f1);
      d1.setCapacity(8);
      d1.setPreferenceTags("安静,早睡,整洁,阅读");
      dormitoryRepository.save(d1);

      Dormitory d2 = new Dormitory();
      d2.setDormCode("1-102");
      d2.setBuilding(b1);
      d2.setFloor(f1);
      d2.setCapacity(6);
      d2.setPreferenceTags("活跃,正常,一般,运动");
      dormitoryRepository.save(d2);

      Dormitory d3 = new Dormitory();
      d3.setDormCode("2-201");
      d3.setBuilding(b2);
      d3.setFloor(f3);
      d3.setCapacity(10);
      d3.setPreferenceTags("安静,晚睡,整洁,游戏");
      dormitoryRepository.save(d3);

      for (int i = 1; i <= d1.getCapacity(); i++) {
        Bed bed = new Bed();
        bed.setDormitory(d1);
        bed.setBedNo(i + "号床");
        bed.setStatus(BedState.VACANT);
        bed.setNotes("自动生成");
        bedRepository.save(bed);
      }
      for (int i = 1; i <= d2.getCapacity(); i++) {
        Bed bed = new Bed();
        bed.setDormitory(d2);
        bed.setBedNo(i + "号床");
        bed.setStatus(BedState.VACANT);
        bed.setNotes("自动生成");
        bedRepository.save(bed);
      }
      for (int i = 1; i <= d3.getCapacity(); i++) {
        Bed bed = new Bed();
        bed.setDormitory(d3);
        bed.setBedNo(i + "号床");
        bed.setStatus(BedState.VACANT);
        bed.setNotes("自动生成");
        bedRepository.save(bed);
      }

      User admin = new User();
      admin.setUsername("admin");
      admin.setPassword(passwordEncoder.encode("123456"));
      admin.setFullName("系统管理员");
      admin.setRole(UserRole.ADMIN);
      userRepository.save(admin);

      User manager = new User();
      manager.setUsername("manager");
      manager.setPassword(passwordEncoder.encode("123456"));
      manager.setFullName("宿舍管理员");
      manager.setRole(UserRole.DORM_MANAGER);
      manager.setBuilding(b1);
      userRepository.save(manager);

      User student = new User();
      student.setUsername("student");
      student.setPassword(passwordEncoder.encode("123456"));
      student.setFullName("测试学生");
      student.setRole(UserRole.STUDENT);
      userRepository.save(student);

      Notice notice = new Notice();
      notice.setTitle("欢迎使用宿舍管理系统");
      notice.setContent("示例系统已启动，可直接登录：admin、manager 或 student，密码都是 123456。");
      notice.setScope(NoticeScope.ALL);
      notice.setAuthor(admin);
      notice.setCreateTime(LocalDateTime.now());
      noticeRepository.save(notice);
    };
  }
}

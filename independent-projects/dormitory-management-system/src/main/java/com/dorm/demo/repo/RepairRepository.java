package com.dorm.demo.repo;

import com.dorm.demo.domain.Repair;
import com.dorm.demo.domain.RepairState;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RepairRepository extends JpaRepository<Repair, Long> {
  List<Repair> findByStudentId(Long studentId);

  List<Repair> findByStatus(RepairState status);
}


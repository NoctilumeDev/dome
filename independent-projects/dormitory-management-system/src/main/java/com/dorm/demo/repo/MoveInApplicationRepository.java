package com.dorm.demo.repo;

import com.dorm.demo.domain.MoveInApplication;
import com.dorm.demo.domain.ProcessState;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface MoveInApplicationRepository extends JpaRepository<MoveInApplication, Long> {
  List<MoveInApplication> findByStudentId(Long studentId);

  List<MoveInApplication> findByStatus(ProcessState status);

  boolean existsByStudentIdAndStatus(Long studentId, ProcessState status);

  boolean existsByAssignedBed_Id(Long bedId);
}

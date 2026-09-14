package com.dorm.demo.repo;

import com.dorm.demo.domain.MoveOutApplication;
import com.dorm.demo.domain.ProcessState;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface MoveOutApplicationRepository extends JpaRepository<MoveOutApplication, Long> {
  List<MoveOutApplication> findByStudentId(Long studentId);

  List<MoveOutApplication> findByStatus(ProcessState status);

  boolean existsByStudentIdAndStatus(Long studentId, ProcessState status);

  boolean existsByBed_Id(Long bedId);
}

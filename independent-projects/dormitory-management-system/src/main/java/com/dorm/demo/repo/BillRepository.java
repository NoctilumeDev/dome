package com.dorm.demo.repo;

import com.dorm.demo.domain.Bill;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BillRepository extends JpaRepository<Bill, Long> {
  List<Bill> findByStudentId(Long studentId);
}

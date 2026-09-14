package com.dorm.demo.repo;

import com.dorm.demo.domain.Dormitory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DormitoryRepository extends JpaRepository<Dormitory, Long> {
  List<Dormitory> findByBuildingId(Long buildingId);

  long countByFloorId(Long floorId);
}

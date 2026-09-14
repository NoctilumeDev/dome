package com.dorm.demo.repo;

import com.dorm.demo.domain.Floor;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface FloorRepository extends JpaRepository<Floor, Long> {
  List<Floor> findByBuildingId(Long buildingId);

  long countByBuildingId(Long buildingId);
}

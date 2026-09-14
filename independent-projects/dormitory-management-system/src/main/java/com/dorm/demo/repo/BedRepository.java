package com.dorm.demo.repo;

import com.dorm.demo.domain.Bed;
import com.dorm.demo.domain.BedState;
import com.dorm.demo.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

public interface BedRepository extends JpaRepository<Bed, Long> {
  List<Bed> findByDormitoryId(Long dormitoryId);

  List<Bed> findByDormitoryBuildingId(Long buildingId);

  boolean existsByOccupantId(Long occupantId);

  Optional<Bed> findByOccupantId(Long occupantId);

  boolean existsByDormitoryIdAndBedNo(Long dormitoryId, String bedNo);

  Optional<Bed> findByDormitoryIdAndBedNo(Long dormitoryId, String bedNo);

  long countByDormitoryId(Long dormitoryId);

  long countByDormitoryIdAndStatus(Long dormitoryId, BedState status);

  long countByStatus(BedState status);

  long countByDormitoryBuildingIdAndStatus(Long buildingId, BedState status);

  long countByDormitoryBuildingId(Long buildingId);

  Optional<Bed> findFirstByStatusOrderById(BedState status);

  Optional<Bed> findFirstByDormitoryIdAndStatus(Long dormitoryId, BedState status);

  @Modifying
  @Transactional
  @Query("update Bed b set b.status = :occupiedStatus, b.occupant = :student " +
      "where b.id = :id and b.status = :vacantStatus and b.occupant is null")
  int occupyIfVacant(
      @Param("id") Long id,
      @Param("student") User student,
      @Param("occupiedStatus") BedState occupiedStatus,
      @Param("vacantStatus") BedState vacantStatus
  );
}

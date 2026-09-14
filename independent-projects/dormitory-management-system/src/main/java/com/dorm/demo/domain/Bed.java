package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;

@Entity
@Table(uniqueConstraints = {
    @UniqueConstraint(name = "uk_bed_dormitory_no", columnNames = {"dormitory_id", "bed_no"}),
    @UniqueConstraint(name = "uk_bed_occupant", columnNames = {"occupant_id"})
})
@Data
@NoArgsConstructor
public class Bed {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "dormitory_id", nullable = false)
  private Dormitory dormitory;

  @Column(name = "bed_no", nullable = false, length = 64)
  private String bedNo;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private BedState status;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "occupant_id")
  private User occupant;

  @Column(length = 255)
  private String notes;
}

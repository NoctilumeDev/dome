package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;

@Entity
@Data
@NoArgsConstructor
public class Dormitory {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "building_id", nullable = false)
  private Building building;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "floor_id", nullable = false)
  private Floor floor;

  @Column(nullable = false, length = 64)
  private String dormCode;

  @Column(nullable = false)
  private Integer capacity;

  @Column(name = "preference_tags", length = 255)
  private String preferenceTags;
}

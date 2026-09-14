package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
public class MoveInApplication {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "student_id", nullable = false)
  private User student;

  @Column(nullable = false)
  private String reason;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "preferred_dormitory_id")
  private Dormitory preferredDormitory;

  @Column(name = "preference_tags", length = 255)
  private String preferenceTags;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private ProcessState status;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "approved_by")
  private User approver;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "assigned_bed_id")
  private Bed assignedBed;

  @Column(length = 255)
  private String comment;

  @Column(nullable = false)
  private LocalDateTime applyTime;

  private LocalDateTime processTime;
}

package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
public class MoveOutApplication {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "student_id", nullable = false)
  private User student;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "bed_id", nullable = false)
  private Bed bed;

  @Column(nullable = false, length = 512)
  private String reason;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private ProcessState status;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "approved_by")
  private User approver;

  @Column(length = 255)
  private String comment;

  @Column(nullable = false)
  private LocalDateTime applyTime;

  private LocalDateTime processTime;
}


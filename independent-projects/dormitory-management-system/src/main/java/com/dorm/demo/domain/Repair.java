package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
public class Repair {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "student_id", nullable = false)
  private User student;

  @Column(nullable = false, length = 255)
  private String location;

  @Column(nullable = false, length = 512)
  private String description;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private RepairState status;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "handler_id")
  private User handler;

  @Column(length = 255)
  private String comment;

  @Column(nullable = false)
  private LocalDateTime createTime;
  private LocalDateTime handleTime;
}


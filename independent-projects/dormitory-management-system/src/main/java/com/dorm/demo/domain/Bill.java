package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Data
@NoArgsConstructor
public class Bill {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "student_id", nullable = false)
  private User student;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "bed_id")
  private Bed bed;

  @Column(name = "bill_month", nullable = false, length = 16)
  private String month;

  @Column(nullable = false)
  private BigDecimal electricity;

  @Column(nullable = false)
  private BigDecimal water;

  @Column(nullable = false)
  private BigDecimal otherFee;

  @Column(nullable = false, precision = 10, scale = 2)
  private BigDecimal total;

  @Column(nullable = false)
  private LocalDate recordDate;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private BillState state;
}

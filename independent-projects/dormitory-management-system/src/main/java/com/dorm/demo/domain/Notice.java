package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
public class Notice {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(nullable = false, length = 128)
  private String title;

  @Column(nullable = false, length = 1024)
  private String content;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private NoticeScope scope;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "building_id")
  private Building building;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "author_id")
  private User author;

  @Column(nullable = false)
  private LocalDateTime createTime;

  @PrePersist
  private void fillCreateTime() {
    if (this.createTime == null) {
      this.createTime = LocalDateTime.now();
    }
  }
}

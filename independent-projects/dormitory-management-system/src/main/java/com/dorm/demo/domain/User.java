package com.dorm.demo.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;

@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
public class User {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(unique = true, nullable = false, length = 64)
  private String username;

  @Column(nullable = false, length = 64)
  private String password;

  @Column(nullable = false, length = 64)
  private String fullName;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private UserRole role;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "building_id")
  private Building building;
}


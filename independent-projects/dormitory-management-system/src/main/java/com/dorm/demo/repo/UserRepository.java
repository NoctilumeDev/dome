package com.dorm.demo.repo;

import com.dorm.demo.domain.User;
import com.dorm.demo.domain.UserRole;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserRepository extends JpaRepository<User, Long> {
  User findByUsername(String username);

  List<User> findByRole(UserRole role);
}

package com.example.repair;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper // MyBatis 看到这个记号，才会来接这份活
public interface RepairMapper {

    @Select("SELECT id, room, content FROM repair WHERE id = #{id}")
    Repair findById(Long id); // 给它一个编号，它会交回来一条 Repair
}

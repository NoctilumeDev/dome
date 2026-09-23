package com.example.repair;

public class Repair {

    private Long id; // 编号放这里
    private String room; // 宿舍号放这里
    private String content; // 坏了什么放这里

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getRoom() {
        return room;
    }

    public void setRoom(String room) {
        this.room = room;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }
}

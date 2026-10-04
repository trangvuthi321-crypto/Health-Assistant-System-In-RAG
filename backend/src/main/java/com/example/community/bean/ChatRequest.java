package com.example.community.bean;

import lombok.Data;

/**
 * 健康助手对话请求
 *
 * @author integration
 */
@Data
public class ChatRequest {
    /** 用户提问 */
    private String message;
    /** 会话ID（按登录用户隔离） */
    private String sessionId;
    /** 当前登录用户ID（供智能体工具获取用户信息/生成报告） */
    private String userId;
}

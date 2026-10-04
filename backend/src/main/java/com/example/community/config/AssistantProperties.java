package com.example.community.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 健康助手（Python 检索问答微服务）配置
 *
 * @author integration
 */
@Data
@Component
@ConfigurationProperties(prefix = "assistant")
public class AssistantProperties {
    /** Python 服务地址 */
    private String baseUrl = "http://127.0.0.1:8000";
    /** 与 Python 服务约定的共享口令，为空表示不校验 */
    private String token = "";
    /** 连接超时（毫秒） */
    private int connectTimeout = 3000;
    /** 读取超时（毫秒）——模型推理可能较慢，给足时间 */
    private int readTimeout = 90000;
}

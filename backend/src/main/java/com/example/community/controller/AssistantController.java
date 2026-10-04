package com.example.community.controller;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.example.community.bean.ChatRequest;
import com.example.community.bean.Knowledge;
import com.example.community.config.AssistantProperties;
import com.example.community.dao.KnowledgeDao;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import javax.annotation.Resource;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 健康助手：转发至 Python 检索问答微服务。
 *
 * @author integration
 */
@RestController
@RequestMapping("/assistant")
public class AssistantController {

    /** 同一会话最小请求间隔（毫秒），简单限流，防止刷接口/刷模型额度 */
    private static final long MIN_INTERVAL_MS = 1500L;

    @Resource(name = "assistantRestTemplate")
    private RestTemplate assistantRestTemplate;

    @Resource
    private AssistantProperties assistantProperties;

    @Resource
    private KnowledgeDao knowledgeDao;

    private final Map<String, Long> lastRequestAt = new ConcurrentHashMap<>();

    /**
     * 健康助手对话
     */
    @PostMapping("/chat")
    public String chat(@RequestBody ChatRequest req) {
        String sessionId = (req.getSessionId() == null || req.getSessionId().trim().isEmpty())
                ? "default" : req.getSessionId().trim();

        long now = System.currentTimeMillis();
        Long last = lastRequestAt.get(sessionId);
        if (last != null && now - last < MIN_INTERVAL_MS) {
            return errorJson("操作过于频繁，请稍后再试");
        }
        lastRequestAt.put(sessionId, now);

        if (req.getMessage() == null || req.getMessage().trim().isEmpty()) {
            return errorJson("提问内容不能为空");
        }

        JSONObject body = new JSONObject();
        body.put("message", req.getMessage().trim());
        body.put("session_id", sessionId);
        body.put("user_id", req.getUserId() == null ? "" : req.getUserId().trim());
        return doPost("/assistant/chat", body);
    }

    /**
     * 将已发布的健康知识文章同步进向量知识库
     */
    @PostMapping("/sync")
    public String sync() {
        List<Knowledge> list = knowledgeDao.getPublishedKnowledge();
        JSONArray articles = new JSONArray();
        for (Knowledge k : list) {
            JSONObject item = new JSONObject();
            item.put("id", k.getId());
            item.put("title", k.getBookName());
            item.put("author", k.getCreateName());
            item.put("introduction", k.getIntroduction());
            item.put("content", k.getContent());
            articles.add(item);
        }
        JSONObject body = new JSONObject();
        body.put("articles", articles);
        return doPost("/assistant/sync", body);
    }

    /**
     * 探活
     */
    @GetMapping("/health")
    public String health() {
        try {
            ResponseEntity<String> resp = assistantRestTemplate.getForEntity(
                    assistantProperties.getBaseUrl() + "/assistant/health", String.class);
            return resp.getBody();
        } catch (Exception e) {
            return errorJson("知识服务不可用：" + e.getMessage());
        }
    }

    private String doPost(String path, JSONObject body) {
        try {
            ResponseEntity<String> resp = assistantRestTemplate.postForEntity(
                    assistantProperties.getBaseUrl() + path, body, String.class);
            return resp.getBody();
        } catch (Exception e) {
            return errorJson("调用知识服务失败：" + e.getMessage());
        }
    }

    private String errorJson(String message) {
        JSONObject json = new JSONObject();
        json.put("code", 500);
        json.put("status", "error");
        json.put("message", message);
        return JSON.toJSONString(json);
    }
}

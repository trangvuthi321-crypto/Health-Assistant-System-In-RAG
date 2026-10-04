package com.example.community.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestTemplate;

import javax.annotation.Resource;

/**
 * 调用 Python 服务的 RestTemplate。
 * 关键点：显式设置连接/读取超时，避免下游卡死拖垮 Tomcat 线程池。
 *
 * @author integration
 */
@Configuration
public class RestTemplateConfig {

    @Resource
    private AssistantProperties assistantProperties;

    @Bean(name = "assistantRestTemplate")
    public RestTemplate assistantRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(assistantProperties.getConnectTimeout());
        factory.setReadTimeout(assistantProperties.getReadTimeout());

        RestTemplate restTemplate = new RestTemplate(factory);
        restTemplate.getInterceptors().add((request, body, execution) -> {
            if (StringUtils.hasText(assistantProperties.getToken())) {
                request.getHeaders().set("X-Service-Token", assistantProperties.getToken());
            }
            request.getHeaders().setContentType(MediaType.APPLICATION_JSON);
            return execution.execute(request, body);
        });
        return restTemplate;
    }
}

package com.rag.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GeminiConfig {
    @Value("${app.gemini.apiKey:changeme}")
    public String apiKey;

    @Value("${app.gemini.model:gemini-1.5-flash}")
    public String model;

    @Value("${app.gemini.maxOutputTokens:1024}")
    public int maxOutputTokens;
}

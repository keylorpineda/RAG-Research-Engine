package com.rag.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CohereConfig {

    @Value("${app.cohere.apiKey:changeme}")
    public String apiKey;

    @Value("${app.cohere.embeddingModel:embed-english-v3.0}")
    public String embeddingModel;

    @Value("${app.cohere.embeddingInputType:search_document}")
    public String embeddingInputType;
}

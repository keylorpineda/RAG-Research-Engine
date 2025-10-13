package com.rag.services.providers;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rag.config.CohereConfig;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class CohereEmbeddingProvider implements EmbeddingProvider {

    private static final Logger log = LoggerFactory.getLogger(CohereEmbeddingProvider.class);
    private static final MediaType JSON = MediaType.parse("application/json");
    private static final String COHERE_URL = "https://api.cohere.com/v1/embed";

    private final CohereConfig cfg;
    private final OkHttpClient http = new OkHttpClient();
    private final ObjectMapper om = new ObjectMapper();

    public CohereEmbeddingProvider(CohereConfig cfg) {
        this.cfg = cfg;
    }

    @Override
    public double[] embed(String text) throws Exception {
        if (cfg.apiKey == null || cfg.apiKey.isBlank() || "changeme".equalsIgnoreCase(cfg.apiKey.trim())) {
            throw new IllegalStateException("Cohere API key is not configured. Please set app.cohere.apiKey.");
        }

        var payload = om.createObjectNode();
        payload.put("model", cfg.embeddingModel);
        if (cfg.embeddingInputType != null && !cfg.embeddingInputType.isBlank()) {
            payload.put("input_type", cfg.embeddingInputType);
        }
        payload.put("truncate", "NONE");
        payload.putArray("texts").add(text);

        Request request = new Request.Builder()
                .url(COHERE_URL)
                .addHeader("Authorization", "Bearer " + cfg.apiKey)
                .addHeader("Content-Type", "application/json")
                .post(RequestBody.create(om.writeValueAsBytes(payload), JSON))
                .build();

        try (Response response = http.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            if (!response.isSuccessful()) {
                log.error("Cohere embeddings request failed: status={} body={}", response.code(), responseBody);
                throw new RuntimeException("Cohere embeddings error: " + response.code() + " - " + responseBody);
            }

            JsonNode embeddingsNode = om.readTree(responseBody).path("embeddings");
            if (!embeddingsNode.isArray() || embeddingsNode.size() == 0) {
                throw new RuntimeException("Cohere embeddings response is missing embeddings: " + responseBody);
            }

            JsonNode firstEmbedding = embeddingsNode.get(0);
            if (!firstEmbedding.isArray()) {
                throw new RuntimeException("Cohere embedding vector is not an array: " + responseBody);
            }

            List<Double> vector = new ArrayList<>();
            for (JsonNode value : firstEmbedding) {
                vector.add(value.asDouble());
            }
            return vector.stream().mapToDouble(Double::doubleValue).toArray();
        }
    }
}

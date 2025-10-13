package com.rag.services.providers;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rag.config.GeminiConfig;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class GeminiLLMProvider implements LLMProvider {
    private static final MediaType JSON = MediaType.parse("application/json");
    private static final String GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s";

    private final GeminiConfig cfg;
    private final OkHttpClient http = new OkHttpClient();
    private final ObjectMapper om = new ObjectMapper();

    public GeminiLLMProvider(GeminiConfig cfg) {
        this.cfg = cfg;
    }

    @Override
    public String chat(String prompt) throws Exception {
        if (cfg.apiKey == null || cfg.apiKey.isBlank() || "changeme".equalsIgnoreCase(cfg.apiKey.trim())) {
            throw new IllegalStateException("Gemini API key is not configured. Please set app.gemini.apiKey.");
        }

        Map<String, Object> payload = new HashMap<>();
        payload.put("contents", List.of(
                Map.of("parts", List.of(Map.of("text", prompt)))
        ));
        if (cfg.maxOutputTokens > 0) {
            payload.put("generationConfig", Map.of("maxOutputTokens", cfg.maxOutputTokens));
        }

        Request req = new Request.Builder()
                .url(String.format(GEMINI_URL_TEMPLATE, cfg.model, cfg.apiKey))
                .post(RequestBody.create(om.writeValueAsString(payload), JSON))
                .build();

        try (Response res = http.newCall(req).execute()) {
            if (!res.isSuccessful()) {
                throw new RuntimeException("Gemini chat error: " + res.code() + " - " + (res.body() != null ? res.body().string() : ""));
            }
            String responseBody = res.body() != null ? res.body().string() : "{}";
            JsonNode root = om.readTree(responseBody);
            JsonNode candidates = root.path("candidates");
            if (candidates.isArray()) {
                for (JsonNode candidate : candidates) {
                    JsonNode content = candidate.path("content");
                    JsonNode parts = content.path("parts");
                    if (parts.isArray()) {
                        for (JsonNode part : parts) {
                            JsonNode text = part.path("text");
                            if (text.isTextual()) {
                                return text.asText();
                            }
                        }
                    }
                }
            }
            return "";
        }
    }
}

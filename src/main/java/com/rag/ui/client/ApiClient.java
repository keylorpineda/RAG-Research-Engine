package com.rag.ui.client;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rag.dto.DocumentSummaryDto;
import com.rag.dto.QueryResponseDto;
import com.rag.dto.UploadResponseDto;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class ApiClient {

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final String baseUrl;

    public ApiClient(String baseUrl) {
        if (baseUrl == null || baseUrl.isBlank()) {
            throw new IllegalArgumentException("Base URL cannot be blank.");
        }
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
        this.objectMapper = new ObjectMapper();
    }

    public List<DocumentSummaryDto> fetchDocuments() throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/documents"))
            .timeout(Duration.ofSeconds(20))
            .GET()
            .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        ensureSuccess(response);
        return objectMapper.readValue(response.body(), new TypeReference<List<DocumentSummaryDto>>() { });
    }

    public UploadResponseDto uploadFiles(List<Path> files) throws IOException, InterruptedException {
        if (files == null || files.isEmpty()) {
            throw new IllegalArgumentException("No files to upload.");
        }
        MultipartBody body = MultipartBody.create();
        for (Path path : files) {
            if (path == null) {
                continue;
            }
            String fileName = path.getFileName().toString();
            String contentType = Files.probeContentType(path);
            body.addFilePart("files", fileName, contentType != null ? contentType : "application/octet-stream", Files.readAllBytes(path));
        }
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/upload"))
            .timeout(Duration.ofMinutes(1))
            .header("Content-Type", body.contentType())
            .POST(HttpRequest.BodyPublishers.ofByteArray(body.build()))
            .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        ensureSuccess(response);
        return objectMapper.readValue(response.body(), UploadResponseDto.class);
    }

    public QueryResponseDto askQuestion(String question, int topK) throws IOException, InterruptedException {
        Map<String, Object> payload = Map.of("q", question, "k", topK);
        String json = objectMapper.writeValueAsString(payload);
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/query"))
            .timeout(Duration.ofSeconds(30))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8))
            .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        ensureSuccess(response);
        return objectMapper.readValue(response.body(), QueryResponseDto.class);
    }

    private void ensureSuccess(HttpResponse<?> response) throws IOException {
        int status = response.statusCode();
        if (status >= 200 && status < 300) {
            return;
        }
        Object body = response.body();
        throw new IOException("API request failed with status " + status + ": " + (body != null ? body : ""));
    }

    private static class MultipartBody {
        private final String boundary;
        private final ByteArrayOutputStream output;

        private MultipartBody() {
            this.boundary = "----RagUIBoundary" + UUID.randomUUID();
            this.output = new ByteArrayOutputStream();
        }

        static MultipartBody create() {
            return new MultipartBody();
        }

        void addFilePart(String name, String filename, String contentType, byte[] content) throws IOException {
            output.write(("--" + boundary + "\r\n").getBytes(StandardCharsets.UTF_8));
            output.write(("Content-Disposition: form-data; name=\"" + name + "\"; filename=\"" + filename + "\"\r\n").getBytes(StandardCharsets.UTF_8));
            output.write(("Content-Type: " + contentType + "\r\n\r\n").getBytes(StandardCharsets.UTF_8));
            output.write(content);
            output.write("\r\n".getBytes(StandardCharsets.UTF_8));
        }

        byte[] build() throws IOException {
            output.write(("--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
            return output.toByteArray();
        }

        String contentType() {
            return "multipart/form-data; boundary=" + boundary;
        }
    }
}

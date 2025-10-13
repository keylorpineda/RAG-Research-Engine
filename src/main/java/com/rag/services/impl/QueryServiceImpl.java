package com.rag.services.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.rag.dto.QueryReferenceDto;
import com.rag.dto.QueryResponseDto;
import com.rag.entities.DocChunk;
import com.rag.entities.Embedding;
import com.rag.entities.QueryLog;
import com.rag.transformers.QueryMapper;
import com.rag.repos.DocChunkRepository;
import com.rag.repos.EmbeddingRepository;
import com.rag.repos.QueryLogRepository;
import com.rag.services.EmbeddingService;
import com.rag.services.QueryService;
import com.rag.services.providers.EmbeddingProvider;
import com.rag.services.providers.LLMProvider;
import com.rag.util.Similarity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class QueryServiceImpl implements QueryService {

    private final DocChunkRepository chunkRepository;
    private final EmbeddingRepository embeddingRepository;
    private final EmbeddingProvider embeddingProvider;
    private final LLMProvider llmProvider;
    private final EmbeddingService embeddingService;
    private final QueryLogRepository queryLogRepository;
    private final QueryMapper mapper;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public QueryServiceImpl(DocChunkRepository chunkRepository,
                            EmbeddingRepository embeddingRepository,
                            EmbeddingProvider embeddingProvider,
                            LLMProvider llmProvider,
                            EmbeddingService embeddingService,
                            QueryLogRepository queryLogRepository,
                            QueryMapper mapper) {
        this.chunkRepository = chunkRepository;
        this.embeddingRepository = embeddingRepository;
        this.embeddingProvider = embeddingProvider;
        this.llmProvider = llmProvider;
        this.embeddingService = embeddingService;
        this.queryLogRepository = queryLogRepository;
        this.mapper = mapper;
    }

    @Override
    @Transactional
    public QueryResponseDto ask(String question, int topK) throws Exception {
        double[] queryVector = embeddingProvider.embed(question);
        List<DocChunk> chunks = chunkRepository.findAll();
        Map<Integer, DocChunk> chunksById = chunks.stream()
                .collect(Collectors.toMap(DocChunk::getId, chunk -> chunk));
        List<Embedding> embeddings = embeddingRepository.findAll();
        List<Map.Entry<DocChunk, Double>> scoredChunks = new ArrayList<>();
        for (Embedding embedding : embeddings) {
            DocChunk chunk = chunksById.get(embedding.getChunkId());
            if (chunk == null) {
                continue;
            }
            double[] vector = embeddingService.parse(embedding);
            double score = Similarity.cosine(queryVector, vector);
            scoredChunks.add(Map.entry(chunk, score));
        }
        scoredChunks.sort((left, right) -> Double.compare(right.getValue(), left.getValue()));
        List<Map.Entry<DocChunk, Double>> topMatches = scoredChunks.stream()
                .limit(topK)
                .toList();

        String context = topMatches.stream()
                .map(entry -> "- (" + entry.getValue() + ") " + entry.getKey().getText())
                .collect(Collectors.joining("\n"));
        String prompt = "Eres un asistente que responde usando SOLO el contexto.\nContexto:\n" + context +
                "\n\nPregunta:" + question +
                "\nResponde en español y cita de forma breve los fragmentos.";
        String answer = llmProvider.chat(prompt);

        List<QueryReferenceDto> references = topMatches.stream()
                .map(entry -> mapper.toReference(entry.getKey(), entry.getValue()))
                .toList();

        QueryLog log = new QueryLog();
        log.setQueryText(question);
        log.setResultRefs(objectMapper.writeValueAsString(references));
        queryLogRepository.save(log);
        return new QueryResponseDto(answer, references);
    }
}

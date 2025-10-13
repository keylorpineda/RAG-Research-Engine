package com.rag.services.impl;

import com.rag.entities.DocChunk;
import com.rag.entities.Document;
import com.rag.entities.Embedding;
import com.rag.entities.JobLog;
import com.rag.entities.enums.DocumentStatus;
import com.rag.entities.enums.JobStatus;
import com.rag.repos.DocChunkRepository;
import com.rag.repos.DocumentRepository;
import com.rag.repos.EmbeddingRepository;
import com.rag.repos.JobLogRepository;
import com.rag.services.ChunkingService;
import com.rag.services.IngestionService;
import com.rag.services.TextExtractor;
import com.rag.services.providers.EmbeddingProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class IngestionServiceImpl implements IngestionService {

    private static final Logger log = LoggerFactory.getLogger(IngestionServiceImpl.class);

    private final DocumentRepository documentRepository;
    private final DocChunkRepository chunkRepository;
    private final EmbeddingRepository embeddingRepository;
    private final JobLogRepository jobLogRepository;
    private final TextExtractor textExtractor;
    private final ChunkingService chunkingService;
    private final EmbeddingProvider embeddingProvider;
    public IngestionServiceImpl(DocumentRepository documentRepository,
                                DocChunkRepository chunkRepository,
                                EmbeddingRepository embeddingRepository,
                                JobLogRepository jobLogRepository,
                                TextExtractor textExtractor,
                                ChunkingService chunkingService,
                                EmbeddingProvider embeddingProvider) {
        this.documentRepository = documentRepository;
        this.chunkRepository = chunkRepository;
        this.embeddingRepository = embeddingRepository;
        this.jobLogRepository = jobLogRepository;
        this.textExtractor = textExtractor;
        this.chunkingService = chunkingService;
        this.embeddingProvider = embeddingProvider;
    }

    @Override
    @Scheduled(fixedDelayString = "${ingestion.poll-interval-ms:2000}")
    @Transactional
    public void processPending() {
        List<Document> pendingDocuments = documentRepository.findByStatus(DocumentStatus.PENDING);
        for (Document document : pendingDocuments) {
            JobLog job = new JobLog();
            job.setDocumentId(document.getId());
            job.setType("INGEST");
            job.setStatus(JobStatus.RUNNING);
            job.setStartedAt(Instant.now());
            jobLogRepository.save(job);
            try {
                document.setStatus(DocumentStatus.PROCESSING);
                documentRepository.save(document);
                log.info("Starting ingestion job {} for document {} ({})", job.getId(), document.getId(), document.getFilename());

                String text = textExtractor.extract(Path.of(document.getPath()), document.getMime());
                List<String> chunks = chunkingService.chunk(text, 1000, 200);
                List<DocChunk> chunkEntities = new ArrayList<>(chunks.size());
                int index = 0;
                for (String chunkText : chunks) {
                    DocChunk entity = new DocChunk();
                    entity.setDocumentId(document.getId());
                    entity.setChunkIndex(index++);
                    entity.setText(chunkText);
                    entity.setTokenCount(chunkingService.approxTokens(chunkText));
                    chunkEntities.add(entity);
                }

                List<DocChunk> persistedChunks = chunkRepository.saveAll(chunkEntities);

                List<Embedding> embeddings = persistedChunks.parallelStream()
                    .map(chunk -> {
                        try {
                            double[] vector = embeddingProvider.embed(chunk.getText());
                            Embedding embedding = new Embedding();
                            embedding.setChunkId(chunk.getId());
                            embedding.setVector(vector);
                            return embedding;
                        } catch (Exception ex) {
                            throw new RuntimeException("Failed to embed chunk " + chunk.getId(), ex);
                        }
                    })
                    .collect(Collectors.toList());

                embeddingRepository.saveAll(embeddings);

                document.setStatus(DocumentStatus.READY);
                documentRepository.save(document);
                job.setStatus(JobStatus.DONE);
                job.setFinishedAt(Instant.now());
                jobLogRepository.save(job);
                log.info("Finished ingestion job {} for document {}. Status set to READY", job.getId(), document.getId());
            } catch (Exception ex) {
                document.setStatus(DocumentStatus.ERROR);
                documentRepository.save(document);
                job.setStatus(JobStatus.ERROR);
                job.setError(ex.getMessage());
                job.setFinishedAt(Instant.now());
                jobLogRepository.save(job);
                log.error("Ingestion job {} failed for document {}: {}", job.getId(), document.getId(), ex.getMessage(), ex);
            }
        }
    }
}

package com.rag.services.impl;

import com.rag.dto.DocumentDetailDto;
import com.rag.dto.DocumentSummaryDto;
import com.rag.entities.DocChunk;
import com.rag.entities.Document;
import com.rag.transformers.DocumentMapper;
import com.rag.repos.DocChunkRepository;
import com.rag.repos.DocumentRepository;
import com.rag.services.DocumentService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class DocumentServiceImpl implements DocumentService {

    private final DocumentRepository documentRepository;
    private final DocChunkRepository chunkRepository;
    private final DocumentMapper mapper;

    public DocumentServiceImpl(DocumentRepository documentRepository,
                               DocChunkRepository chunkRepository,
                               DocumentMapper mapper) {
        this.documentRepository = documentRepository;
        this.chunkRepository = chunkRepository;
        this.mapper = mapper;
    }

    @Override
    @Transactional(readOnly = true)
    public List<DocumentSummaryDto> getAllSummaries() {
        return documentRepository.findAll().stream()
                .map(mapper::toSummary)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public DocumentDetailDto getDetail(Integer id) {
        Document document = documentRepository.findById(id).orElseThrow();
        List<DocChunk> chunks = chunkRepository.findByDocumentIdOrderByChunkIndexAsc(id);
        return mapper.toDetail(document, chunks);
    }

    @Override
    @Transactional
    public Integer register(Document document) {
        Document saved = documentRepository.save(document);
        return saved.getId();
    }
}

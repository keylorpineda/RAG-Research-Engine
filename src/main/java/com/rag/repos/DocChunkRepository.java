package com.rag.repos;

import com.rag.entities.DocChunk;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DocChunkRepository extends JpaRepository<DocChunk, Integer> {
    List<DocChunk> findByDocumentIdOrderByChunkIndexAsc(Integer documentId);
}

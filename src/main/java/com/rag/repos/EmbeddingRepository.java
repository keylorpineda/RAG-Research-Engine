package com.rag.repos;
import com.rag.entities.Embedding;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface EmbeddingRepository extends JpaRepository<Embedding, Integer> {
    List<Embedding> findByChunkIdIn(java.util.Collection<Integer> ids);
    List<Embedding> findByChunkId(Integer id);
}

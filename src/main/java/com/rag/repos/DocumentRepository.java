package com.rag.repos;

import com.rag.entities.Document;
import com.rag.entities.enums.DocumentStatus;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentRepository extends JpaRepository<Document, Integer> {
  List<Document> findByStatus(DocumentStatus status);
}

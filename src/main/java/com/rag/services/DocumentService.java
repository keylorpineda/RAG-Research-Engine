package com.rag.services;

import com.rag.dto.DocumentDetailDto;
import com.rag.dto.DocumentSummaryDto;
import com.rag.entities.Document;

import java.util.List;

public interface DocumentService {

    List<DocumentSummaryDto> getAllSummaries();

    DocumentDetailDto getDetail(Integer id);

    Integer register(Document document);
}

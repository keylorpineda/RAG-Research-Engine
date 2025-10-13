package com.rag.controllers;

import com.rag.dto.DocumentDetailDto;
import com.rag.dto.DocumentSummaryDto;
import com.rag.services.DocumentService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api")
public class DocumentController {
    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @GetMapping("/documents")
    public List<DocumentSummaryDto> list() {
        return documentService.getAllSummaries();
    }

    @GetMapping("/documents/{id}")
    public DocumentDetailDto one(@PathVariable Integer id) {
        return documentService.getDetail(id);
    }
}

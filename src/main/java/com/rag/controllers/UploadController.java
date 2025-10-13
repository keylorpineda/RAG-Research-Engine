package com.rag.controllers;

import com.rag.dto.UploadResponseDto;
import com.rag.entities.Document;
import com.rag.entities.enums.DocumentStatus;
import com.rag.services.DocumentService;
import com.rag.services.StorageService;
import jakarta.validation.constraints.Size;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api")
@Validated
public class UploadController {

    private final StorageService storage;
    private final DocumentService documentService;

    public UploadController(StorageService storage, DocumentService documentService) {
        this.storage = storage;
        this.documentService = documentService;
    }

    @PostMapping(path = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<UploadResponseDto> upload(@RequestParam("files") @Size(max = 10) MultipartFile[] files) throws Exception {
        if (files.length == 0) {
            throw new IllegalArgumentException("No files provided.");
        }
        if (files.length > 10) {
            throw new IllegalArgumentException("Max 10 files.");
        }
        List<Integer> ids = new ArrayList<>();
        for (MultipartFile mf : files) {
            if (mf.getSize() > 20 * 1024 * 1024) {
                throw new IllegalArgumentException("Max 20MB per file.");
            }
            String originalName = java.util.Optional.ofNullable(mf.getOriginalFilename()).orElse("");
            String fn = originalName.toLowerCase();
            if (fn.isBlank()) {
                throw new IllegalArgumentException("Filename is required.");
            }
            if (!(fn.endsWith(".txt") || fn.endsWith(".md") || fn.endsWith(".pdf"))) {
                throw new IllegalArgumentException("Only TXT/MD/PDF files are supported.");
            }
            Path p = storage.save(mf);
            Document d = new Document();
            d.setFilename(mf.getOriginalFilename());
            d.setMime(mf.getContentType());
            d.setPath(p.toAbsolutePath().toString());
            d.setSize(mf.getSize());
            d.setStatus(DocumentStatus.PENDING);
            ids.add(documentService.register(d));
        }
        return ResponseEntity.ok(new UploadResponseDto(ids, "uploaded"));
    }
}

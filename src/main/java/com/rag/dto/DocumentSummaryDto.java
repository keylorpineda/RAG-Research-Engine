package com.rag.dto;

import com.rag.entities.enums.DocumentStatus;

/**
 * DTO representing a document summary. Needs an explicit no-arg constructor for ModelMapper.
 */
public class DocumentSummaryDto {

    private Integer id;
    private String filename;
    private DocumentStatus status;
    private Long size;

    public DocumentSummaryDto() {
    }

    public DocumentSummaryDto(Integer id, String filename, DocumentStatus status, Long size) {
        this.id = id;
        this.filename = filename;
        this.status = status;
        this.size = size;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public DocumentStatus getStatus() {
        return status;
    }

    public void setStatus(DocumentStatus status) {
        this.status = status;
    }

    public Long getSize() {
        return size;
    }

    public void setSize(Long size) {
        this.size = size;
    }
}

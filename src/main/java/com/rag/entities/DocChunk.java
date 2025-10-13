package com.rag.entities;

import jakarta.persistence.*;

@Entity
@Table(name = "doc_chunks")
public class DocChunk {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "document_id")
    private Integer documentId;

    @Column(name = "chunk_index")
    private Integer chunkIndex;

    @Lob
    @Column(columnDefinition = "TEXT")
    private String text;

    @Column(name = "token_count")
    private Integer tokenCount;

    public DocChunk() {
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public Integer getDocumentId() {
        return documentId;
    }

    public void setDocumentId(Integer documentId) {
        this.documentId = documentId;
    }

    public Integer getChunkIndex() {
        return chunkIndex;
    }

    public void setChunkIndex(Integer chunkIndex) {
        this.chunkIndex = chunkIndex;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public Integer getTokenCount() {
        return tokenCount;
    }

    public void setTokenCount(Integer tokenCount) {
        this.tokenCount = tokenCount;
    }
}

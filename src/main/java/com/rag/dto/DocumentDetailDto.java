package com.rag.dto;

import com.rag.entities.enums.DocumentStatus;

import java.util.List;

public record DocumentDetailDto(Integer id, String filename, DocumentStatus status, Long size, List<DocChunkDto> chunks) { }

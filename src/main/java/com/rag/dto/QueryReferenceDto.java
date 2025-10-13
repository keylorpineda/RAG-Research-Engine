package com.rag.dto;

public record QueryReferenceDto(Integer docId, Integer chunkIndex, String text, Double score) { }

package com.rag.dto;

public record ErrorResponseDto(String error, String detail) {
    public ErrorResponseDto(String error) {
        this(error, null);
    }
}

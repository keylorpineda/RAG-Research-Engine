package com.rag.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

public record QueryRequestDto(@NotBlank String q, @Min(1) Integer k) {
    public QueryRequestDto {
        if (k == null) {
            k = 5;
        }
    }
}

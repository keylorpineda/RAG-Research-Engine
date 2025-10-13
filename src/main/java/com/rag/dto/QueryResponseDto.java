package com.rag.dto;

import java.util.List;

public record QueryResponseDto(String answer, List<QueryReferenceDto> refs) { }

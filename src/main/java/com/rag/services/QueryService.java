package com.rag.services;

import com.rag.dto.QueryResponseDto;

public interface QueryService {

    QueryResponseDto ask(String question, int topK) throws Exception;
}

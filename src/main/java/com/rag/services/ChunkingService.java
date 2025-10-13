package com.rag.services;

import java.util.List;

public interface ChunkingService {

    List<String> chunk(String text, int size, int overlap);

    int approxTokens(String text);
}

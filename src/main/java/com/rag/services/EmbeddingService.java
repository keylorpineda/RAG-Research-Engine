package com.rag.services;

import com.rag.entities.Embedding;

public interface EmbeddingService {

    double[] parse(Embedding embedding);
}

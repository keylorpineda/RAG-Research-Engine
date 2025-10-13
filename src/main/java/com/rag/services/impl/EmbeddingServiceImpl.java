package com.rag.services.impl;

import com.rag.entities.Embedding;
import com.rag.services.EmbeddingService;
import org.springframework.stereotype.Service;

@Service
public class EmbeddingServiceImpl implements EmbeddingService {

    @Override
    public double[] parse(Embedding embedding) {
        double[] vector = embedding.getVector();
        return vector == null ? new double[0] : vector;
    }
}

package com.rag.services.providers;
public interface EmbeddingProvider {
    double[] embed(String text) throws Exception;
}

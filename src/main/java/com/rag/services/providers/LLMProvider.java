package com.rag.services.providers;
public interface LLMProvider {
    String chat(String prompt) throws Exception;
}

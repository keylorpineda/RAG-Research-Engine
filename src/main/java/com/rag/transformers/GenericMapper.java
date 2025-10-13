package com.rag.transformers;

public interface GenericMapper<E, D> {
    D convertToDto(E entity);
    E convertToEntity(D dto);
}

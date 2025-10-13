package com.rag.transformers;

import com.rag.dto.QueryReferenceDto;
import com.rag.entities.DocChunk;
import org.springframework.stereotype.Component;

@Component
public class QueryMapper {

    public QueryReferenceDto toReference(DocChunk chunk, double score) {
        if (chunk == null) {
            return new QueryReferenceDto(null, null, null, score);
        }
        return new QueryReferenceDto(chunk.getDocumentId(), chunk.getChunkIndex(), chunk.getText(), score);
    }
}

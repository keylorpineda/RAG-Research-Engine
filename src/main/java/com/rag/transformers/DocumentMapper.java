package com.rag.transformers;

import com.rag.dto.DocChunkDto;
import com.rag.dto.DocumentDetailDto;
import com.rag.dto.DocumentSummaryDto;
import com.rag.entities.DocChunk;
import com.rag.entities.Document;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class DocumentMapper {

    private final GenericMapper<Document, DocumentSummaryDto> summaryMapper;

    public DocumentMapper(GenericMapperFactory factory) {
        this.summaryMapper = factory.createMapper(Document.class, DocumentSummaryDto.class);
    }

    public DocumentSummaryDto toSummary(Document document) {
        return summaryMapper.convertToDto(document);
    }

    public DocumentDetailDto toDetail(Document document, List<DocChunk> chunks) {
        List<DocChunkDto> chunkDtos = chunks.stream()
            .map(this::toChunk)
            .toList();
        DocumentSummaryDto summary = toSummary(document);
        return new DocumentDetailDto(
            summary.getId(),
            summary.getFilename(),
            summary.getStatus(),
            summary.getSize(),
            chunkDtos
        );
    }

    private DocChunkDto toChunk(DocChunk chunk) {
        Integer index = chunk.getChunkIndex() != null ? chunk.getChunkIndex() : 0;
        String text = chunk.getText();
        return new DocChunkDto(index, text);
    }
}

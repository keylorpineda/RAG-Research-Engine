package com.rag.services.impl;

import com.rag.services.TextExtractor;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
public class TextExtractorImpl implements TextExtractor {

    @Override
    public String extract(Path path, String mime) throws IOException {
        String fileName = path.getFileName().toString().toLowerCase();
        if ((mime != null && mime.contains("pdf")) || fileName.endsWith(".pdf")) {
            try (PDDocument document = PDDocument.load(path.toFile())) {
                PDFTextStripper stripper = new PDFTextStripper();
                return stripper.getText(document);
            }
        }
        return Files.readString(path);
    }
}

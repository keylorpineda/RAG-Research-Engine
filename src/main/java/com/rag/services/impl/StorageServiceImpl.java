package com.rag.services.impl;

import com.rag.services.StorageService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;

@Service
public class StorageServiceImpl implements StorageService {

    private final Path baseDirectory;

    public StorageServiceImpl(@Value("${app.uploadsDir:uploads}") String directory) throws IOException {
        this.baseDirectory = Paths.get(directory);
        Files.createDirectories(baseDirectory);
    }

    @Override
    public Path save(MultipartFile file) throws IOException {
        Path destination = baseDirectory.resolve(System.currentTimeMillis() + "-" + file.getOriginalFilename());
        Files.copy(file.getInputStream(), destination, StandardCopyOption.REPLACE_EXISTING);
        return destination;
    }
}

package com.rag.services;

import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Path;

public interface StorageService {

    Path save(MultipartFile file) throws IOException;
}

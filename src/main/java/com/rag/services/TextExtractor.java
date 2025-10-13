package com.rag.services;

import java.io.IOException;
import java.nio.file.Path;

public interface TextExtractor {

    String extract(Path path, String mime) throws IOException;
}

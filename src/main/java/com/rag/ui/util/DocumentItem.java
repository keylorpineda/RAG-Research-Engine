package com.rag.ui.util;

import com.rag.dto.DocumentSummaryDto;
import javafx.beans.property.SimpleStringProperty;
import javafx.beans.property.StringProperty;

import java.nio.file.Path;

/**
 * View model used by the JavaFX table to display local and remote documents.
 */
public class DocumentItem {

    private final StringProperty id = new SimpleStringProperty();
    private final StringProperty name = new SimpleStringProperty();
    private final StringProperty status = new SimpleStringProperty();
    private final StringProperty size = new SimpleStringProperty();
    private final Path sourcePath;
    private final Integer backendId;

    private DocumentItem(Integer backendId,
                         Path sourcePath,
                         String displayId,
                         String name,
                         Long sizeInBytes,
                         String status) {
        this.backendId = backendId;
        this.sourcePath = sourcePath;
        this.id.set(displayId);
        this.name.set(name);
        this.size.set(formatSize(sizeInBytes));
        this.status.set(status);
    }

    public static DocumentItem fromLocal(String displayId,
                                         Path sourcePath,
                                         String name,
                                         long sizeInBytes,
                                         String pendingStatus) {
        return new DocumentItem(null, sourcePath, displayId, name, sizeInBytes, pendingStatus);
    }

    public static DocumentItem fromRemote(DocumentSummaryDto dto) {
        Integer backendId = dto.getId();
        String displayId = formatRemoteId(backendId);
        String status = dto.getStatus() != null ? dto.getStatus().name() : "";
        Long size = dto.getSize();
        return new DocumentItem(backendId, null, displayId, dto.getFilename(), size, status);
    }

    public boolean isLocal() {
        return sourcePath != null;
    }

    public boolean isRemote() {
        return backendId != null;
    }

    public StringProperty idProperty() {
        return id;
    }

    public String getId() {
        return id.get();
    }

    public StringProperty nameProperty() {
        return name;
    }

    public String getName() {
        return name.get();
    }

    public StringProperty statusProperty() {
        return status;
    }

    public String getStatus() {
        return status.get();
    }

    public void setStatus(String newStatus) {
        status.set(newStatus);
    }

    public StringProperty sizeProperty() {
        return size;
    }

    public String getSize() {
        return size.get();
    }

    public Path getSourcePath() {
        return sourcePath;
    }

    public Integer getBackendId() {
        return backendId;
    }

    private static String formatRemoteId(Integer backendId) {
        if (backendId == null) {
            return "-";
        }
        return String.format("#%03d", backendId);
    }

    private static String formatSize(Long bytes) {
        if (bytes == null) {
            return "-";
        }
        if (bytes <= 0) {
            return "0 B";
        }
        String[] units = {"B", "KB", "MB", "GB", "TB"};
        double value = bytes;
        int unitIndex = 0;
        while (value >= 1024 && unitIndex < units.length - 1) {
            value /= 1024;
            unitIndex++;
        }
        return String.format("%.1f %s", value, units[unitIndex]);
    }
}

package com.rag.ui.controller;

import com.rag.dto.DocumentSummaryDto;
import com.rag.dto.QueryReferenceDto;
import com.rag.dto.QueryResponseDto;
import com.rag.ui.client.ApiClient;
import com.rag.ui.util.DaemonThreadFactory;
import com.rag.ui.util.DocumentItem;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ListChangeListener;
import javafx.collections.ObservableList;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ListView;
import javafx.scene.control.SelectionMode;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.control.TextArea;
import javafx.stage.FileChooser;
import javafx.stage.Window;

import java.io.File;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 * Controller responsible for coordinating user interactions from the JavaFX view.
 */
public class MainViewController {

    private static final int MAX_FILES = 10;
    private static final int DEFAULT_TOP_K = 5;
    private static final String STATUS_PENDING = "PENDING";
    private static final String STATUS_PROCESSING = "PROCESSING";
    private static final String STATUS_READY = "READY";
    private static final String DEFAULT_API_BASE_URL = "http://localhost:8080/api";

    @FXML
    private Button selectFilesButton;

    @FXML
    private Button uploadButton;

    @FXML
    private Button deleteSelectedButton;

    @FXML
    private Label selectedFilesLabel;

    @FXML
    private TableView<DocumentItem> documentsTable;

    @FXML
    private TableColumn<DocumentItem, String> idColumn;

    @FXML
    private TableColumn<DocumentItem, String> nameColumn;

    @FXML
    private TableColumn<DocumentItem, String> statusColumn;

    @FXML
    private TableColumn<DocumentItem, String> sizeColumn;

    @FXML
    private TextArea queryInput;

    @FXML
    private Button sendQueryButton;

    @FXML
    private TextArea queryResultArea;

    @FXML
    private ListView<String> referencesList;

    private final ObservableList<DocumentItem> documents = FXCollections.observableArrayList();
    private final AtomicInteger idGenerator = new AtomicInteger(1);
    private final ScheduledExecutorService executorService =
        Executors.newSingleThreadScheduledExecutor(new DaemonThreadFactory());

    private ScheduledFuture<?> refreshTask;
    private ApiClient apiClient;
    private volatile boolean uploadInProgress;
    private volatile boolean queryInProgress;

    @FXML
    public void initialize() {
        idColumn.setCellValueFactory(cell -> cell.getValue().idProperty());
        nameColumn.setCellValueFactory(cell -> cell.getValue().nameProperty());
        statusColumn.setCellValueFactory(cell -> cell.getValue().statusProperty());
        sizeColumn.setCellValueFactory(cell -> cell.getValue().sizeProperty());

        documentsTable.setItems(documents);
        documentsTable.getSelectionModel().setSelectionMode(SelectionMode.MULTIPLE);
        documentsTable.setPlaceholder(new Label("No hay documentos cargados."));
        documentsTable.getSelectionModel().getSelectedItems().addListener(
            (ListChangeListener<DocumentItem>) change -> updateDeleteButtonState());

        queryInput.textProperty().addListener((obs, oldValue, newValue) -> updateSendQueryButtonState());
        updateSendQueryButtonState();

        updateSelectedFilesLabel();
        updateUploadButtonState();
        updateDeleteButtonState();

        apiClient = new ApiClient(resolveApiBaseUrl());
        refreshDocumentsFromServer(true);
        refreshTask = executorService.scheduleAtFixedRate(() -> fetchDocumentsAndSync(false), 12, 12, TimeUnit.SECONDS);
    }

    @FXML
    public void handleSelectFiles(ActionEvent event) {
        Window owner = selectFilesButton.getScene() != null ? selectFilesButton.getScene().getWindow() : null;
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Seleccionar documentos");
        fileChooser.getExtensionFilters().add(new FileChooser.ExtensionFilter(
            "Documentos soportados", "*.txt", "*.md", "*.pdf"));

        List<File> selectedFiles = fileChooser.showOpenMultipleDialog(owner);
        if (selectedFiles == null || selectedFiles.isEmpty()) {
            return;
        }

        int localCount = countLocalDocuments();
        int availableSlots = MAX_FILES - localCount;
        if (availableSlots <= 0) {
            showAlert(Alert.AlertType.INFORMATION, "Límite alcanzado",
                "Solo se permiten " + MAX_FILES + " archivos por lote.");
            return;
        }

        List<File> filesToProcess = selectedFiles.stream()
            .limit(availableSlots)
            .collect(Collectors.toList());

        List<File> duplicates = new ArrayList<>();
        for (File file : filesToProcess) {
            Path path = file.toPath().toAbsolutePath().normalize();
            boolean alreadyExists = documents.stream()
                .filter(DocumentItem::isLocal)
                .anyMatch(item -> path.equals(item.getSourcePath()));
            if (alreadyExists) {
                duplicates.add(file);
                continue;
            }

            DocumentItem item = DocumentItem.fromLocal(
                generateDocumentId(),
                path,
                file.getName(),
                file.length(),
                STATUS_PENDING);
            documents.add(item);
        }

        if (!duplicates.isEmpty()) {
            showAlert(Alert.AlertType.INFORMATION, "Archivos omitidos",
                "Se omitieron " + duplicates.size() + " archivo(s) porque ya estaban en la lista.");
        }

        if (selectedFiles.size() > filesToProcess.size()) {
            showAlert(Alert.AlertType.INFORMATION, "Límite de archivos",
                "Algunos archivos no fueron agregados porque se alcanzó el máximo de " + MAX_FILES + ".");
        }

        sortDocumentsForDisplay();
        updateSelectedFilesLabel();
        updateUploadButtonState();
    }

    @FXML
    public void handleUpload(ActionEvent event) {
        List<DocumentItem> pendingItems = documents.stream()
            .filter(DocumentItem::isLocal)
            .collect(Collectors.toList());

        if (pendingItems.isEmpty()) {
            showAlert(Alert.AlertType.INFORMATION, "Sin pendientes",
                "No hay archivos para subir. Seleccione nuevos archivos.");
            return;
        }

        pendingItems.forEach(item -> item.setStatus(STATUS_PROCESSING));
        uploadInProgress = true;
        updateUploadButtonState();

        List<Path> paths = pendingItems.stream()
            .map(DocumentItem::getSourcePath)
            .collect(Collectors.toList());

        executorService.submit(() -> {
            try {
                apiClient.uploadFiles(paths);
                Platform.runLater(() -> {
                    documents.removeAll(pendingItems);
                    sortDocumentsForDisplay();
                    updateSelectedFilesLabel();
                    showAlert(Alert.AlertType.INFORMATION, "Carga completada",
                        "Los archivos fueron enviados y comenzarán a procesarse.");
                    refreshDocumentsFromServer(false);
                });
            } catch (Exception e) {
                if (e instanceof InterruptedException) {
                    Thread.currentThread().interrupt();
                }
                Platform.runLater(() -> {
                    pendingItems.forEach(item -> item.setStatus(STATUS_PENDING));
                    showAlert(Alert.AlertType.ERROR, "Error al subir", e.getMessage());
                });
            } finally {
                Platform.runLater(() -> {
                    uploadInProgress = false;
                    updateUploadButtonState();
                });
            }
        });
    }

    @FXML
    public void handleDeleteSelected(ActionEvent event) {
        ObservableList<DocumentItem> selectedItems = documentsTable.getSelectionModel().getSelectedItems();
        if (selectedItems == null || selectedItems.isEmpty()) {
            showAlert(Alert.AlertType.INFORMATION, "Sin selección", "Seleccione documentos locales para eliminarlos.");
            return;
        }

        List<DocumentItem> localItems = selectedItems.stream()
            .filter(DocumentItem::isLocal)
            .collect(Collectors.toList());

        if (localItems.isEmpty()) {
            showAlert(Alert.AlertType.INFORMATION, "No se puede eliminar", "Solo se pueden eliminar documentos pendientes.");
            return;
        }

        documents.removeAll(localItems);
        documentsTable.getSelectionModel().clearSelection();

        updateSelectedFilesLabel();
        updateUploadButtonState();
        updateDeleteButtonState();
    }

    @FXML
    public void handleSendQuery(ActionEvent event) {
        String question = queryInput.getText() != null ? queryInput.getText().trim() : "";
        if (question.isEmpty()) {
            showAlert(Alert.AlertType.WARNING, "Consulta vacía", "Ingrese una pregunta para continuar.");
            return;
        }

        boolean hasReadyDocuments = documents.stream()
            .filter(DocumentItem::isRemote)
            .anyMatch(item -> STATUS_READY.equalsIgnoreCase(item.getStatus()));

        if (!hasReadyDocuments) {
            queryResultArea.setText("No hay documentos con estado READY. Intente nuevamente cuando la ingesta finalice.");
            referencesList.getItems().clear();
            return;
        }

        queryInProgress = true;
        updateSendQueryButtonState();
        queryResultArea.setText("Consultando a la IA...");
        referencesList.getItems().clear();

        executorService.submit(() -> {
            try {
                QueryResponseDto response = apiClient.askQuestion(question, DEFAULT_TOP_K);
                Platform.runLater(() -> applyQueryResponse(response));
            } catch (Exception e) {
                if (e instanceof InterruptedException) {
                    Thread.currentThread().interrupt();
                }
                Platform.runLater(() -> {
                    queryResultArea.setText("Error al consultar la IA: " + e.getMessage());
                    showAlert(Alert.AlertType.ERROR, "Error en consulta", e.getMessage());
                });
            } finally {
                Platform.runLater(() -> {
                    queryInProgress = false;
                    updateSendQueryButtonState();
                });
            }
        });
    }

    public void shutdown() {
        if (refreshTask != null) {
            refreshTask.cancel(true);
        }
        executorService.shutdownNow();
    }

    private void applyQueryResponse(QueryResponseDto response) {
        if (response == null) {
            queryResultArea.setText("No se recibió respuesta de la IA.");
            referencesList.getItems().clear();
            return;
        }

        queryResultArea.setText(response.answer() != null ? response.answer() : "");

        ObservableList<String> references = FXCollections.observableArrayList();
        if (response.refs() != null) {
            for (QueryReferenceDto ref : response.refs()) {
                references.add(formatReference(ref));
            }
        }
        referencesList.setItems(references);
    }

    private void refreshDocumentsFromServer(boolean showError) {
        executorService.submit(() -> fetchDocumentsAndSync(showError));
    }

    private void fetchDocumentsAndSync(boolean showError) {
        if (apiClient == null) {
            return;
        }
        try {
            List<DocumentSummaryDto> summaries = apiClient.fetchDocuments();
            Platform.runLater(() -> applyRemoteDocuments(summaries));
        } catch (Exception e) {
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            if (showError) {
                Platform.runLater(() -> showAlert(Alert.AlertType.ERROR, "Error al cargar documentos", e.getMessage()));
            } else {
                System.err.println("No se pudo actualizar la lista de documentos: " + e.getMessage());
            }
        }
    }

    private void applyRemoteDocuments(List<DocumentSummaryDto> summaries) {
        if (summaries == null) {
            return;
        }
        documents.removeIf(DocumentItem::isRemote);
        List<DocumentItem> remoteItems = summaries.stream()
            .map(DocumentItem::fromRemote)
            .sorted(Comparator.comparing(DocumentItem::getBackendId, Comparator.nullsLast(Integer::compareTo)))
            .collect(Collectors.toList());
        documents.addAll(remoteItems);
        sortDocumentsForDisplay();
    }

    private String formatReference(QueryReferenceDto ref) {
        if (ref == null) {
            return "";
        }
        Integer docId = ref.docId();
        Integer chunkIndex = ref.chunkIndex();
        Double score = ref.score();
        String scoreText = score != null ? String.format("%.3f", score) : "-";
        String text = ref.text() != null ? ref.text().replaceAll("\\s+", " ").trim() : "";
        if (text.length() > 160) {
            text = text.substring(0, 157) + "...";
        }
        return "Documento #" + (docId != null ? docId : "?") +
            " · Fragmento " + (chunkIndex != null ? chunkIndex : "?") +
            " · Score " + scoreText + "\n" + text;
    }

    private void sortDocumentsForDisplay() {
        Comparator<DocumentItem> comparator = (left, right) -> {
            if (left.isLocal() && right.isLocal()) {
                return left.getId().compareToIgnoreCase(right.getId());
            }
            if (left.isRemote() && right.isRemote()) {
                Integer leftId = left.getBackendId();
                Integer rightId = right.getBackendId();
                if (leftId == null && rightId == null) {
                    return 0;
                }
                if (leftId == null) {
                    return 1;
                }
                if (rightId == null) {
                    return -1;
                }
                return leftId.compareTo(rightId);
            }
            return left.isLocal() ? -1 : 1;
        };
        FXCollections.sort(documents, comparator);
    }

    private int countLocalDocuments() {
        return (int) documents.stream().filter(DocumentItem::isLocal).count();
    }

    private String resolveApiBaseUrl() {
        String property = System.getProperty("rag.api.base-url");
        if (property == null || property.isBlank()) {
            property = System.getenv("RAG_API_BASE_URL");
        }
        if (property == null || property.isBlank()) {
            property = DEFAULT_API_BASE_URL;
        }
        return property;
    }

    private void updateSelectedFilesLabel() {
        int pending = countLocalDocuments();
        selectedFilesLabel.setText("Archivos pendientes de subida: " + pending + " / " + MAX_FILES);
    }

    private void updateUploadButtonState() {
        boolean hasPending = documents.stream().anyMatch(DocumentItem::isLocal);
        uploadButton.setDisable(uploadInProgress || !hasPending);
    }

    private void updateDeleteButtonState() {
        if (deleteSelectedButton == null) {
            return;
        }
        ObservableList<DocumentItem> selectedItems = documentsTable.getSelectionModel().getSelectedItems();
        boolean hasSelection = selectedItems != null && !selectedItems.isEmpty();
        boolean allLocal = hasSelection && selectedItems != null && selectedItems.stream().allMatch(DocumentItem::isLocal);
        deleteSelectedButton.setDisable(!hasSelection || !allLocal);
    }

    private void updateSendQueryButtonState() {
        String text = queryInput.getText();
        boolean hasText = text != null && !text.trim().isEmpty();
        sendQueryButton.setDisable(!hasText || queryInProgress);
    }

    private void showAlert(Alert.AlertType type, String title, String message) {
        Alert alert = new Alert(type);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }

    private String generateDocumentId() {
        return String.format("LOCAL-%03d", idGenerator.getAndIncrement());
    }

}

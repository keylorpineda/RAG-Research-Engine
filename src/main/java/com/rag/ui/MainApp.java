package com.rag.ui;

import com.rag.ui.controller.MainViewController;
import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.stage.Stage;

/**
 * JavaFX entry point that loads the main view defined in FXML.
 */
public class MainApp extends Application {

    @Override
    public void start(Stage primaryStage) throws Exception {
        FXMLLoader loader = new FXMLLoader(getClass().getResource("/com/rag/ui/MainView.fxml"));
        Parent root = loader.load();
        MainViewController controller = loader.getController();

        primaryStage.setTitle("RAG Demo UI");
        primaryStage.setScene(new Scene(root));
        primaryStage.setMinWidth(800);
        primaryStage.setMinHeight(540);
        primaryStage.show();

        primaryStage.setOnCloseRequest(event -> controller.shutdown());
    }

    public static void main(String[] args) {
        launch(args);
    }
}

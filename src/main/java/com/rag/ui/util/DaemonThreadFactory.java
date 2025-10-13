package com.rag.ui.util;

import java.util.concurrent.ThreadFactory;

/**
 * Simple {@link ThreadFactory} that marks worker threads as daemon threads so
 * that the JavaFX application can exit cleanly.
 */
public class DaemonThreadFactory implements ThreadFactory {

    @Override
    public Thread newThread(Runnable runnable) {
        Thread thread = new Thread(runnable, "rag-ui-worker");
        thread.setDaemon(true);
        return thread;
    }
}

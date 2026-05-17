package com.ultrasoundImage.converter.util;

import java.time.LocalDateTime;

public class ProcessResult {
    private Algorithm algorithm;
    private LocalDateTime startDateTime;
    private LocalDateTime endDateTime;
    private int widthPixels;
    private int heightPixels;
    private int numIterations;

    public ProcessResult(){
        algorithm = null;
        startDateTime = null;
        endDateTime = null;
        widthPixels = 0;
        heightPixels = 0;
        numIterations = 0;
    }

    public Algorithm getAlgorithm() {
        return this.algorithm;
    }

    public void setAlgorithm(Algorithm algorithm) {
        this.algorithm = algorithm;
    }

    public LocalDateTime getStartDateTime() {
        return this.startDateTime;
    }

    public void setStartDateTime(LocalDateTime startDateTime) {
        this.startDateTime = startDateTime;
    }

    public LocalDateTime getEndDateTime() {
        return this.endDateTime;
    }

    public void setEndDateTime(LocalDateTime endDateTime) {
        this.endDateTime = endDateTime;
    }

    public int getWidthPixels() {
        return this.widthPixels;
    }

    public void setWidthPixels(int widthPixels) {
        this.widthPixels = widthPixels;
    }

    public int getHeightPixels() {
        return this.heightPixels;
    }

    public void setHeightPixels(int heightPixels) {
        this.heightPixels = heightPixels;
    }

    public int getNumIterations() {
        return this.numIterations;
    }

    public void setNumIterations(int numIterations) {
        this.numIterations = numIterations;
    }
}

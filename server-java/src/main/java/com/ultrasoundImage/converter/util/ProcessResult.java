package com.ultrasoundImage.converter.util;

import java.time.LocalDateTime;

public class ProcessResult {
    private Algorithm algorithm;
    private LocalDateTime startDateTime;
    private LocalDateTime endDateTime;
    private int widthPixels;
    private int heightPixels;
    private int numIterations;
    // em bytes
    private long initialAllocatedMemory;
    private long finalAllocatedMemory;
    // em ms
    private long initialCPUTime;
    private long finalCPUTime;

    public ProcessResult(){
        algorithm = null;
        startDateTime = null;
        endDateTime = null;
        widthPixels = 0;
        heightPixels = 0;
        numIterations = 0;
        initialAllocatedMemory = 0;
        finalAllocatedMemory = 0;
        initialCPUTime = 0;
        finalCPUTime = 0;
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

    public long getFinalAllocatedMemory() {
        return finalAllocatedMemory;
    }

    public long getInitialAllocatedMemory() {
        return initialAllocatedMemory;
    }

    public void setInitialAllocatedMemory(long initialAllocatedMemory) {
        this.initialAllocatedMemory = initialAllocatedMemory;
    }

    public void setFinalAllocatedMemory(long finalAllocatedMemory) {
        this.finalAllocatedMemory = finalAllocatedMemory;
    }

    public long getFinalCPUTime() {
        return finalCPUTime;
    }

    public long getInitialCPUTime() {
        return initialCPUTime;
    }

    public void setFinalCPUTime(long finalCPUTime) {
        this.finalCPUTime = finalCPUTime;
    }

    public void setInitialCPUTime(long initialCPUTime) {
        this.initialCPUTime = initialCPUTime;
    }
}

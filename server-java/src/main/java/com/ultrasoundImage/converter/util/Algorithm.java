package com.ultrasoundImage.converter.util;

public enum Algorithm {
    CGNE("CGNE"),
    CGNR("CGNR");

    private final String description;

    Algorithm(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}

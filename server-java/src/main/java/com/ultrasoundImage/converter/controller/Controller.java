package com.ultrasoundImage.converter.controller;

import com.ultrasoundImage.converter.service.ImageService;
import com.ultrasoundImage.converter.util.Algorithm;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.io.InputStream;

@RestController
@RequestMapping
public class Controller {

    private final ImageService imageService;

    public Controller(ImageService imageService){
        this.imageService = imageService;
    }

    @PostMapping(value = "/image", consumes = "application/octet-stream")
    public void process(
            @RequestParam Algorithm algorithm,
            HttpServletRequest request,
            HttpServletResponse response
    ) throws IOException
    {
        response.setHeader(
                "Content-Disposition",
                "attachment; filename=result.bin"
        );
        response.setContentType("application/octet-stream");

        imageService.process(
                algorithm,
                request.getInputStream(),
                response.getOutputStream()
        );
    }
}

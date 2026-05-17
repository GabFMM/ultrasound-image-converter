package com.ultrasoundImage.converter.controller;

import com.ultrasoundImage.converter.service.ImageService;
import com.ultrasoundImage.converter.util.Algorithm;
import com.ultrasoundImage.converter.util.ProcessResult;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.io.InputStream;
import java.time.format.DateTimeFormatter;

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

        ProcessResult processResult = imageService.process(
                algorithm,
                request.getInputStream(),
                response.getOutputStream()
        );

        response.setHeader(
                "Algorithm",
                processResult.getAlgorithm().getDescription()
        );

        response.setHeader(
                "start-time",
                processResult.getStartDateTime().format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss"))
        );

        response.setHeader(
                "start-time",
                processResult.getEndDateTime().format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss"))
        );

        response.setHeader(
                "width-pixels",
                Integer.toString(processResult.getWidthPixels())
        );

        response.setHeader(
                "height-pixels",
                Integer.toString(processResult.getHeightPixels())
        );

        response.setHeader(
                "num-iterations",
                Integer.toString(processResult.getNumIterations())
        );
    }
}

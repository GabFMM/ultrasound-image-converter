package com.ultrasoundImage.converter.controller;

import com.ultrasoundImage.converter.service.ImageService;
import com.ultrasoundImage.converter.util.Algorithm;
import com.ultrasoundImage.converter.util.ProcessResult;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.nio.file.Path;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.atomic.AtomicReference;

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

        AtomicReference<Path> outputPath = new AtomicReference<>(null);
        ProcessResult processResult = imageService.process(
                algorithm,
                request.getInputStream(),
                outputPath
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
                "end-time",
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

        imageService.toOutputStream(outputPath.get(), response.getOutputStream());
    }
}

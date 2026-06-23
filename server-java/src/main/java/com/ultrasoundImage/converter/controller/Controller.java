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
import java.util.Locale;
import java.util.concurrent.atomic.AtomicReference;

@RestController
@RequestMapping
public class Controller {

    private final ImageService imageService;

    private void setHeaders(HttpServletResponse response, ProcessResult processResult){
        response.setHeader(
                "Algorithm",
                processResult.getAlgorithm().getDescription()
        );

        response.setHeader(
                "start-time",
                processResult.getStartDateTime().format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss.SSS"))
        );

        response.setHeader(
                "end-time",
                processResult.getEndDateTime().format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss.SSS"))
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

        long initial = processResult.getInitialAllocatedMemory();
        long end = processResult.getFinalAllocatedMemory();
        response.setHeader(
                "allocated-memory",
                // transforma bytes em MB
                Long.toString((long)((end - initial) / 1e+6))
        );

        initial = processResult.getInitialCPUTime();
        end = processResult.getFinalCPUTime();
        response.setHeader(
                "cpu-time",
                // transforma ns em s
                String.format(Locale.US, "%.3f", (end - initial) / 1e+9)
        );
    }

    public Controller(ImageService imageService){
        this.imageService = imageService;
    }

    @PostMapping(value = "/image", consumes = "application/octet-stream")
    public void process(
            @RequestParam Algorithm algorithm,
            @RequestParam("num-input") int numInput,
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
                numInput,
                request.getInputStream(),
                outputPath
        );

        setHeaders(response, processResult);

        try {
            imageService.toOutputStream(outputPath.get(), response.getOutputStream());
        }
        catch (IOException e) {
            System.out.println("Envio dos dados finais foi interrompido");
        }
        finally {
            imageService.deleteTempFile(outputPath.get());

            System.out.println("Resposta enviada para o cliente");
            System.out.println("=========================================");
        }
    }
}

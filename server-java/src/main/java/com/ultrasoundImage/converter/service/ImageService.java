package com.ultrasoundImage.converter.service;

import com.ultrasoundImage.converter.util.Algorithm;
import com.ultrasoundImage.converter.util.ProcessResult;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

@Service
public class ImageService {

    // There is no risk of races,
    // as createTempFile generates a single file per client.
    private Path createTempFile(InputStream input) throws IOException {
        Path tempInput = Files.createTempFile("upload-", ".bin");
        Files.copy(input, tempInput, StandardCopyOption.REPLACE_EXISTING);
        return tempInput;
    }

    private void deleteTempFile(Path path) throws IOException {
        if(path != null)
            Files.deleteIfExists(path);
    }

    private Path signalGain(Path path){

    }

    private Path CGNR(Path path){

    }

    private Path CGNE(Path path){
        
    }

    private void toOutputStream(Path path, OutputStream outputStream) throws IOException{
        try(InputStream inputStream =
                    Files.newInputStream(path)) {

            byte[] buffer = new byte[8192];

            int bytesRead;

            while((bytesRead =
                    inputStream.read(buffer)) != -1) {

                outputStream.write(
                        buffer,
                        0,
                        bytesRead
                );
            }

            outputStream.flush();
        }
    }
    
    public ProcessResult process(Algorithm algorithm, InputStream input, OutputStream output) throws IOException {
        ProcessResult processResult = new ProcessResult();
        processResult.setAlgorithm(algorithm);

        Path inputPath = null;
        Path outputPath = null;

        try {
            inputPath = createTempFile(input);
            outputPath = signalGain(inputPath);

            if (algorithm == Algorithm.CGNE)
                outputPath = CGNE(outputPath);
            else if(algorithm == Algorithm.CGNR)
                outputPath = CGNR(outputPath);

            toOutputStream(outputPath, output);
        }
        // finally for errors (IOExceptions) or success
        finally {
            deleteTempFile(inputPath);
            deleteTempFile(outputPath);
        }

        return processResult;
    }
}

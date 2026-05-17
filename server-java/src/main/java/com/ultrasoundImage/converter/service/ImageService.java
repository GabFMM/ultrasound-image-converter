package com.ultrasoundImage.converter.service;

import com.ultrasoundImage.converter.util.Algorithm;
import com.ultrasoundImage.converter.util.ProcessResult;
import org.jblas.DoubleMatrix;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.StringTokenizer;

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

    // Possible improvement: return double[] to reduce memory cost
    private double[][] readCSV(Path path) throws IOException {
        // get number of lines
        long numLines;
        try (var lines = Files.lines(path)) {
            numLines = lines.count();
        }

        // get number of columns
        int numColumns = 0;

        try(BufferedReader br = new BufferedReader(
                new FileReader(path.toFile()),
                64 * 1024 // 64 KB per chunk
        )) {

            String line = br.readLine();
            StringTokenizer st = new StringTokenizer(line, ",");
            while (st.hasMoreTokens()) {
                numColumns++;
                st.nextToken();
            }

            // create matrix
            double[][] matrix = new double[(int) numLines][numColumns];
            int i = 0;
            int j = 0;

            do {
                st = new StringTokenizer(line, ",");
                while (st.hasMoreTokens()) {
                    String column = st.nextToken();
                    matrix[i][j] = Double.parseDouble(column);
                    j++;
                }
                j = 0;
                i++;
            }
            while ((line = br.readLine()) != null);

            return matrix;
        }
    }

    private Path signalGain(Path path){

    }

    private Path CGNR(Path path) throws IOException {
        DoubleMatrix matrixH = new DoubleMatrix(readCSV(Path.of("data/h2.csv")));
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

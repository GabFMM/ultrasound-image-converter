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

    private Path CGNE(Path signalPath) throws IOException {
        // Carregar a Matriz de Modelo (H): lê arquivo CSV e converte para uma DoubleMatrix do jblas.
        DoubleMatrix H = new DoubleMatrix(readCSV(Path.of("data/h2.csv")));

        // Carregar o Vetor de Sinal (g), assumindo que o sinal (output do signalGain) pode ser lido pelo readCSV.
        DoubleMatrix g = new DoubleMatrix(readCSV(signalPath));

        // Inicialização (Baseado nas três primeiras linhas da imagem)
        DoubleMatrix f = DoubleMatrix.zeros(H.columns, 1); // f0 = 0
        DoubleMatrix r = g.dup();                          // r0 = g - H*f0 (como f0 é 0, fica só g)
        DoubleMatrix p = H.transpose().mmul(r);            // p0 = H^T * r0

        // Configurações do loop
        double tolerance = 1e-4; // Critério de parada (ajuste se necessário)
        int maxIterations = 100; // Limite para não rodar infinitamente
        
        // Guarda o (r^T * r) inicial para usar na primeira iteração
        double rDotR = r.dot(r); 

        // Loop "until convergence"
        for (int i = 0; i < maxIterations; i++) {
            
            // alpha = (r_i^T * r_i) / (p_i^T * p_i)
            double pDotP = p.dot(p);
            double alpha = rDotR / pDotP;

            // f_{i+1} = f_i + alpha * p_i
            f.addi(p.mul(alpha));

            // r_{i+1} = r_i - alpha * H * p_i
            DoubleMatrix Hp = H.mmul(p);
            r.subi(Hp.mul(alpha));

            // Calcula o (r_{i+1}^T * r_{i+1}) da próxima iteração
            double rNextDotRNext = r.dot(r);

            // Verifica a convergência (se o erro for menor que a tolerância, o loop para)
            if (Math.sqrt(rNextDotRNext) < tolerance) {
                break;
            }

            // beta = (r_{i+1}^T * r_{i+1}) / (r_i^T * r_i)
            double beta = rNextDotRNext / rDotR;

            // p_{i+1} = H^T * r_{i+1} + beta * p_i
            DoubleMatrix HTrNext = H.transpose().mmul(r);
            p = HTrNext.add(p.mul(beta));

            // Atualiza o rDotR para o próximo ciclo do loop
            rDotR = rNextDotRNext;
        }

        // Salva o resultado (f) e retornar o Path
        return saveMatrixToTempFile(f);
    }

    /**
     * Método auxiliar para pegar a matriz resultante e salvar em um arquivo .bin,
     * permitindo que o Controller envie via outputStream.
     */
    private Path saveMatrixToTempFile(DoubleMatrix matrix) throws IOException {
        Path tempFile = Files.createTempFile("cgne-result-", ".bin");
        
        try (DataOutputStream dos = new DataOutputStream(new FileOutputStream(tempFile.toFile()))) {
            // Escreve cada número da matriz como um dado binário (double - 8 bytes)
            for (int i = 0; i < matrix.length; i++) {
                dos.writeDouble(matrix.get(i));
            }
        }
        
        return tempFile;
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

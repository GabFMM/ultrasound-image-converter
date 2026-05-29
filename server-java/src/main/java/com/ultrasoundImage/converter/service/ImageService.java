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

    private Path signalGain(Path inputPath) throws IOException {
        // Arquivo temporário para salvar o sinal com ganho
        Path outputPath = Files.createTempFile("signal-gain-", ".bin");

        int N = 64;   // Número de elementos sensores (exemplo)
        int S = 2048; // Número de amostras do sinal (exemplo)

        // DataInputStream e DataOutputStream para ler e escrever números decimais de 8 bytes (double) direto do arquivo binário
        try (DataInputStream dis = new DataInputStream(new FileInputStream(inputPath.toFile()));
             DataOutputStream dos = new DataOutputStream(new FileOutputStream(outputPath.toFile()))) {

            for (int c = 1; c <= N; c++) {
                for (int l = 1; l <= S; l++) {
                    try {
                        // Lê o valor original da amostra no arquivo de entrada
                        double gOriginal = dis.readDouble();
                        // Aplica a fórmula: 100 + (1/20) * l * raiz(l)
                        double gamma = 100.0 + (1.0 / 20.0) * l * Math.sqrt(l);
                        // Multiplica o sinal original pelo ganho
                        double gNovo = gOriginal * gamma;
                        // Escreve o novo valor no arquivo de saída
                        dos.writeDouble(gNovo);
    
                    } catch (EOFException e) {
                        // Se o arquivo acabar antes do esperado pelo tamanho de N e S, interrompemos a leitura 
                        break; 
                    }
                }
            }
        }
        return outputPath; // Retorna o caminho do novo arquivo para o próximo passo (CGNE/CGNR)
    }

    private Path CGNR(Path path) throws IOException {
        DoubleMatrix matrixH = new DoubleMatrix(readCSV(Path.of("data/h2.csv")));
        return path;
    }


    //Lê um arquivo binário de doubles e o converte para um array bidimensional (vetor coluna).
    //Ideal para ler o resultado do signalGain.
    private double[][] readBinaryVector(Path path) throws IOException {
        // Descobre quantos números (doubles) existem no arquivo
        // Cada double em Java ocupa 8 bytes
        long fileSize = Files.size(path);
        int numElements = (int) (fileSize / 8); 
        
        // Cria um vetor coluna (numElements linhas, 1 coluna)
        double[][] matrix = new double[numElements][1]; 
        
        try (DataInputStream dis = new DataInputStream(new FileInputStream(path.toFile()))) {
            for (int i = 0; i < numElements; i++) {
                matrix[i][0] = dis.readDouble();
            }
        }
        return matrix;
    }

    private Path CGNE(Path signalPath) throws IOException {
        // Carregar a Matriz de Modelo (H): usando o CSV original
        DoubleMatrix H = new DoubleMatrix(readCSV(Path.of("data/h2.csv")));

        // Carregar o Vetor de Sinal (g)
        DoubleMatrix g = new DoubleMatrix(readBinaryVector(signalPath));

        // Inicialização
        DoubleMatrix f = DoubleMatrix.zeros(H.columns, 1); 
        DoubleMatrix r = g.dup();                          
        DoubleMatrix p = H.transpose().mmul(r);            

        // Configurações do loop
        double tolerance = 1e-4; 
        int maxIterations = 100; 
        
        // Guarda o (r^T * r) inicial 
        double rDotR = r.dot(r); 

        for (int i = 0; i < maxIterations; i++) {
            double pDotP = p.dot(p);
            double alpha = rDotR / pDotP;
            // f_{i+1} = f_i + alpha * p_i
            f.addi(p.mul(alpha));
            // r_{i+1} = r_i - alpha * H * p_i
            DoubleMatrix Hp = H.mmul(p);
            r.subi(Hp.mul(alpha));
            // Calcula o (r_{i+1}^T * r_{i+1})
            double rNextDotRNext = r.dot(r);

            // CÁLCULO DO ERRO: epsilon = ||r_{i+1}||_2 - ||r_i||_2
            // A norma 2 (||x||_2) é a raiz quadrada do produto escalar (sqrt(x^T * x))
            double normaRProximo = Math.sqrt(rNextDotRNext);
            double normaRAtual = Math.sqrt(rDotR);
            double epsilon = Math.abs(normaRProximo - normaRAtual); // Math.abs para garantir que a diferença seja positiva

            // Verifica a convergência baseada no epsilon
            if (epsilon < tolerance) {
                break;
            }

            // beta = (r_{i+1}^T * r_{i+1}) / (r_i^T * r_i)
            double beta = rNextDotRNext / rDotR;
            // p_{i+1} = H^T * r_{i+1} + beta * p_i
            DoubleMatrix HTrNext = H.transpose().mmul(r);
            p = HTrNext.add(p.mul(beta));
            // Atualiza o rDotR para a próxima iteração
            rDotR = rNextDotRNext;
        }
        return saveMatrixToTempFile(f);
    }

    //Método auxiliar para pegar a matriz resultante e salvar em um arquivo .bin,
    //permitindo que o Controller envie via outputStream.
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
        Path signalPath = null;
        Path finalOutputPath = null;

        try {
            // Salva o arquivo de entrada recebido do cliente
            inputPath = createTempFile(input);
            // Aplica o ganho de sinal (gera o primeiro arquivo temporário intermediário)
            signalPath = signalGain(inputPath);
            // Aplica o algoritmo de reconstrução (gera o arquivo temporário final)
            if (algorithm == Algorithm.CGNE) {
                finalOutputPath = CGNE(signalPath);
            } else if(algorithm == Algorithm.CGNR) {
                finalOutputPath = CGNR(signalPath);
            }

            // Envia o resultado final para o cliente
            toOutputStream(finalOutputPath, output);
            
        } finally {
            // Limpa TODOS os rastros do disco do servidor
            deleteTempFile(inputPath);
            deleteTempFile(signalPath);
            deleteTempFile(finalOutputPath);
        }
        return processResult;
    }
}

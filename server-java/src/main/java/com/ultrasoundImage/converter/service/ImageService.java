package com.ultrasoundImage.converter.service;

import com.ultrasoundImage.converter.util.Algorithm;
import com.ultrasoundImage.converter.util.IntWrapper;
import com.ultrasoundImage.converter.util.ProcessResult;
import org.jblas.DoubleMatrix;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.util.Random;
import java.util.StringTokenizer;
import java.util.concurrent.atomic.AtomicReference;

@Service
public class ImageService {

    // Determina qual matriz modelo H usar
    private final int numH;

    // Usado no CGNE ou no CGNR
    private final double tolerance;
    private final int maxIterations;

    public ImageService(){
        Random random = new Random();
        // numH eh igual a 1 ou 2
        // numH = random.nextInt(2) + 1;
        numH = 2;

        tolerance = 1e-4;
        maxIterations = 10;
    }

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
        System.out.println("Início da leitura de " + path.toString());

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

            System.out.println("Fim da leitura de " + path);
            return matrix;
        }
    }

    private Path signalGain(Path inputPath) throws IOException {
        System.out.println("Iniciado ganho de sinal");

        // Arquivo temporário para salvar o sinal com ganho
        Path outputPath = Files.createTempFile("signal-gain-", ".bin");

        int N = 0; // Número de elementos sensores
        int S = 0;  // Número de amostras do sinal

        if(numH == 1){
            S = 794;
            N = 64;
        }
        else if(numH == 2){
            S = 436;
            N = 64;
        }

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
                        // Se o arquivo acabar antes do esperado pelo tamanho de N e S,
                        // interrompemos a leitura
                        System.out.println("Feito ganho de sinal");
                        // Retorna o caminho do novo arquivo para o próximo passo (CGNE/CGNR)
                        return outputPath;
                    }
                }
            }
        }

        System.out.println("Feito ganho de sinal");

        return outputPath; // Retorna o caminho do novo arquivo para o próximo passo (CGNE/CGNR)
    }

    private Path CGNR(Path signalPath, IntWrapper intWrapper) throws IOException {
        System.out.println("Iniciado CGNR");

        // Carregar a Matriz de Modelo (H): usando o CSV original
        DoubleMatrix H = new DoubleMatrix(readCSV(Path.of("data/h" + numH + ".csv")));

        // Carregar o Vetor de Sinal (g)
        DoubleMatrix g = new DoubleMatrix(readBinaryVector(signalPath));

        // Inicialização
        DoubleMatrix f = DoubleMatrix.zeros(H.columns, 1);
        DoubleMatrix r = g.dup();
        DoubleMatrix p = H.transpose().mmul(r);

        for (int i = 0; i < maxIterations; i++) {
            System.out.println("Iteração: " + (i + 1));
            // usado para o ProcessResult
            // i + 1 para trabalhar com números nesse intervalo: [1, maxIterations]
            intWrapper.setNum(i + 1);

            // pré-cálculo para evitar repetição
            double r_dot_r = r.dot(r);

            double alpha = r_dot_r / p.dot(p);

            f = f.add(p.mul(alpha));

            // mudar para H.mul(alpha).mmul(p)?
            DoubleMatrix r2 = r.sub(H.mmul(p).mul(alpha));

            double r_dot_r2 = r2.dot(r2);
            if (calcError(r_dot_r2, r_dot_r) < tolerance)
                break;

            double beta = (r2.transpose().dot(r2)) / r_dot_r;

            r = r2;

            p = H.transpose().mmul(r).add(p.mul(beta));
        }

        System.out.println("Feito CGNR");
        return saveMatrixToTempFile(f);
    }

    private Path CGNE(Path signalPath, IntWrapper intWrapper) throws IOException {
        System.out.println("Iniciado CGNE");

        // Carregar a Matriz de Modelo (H): usando o CSV original
        DoubleMatrix H = new DoubleMatrix(readCSV(Path.of("data/h" + numH + ".csv")));

        // Carregar o Vetor de Sinal (g)
        DoubleMatrix g = new DoubleMatrix(readBinaryVector(signalPath));

        // Inicialização
        DoubleMatrix f = DoubleMatrix.zeros(H.columns, 1);
        DoubleMatrix r = g.dup();
        DoubleMatrix p = H.transpose().mmul(r);

        // Guarda o (r^T * r) inicial
        double rDotR = r.dot(r);

        for (int i = 0; i < maxIterations; i++) {
            System.out.println("Iteração: " + (i + 1));
            // usado para o ProcessResult
            // i + 1 para trabalhar com números nesse intervalo: [1, maxIterations]
            intWrapper.setNum(i + 1);

            double pDotP = p.dot(p);
            double alpha = rDotR / pDotP;

            // f_{i+1} = f_i + alpha * p_i
            f.addi(p.mul(alpha));
            // r_{i+1} = r_i - alpha * H * p_i
            DoubleMatrix Hp = H.mmul(p);
            r.subi(Hp.mul(alpha));
            // Calcula o (r_{i+1}^T * r_{i+1})
            double rNextDotRNext = r.dot(r);

            // Verifica a convergência baseada no epsilon
            if (calcError(rNextDotRNext, rDotR) < tolerance) {
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

        System.out.println("Feito CGNE");
        return saveMatrixToTempFile(f);
    }

    // calcula o valor do erro das iterações dos algoritmos CGNE e CGNR
    private double calcError(double rNextDotRNext, double rDotR){
        // CÁLCULO DO ERRO: epsilon = ||r_{i+1}||_2 - ||r_i||_2
        // A norma 2 (||x||_2) é a raiz quadrada do produto escalar (sqrt(x^T * x))
        double normaRProximo = Math.sqrt(rNextDotRNext);
        double normaRAtual = Math.sqrt(rDotR);

        // return epsilon
        return Math.abs(normaRProximo - normaRAtual);
    }

    // Lê um arquivo binário de doubles e o converte para um array bidimensional (vetor coluna).
    // Ideal para ler o resultado do signalGain.
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

    // Método auxiliar para pegar a matriz resultante e salvar em um arquivo .bin,
    // permitindo que o Controller envie via outputStream.
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

    public void toOutputStream(Path path, OutputStream outputStream) throws IOException{
        if(path == null)
            return;

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
        finally {
            deleteTempFile(path);
        }
    }
    
    public ProcessResult process(
            Algorithm algorithm,
            InputStream input,
            AtomicReference<Path> finalOutputPath
    ) throws IOException {
        ProcessResult processResult = new ProcessResult();

        processResult.setAlgorithm(algorithm);
        processResult.setStartDateTime(LocalDateTime.now());

        if(numH == 1){
            processResult.setWidthPixels(60);
            processResult.setHeightPixels(60);
        }
        else if(numH == 2){
            processResult.setWidthPixels(30);
            processResult.setHeightPixels(30);
        }

        IntWrapper intWrapper = new IntWrapper(-1);

        Path inputPath = null;
        Path signalPath = null;

        try {
            // Salva o arquivo de entrada recebido do cliente
            inputPath = createTempFile(input);
            // Aplica o ganho de sinal (gera o primeiro arquivo temporário intermediário)
            signalPath = signalGain(inputPath);
            // Aplica o algoritmo de reconstrução (gera o arquivo temporário final)
            if (algorithm == Algorithm.CGNE) {
                finalOutputPath.set(CGNE(signalPath, intWrapper));
            } else if(algorithm == Algorithm.CGNR) {
                finalOutputPath.set(CGNR(signalPath, intWrapper));
            }

            processResult.setNumIterations(intWrapper.getNum());
            
        } finally {
            // Limpa TODOS os rastros do disco do servidor
            deleteTempFile(inputPath);
            deleteTempFile(signalPath);
        }

        processResult.setEndDateTime(LocalDateTime.now());
        return processResult;
    }
}

from processResult import ProcessResult
from constants import *

import datetime
import tempfile
import threading
import shutil
import math
import numpy as np
from typing import Literal
from pathlib import Path

# cria um semaforo que permite duas threads "acessa-lo"
semaphore = threading.BoundedSemaphore(value=2)

def readCSV(path: Path) -> np.ndarray:
    print(f"Início da leitura de {path}")
    matrix = np.loadtxt(path, delimiter=",", dtype=np.float64)
    print(f"Fim da leitura de {path}")
    return matrix

# Lê um arquivo binário de doubles e o converte para um array bidimensional (vetor coluna).
# Ideal para ler o resultado do signalGain.
def readBinaryVector(path: Path) -> np.ndarray:
    # Lê todos os doubles do arquivo
    vector = np.fromfile(path, dtype=np.float64)

    # Converte para vetor coluna
    return vector.reshape((-1, 1))

def CGNE(signalPath: Path, processResult: ProcessResult):
    pass

def CGNR(signalPath: Path, processResult: ProcessResult):
    print("Iniciado CGNR")

    # Carregar a Matriz de Modelo (H): usando o CSV original
    H = readCSV(Path(f"data/h{NUM_H}.csv"))

    # Carregar o Vetor de Sinal (g)
    g = readBinaryVector(signalPath)

    # Guarda a H transposta para diminuir sobrecarga
    Ht = H.T

    # Inicialização
    f = np.zeros((H.shape[1], 1), dtype=np.float64)
    r = g.copy()
    p = Ht @ r

    for i in range(MAX_ITERATIONS):
        print(f"Iteração: {i + 1}")

        # pré-cálculo para evitar repetição
        r_dot_r = np.dot(r, r)

        alpha = r_dot_r / np.dot(p, p)

        f = f + p * alpha

        r2 = r - (H @ p) * alpha

        r_dot_r2 = np.dot(r2, r2)
        if calcError(r_dot_r2, r_dot_r) < TOLERANCE:
            break

        beta = (np.dot(r2.T, r2)) / r_dot_r

        r = r2.copy()

        p = (Ht @ r) + (p * beta)

    print("Feito CGNR")
    return saveMatrixToTempFile(f)

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

# calcula o valor do erro das iterações dos algoritmos CGNE e CGNR
def calcError(rNextDotRNext: np.float64, rDotR: np.float64):
    # CÁLCULO DO ERRO: epsilon = ||r_{i+1}||_2 - ||r_i||_2
    # A norma 2 (||x||_2) é a raiz quadrada do produto escalar (sqrt(x^T * x))
    normaRProximo = math.sqrt(rNextDotRNext)
    normaRAtual = math.sqrt(rDotR)

    # return epsilon
    return math.abs(normaRProximo - normaRAtual)

def signalGain(inputPath: Path) -> Path:
    pass

# There is no risk of races,
# as createTempFile generates a single file per client
# returns the temp file path
def createTempFile(input_stream: bytes) -> Path:
    with tempfile.NamedTemporaryFile(prefix="upload-", suffix=".bin", delete=False) as temp_file:
        # Copia o conteudo do input_stream para o arquivo temporário
        shutil.copyfileobj(input_stream, temp_file)

        return Path(temp_file.name)

def deleteFile(path: Path | None):
    if path:
        path.unlink(missing_ok=True)

def process(algorithm: Literal["CGNE", "CGNR"], inputData: bytes) -> ProcessResult:
    processResult = ProcessResult()
    processResult.algorithm = algorithm
    processResult.startDateTime = datetime.now()

    if NUM_H == 1:
        processResult.heightPixels = 60
        processResult.widthPixels = 60
    elif NUM_H == 2:
        processResult.heightPixels = 30
        processResult.widthPixels = 30

    inputPath: Path | None = None
    signalPath: Path | None = None

    try:
        # Salva o arquivo de entrada recebido do cliente
        inputPath = createTempFile(inputData)

        # Aplica o ganho de sinal (gera o primeiro arquivo temporário intermediário)
        signalPath = signalGain(inputPath)

        # Usa semaforo para evitar queda do servidor
        with semaphore:
            
            # Aplica o algoritmo de reconstrução (gera o arquivo temporário final)
            if algorithm == "CGNE":
                CGNE(signalPath, processResult)
            elif algorithm == "CGNR":
                CGNR(signalPath, processResult)

    finally:
        # apaga os arquivos temporários
        deleteFile(inputPath)
        deleteFile(signalPath)

    processResult.endDateTime = datetime.now()
    return processResult
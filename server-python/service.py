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

def signalGain(inputPath: Path) -> Path:
    N = 64
    S = 2048

    # le o arquivo binário
    # '>f8' força a leitura como big-endian 
    g_original = np.fromfile(inputPath, dtype=">f8")

    l = np.arange(1, S + 1)

    # calcula o ganho (gamma) para uma coluna de amostras
    gamma = 100.0 + (1.0 / 20.0) * l * np.sqrt(l)

    # o ganho se repete para cada sensor (N)
    full_gamma = np.tile(gamma, N)

    # proteção 
    limit = min(len(g_original), len(full_gamma))

    # multiplica o sinal original pelo ganho
    g_novo = g_original[:limit] * full_gamma[:limit]

    with tempfile.NamedTemporaryFile(prefix="signal-gain-", suffix=".bin", delete=False) as temp_file:
        # Salva como '>f8' (big-endian) para o próximo passo conseguir ler
        g_novo.astype(">f8").tofile(temp_file)
        return Path(temp_file.name)
    
def CGNE(signalPath: Path, processResult: ProcessResult):
    print("Iniciado CGNE")

    # carrega a Matriz de Modelo
    H = readCSV(Path(f"data/h{NUM_H}.csv"))

    # carrega o Vetor de Sinal (g)
    g = readBinaryVector(signalPath)

    # transposta
    Ht = H.T

    f = np.zeros((H.shape[1], 1), dtype=np.float64) # f0 = 0
    r = g.copy()                                    # r0 = g
    p = Ht @ r                                      # p0 = H^T * r0

    # guarda o (r^T * r) inicial 
    r_dot_r = np.dot(r.ravel(), r.ravel())

    for i in range(MAX_ITERATIONS):
        print(f"Iteração: {i + 1}")

        p_dot_p = np.dot(p.ravel(), p.ravel())
        alpha = r_dot_r / p_dot_p

        # f_{i+1} = f_i + alpha * p_i
        f = f + p * alpha

        # r_{i+1} = r_i - alpha * H * p_i
        Hp = H @ p
        r2 = r - Hp * alpha

        r_dot_r2 = np.dot(r2.ravel(), r2.ravel())

        # verifica convergência pelo erro epsion
        if calcError(r_dot_r2, r_dot_r) < TOLERANCE:
            break

        # beta = (r_{i+1}^T * r_{i+1}) / (r_i^T * r_i)
        beta = r_dot_r2 / r_dot_r

        # p_{i+1} = H^T * r_{i+1} + beta * p_i
        p = (Ht @ r2) + (p * beta)

        # Atualiza variáveis para próxima iteração
        r = r2
        r_dot_r = r_dot_r2

    processResult.numIterations = i + 1

    print("Feito CGNE")
    return saveMatrixToTempFile(f)

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
        r_dot_r = np.dot(r.ravel(), r.ravel())

        p_dot_p = np.dot(p.ravel(), p.ravel())
        alpha = r_dot_r / p_dot_p

        f = f + p * alpha

        r2 = r - (H @ p) * alpha

        r_dot_r2 = np.dot(r2.ravel(), r2.ravel())
        if calcError(r_dot_r2, r_dot_r) < TOLERANCE:
            break

        beta = np.dot(r2.ravel(), r2.ravel()) / r_dot_r

        r = r2

        p = (Ht @ r) + (p * beta)

    processResult.numIterations = i + 1

    print("Feito CGNR")
    return saveMatrixToTempFile(f)

# Método auxiliar para pegar a matriz resultante e salvar em um arquivo .bin,
# permitindo que o Controller envie via outputStream.
def saveMatrixToTempFile(matrix: np.ndarray) -> Path:
    with tempfile.NamedTemporaryFile(prefix="cgn-result-", suffix=".bin", delete=False) as temp_file:
        # Copia o conteudo da matrix como double em big-endian para o arquivo temporário
        matrix.astype(">f8").tofile(temp_file)

        return Path(temp_file.name)

# calcula o valor do erro das iterações dos algoritmos CGNE e CGNR
def calcError(rNextDotRNext: np.float64, rDotR: np.float64):
    # CÁLCULO DO ERRO: epsilon = ||r_{i+1}||_2 - ||r_i||_2
    # A norma 2 (||x||_2) é a raiz quadrada do produto escalar (sqrt(x^T * x))
    normaRProximo = math.sqrt(rNextDotRNext)
    normaRAtual = math.sqrt(rDotR)

    # return epsilon
    return math.abs(normaRProximo - normaRAtual)

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
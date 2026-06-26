from processResult import ProcessResult
from constants import *
from appConfig import cache

import tempfile
import threading
import math
import numpy as np
from datetime import datetime
from typing import Literal
from pathlib import Path
from collections import defaultdict
import os
import psutil
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor

# obtêm um dicionário de locks para o cache
locks = defaultdict(threading.Lock)

# Lê uma matrix modelo H do cache
# Esse cache possui:
# tempo de expiração (2 minutos), é thread-safe e possui cache stampede protection
def cachedMatrix(numH: int):
    key = f"matrix:{numH}"

    value = cache.get(key)

    # cache hit
    if value is not None:
        print(f"Matrix H{numH} recuperada do cache")
        return value

    # cache miss
    # obtêm lock para cache stampede protection
    lock = locks[key]
    with lock:

        # outra thread pode ter preenchido o cache
        # enquanto esperava o lock
        value = cache.get(key)

        # cache hit
        if value is not None:
            print(f"Matrix H{numH} recuperada do cache")
            return value

        # cache miss
        print(f"Matrix H{numH} não está no cache")
        value = readCSV(Path(f"data/h{numH}.csv"))

        cache.set(key, value)

        return value

def readCSV(path: Path) -> np.ndarray:
    print(f"Início da leitura de {path}")
    matrix = np.loadtxt(path, delimiter=",", dtype=np.float64)
    print(f"Fim da leitura de {path}")
    return matrix

# Lê um arquivo binário de doubles e o converte para um array bidimensional (vetor coluna).
# Ideal para ler o resultado do signalGain.
def readBinaryVector(path: Path) -> np.ndarray:
    # Lê todos os doubles do arquivo em big-endian
    vector = np.fromfile(path, dtype=">f8")

    # Converte para vetor coluna
    return vector.reshape((-1, 1))

def signalGain(inputPath: Path, numH: int) -> Path:
    if numH == 1:
        N = 64
        S = 794
    elif numH == 2:
        N = 64
        S = 436

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
    
def CGNE(signalPath: Path, numH: int, processResult: ProcessResult):
    print("Iniciado CGNE")

    # carrega a Matriz de Modelo
    H = cachedMatrix(numH)

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

    processResult.finalOutputPath = saveMatrixToTempFile(abs(f))

    print("Feito CGNR")

def CGNR(signalPath: Path, numH: int, processResult: ProcessResult):
    print("Iniciado CGNR")

    # Carregar a Matriz de Modelo (H): usando o CSV original
    H = cachedMatrix(numH)

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

    processResult.finalOutputPath = saveMatrixToTempFile(f)

    print("Feito CGNR")

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
    return abs(normaRProximo - normaRAtual)

# There is no risk of races,
# as createTempFile generates a single file per client
# returns the temp file path
def createTempFile(input_stream: bytes) -> Path:
    with tempfile.NamedTemporaryFile(prefix="upload-", suffix=".bin", delete=False) as temp_file:
        # Copia o conteudo do input_stream para o arquivo temporário
        temp_file.write(input_stream)

        return Path(temp_file.name)

def deleteFile(path: Path | None):
    if path:
        path.unlink(missing_ok=True)

def process(algorithm: Literal["CGNE", "CGNR"], numInput: int, inputData: bytes) -> ProcessResult:
    processResult = ProcessResult()
    processResult.algorithm = algorithm
    processResult.startDateTime = datetime.now()

    if numInput >= 1 and numInput <= 3:
        numH = 1
        processResult.heightPixels = 60
        processResult.widthPixels = 60
    elif numInput >= 4 and numInput <= 6:
        numH = 2
        processResult.heightPixels = 30
        processResult.widthPixels = 30

    inputPath: Path | None = None
    signalPath: Path | None = None

    try:
        # Salva o arquivo de entrada recebido do cliente
        inputPath = createTempFile(inputData)

        # Aplica o ganho de sinal (gera o primeiro arquivo temporário intermediário)
        signalPath = signalGain(inputPath, numH)

        # Aplica o algoritmo de reconstrução (gera o arquivo temporário final)
        if algorithm == "CGNE":
            CGNE(signalPath, numH, processResult)
        elif algorithm == "CGNR":
            CGNR(signalPath, numH, processResult)

    finally:
        # apaga os arquivos temporários
        deleteFile(inputPath)
        deleteFile(signalPath)

    processResult.endDateTime = datetime.now()
    return processResult

# LÓGICA DE MULTIPROCESSAMENTO (ISOLAMENTO DE MEMÓRIA E BYPASS DO GIL)

# fábrica de processos paralelos (iniciada apenas quando necessário)
executor_pesado = None
executor_leve = None

def get_executors():
    global executor_pesado, executor_leve
    
    if executor_pesado is None or executor_leve is None:
        cpu_cores = os.cpu_count() or 1
        
        # lê apenas a memória que está livre no momento 
        ram_livre_gb = psutil.virtual_memory().available / (1024 ** 3)
        print(f"RAM Livre exata lida agora: {ram_livre_gb:.2f} GB")
        
        # deixa 1 GB de "respiro" pra tudo não travar
        ram_utilizavel = max(0, ram_livre_gb - 1.0)
        
        # calcula os workers com base apenas no que podemos usar com segurança
        # Fila Pesada (Imagens 60x60): gastam ~3.5GB
        workers_pesados = max(1, min(cpu_cores, int(ram_utilizavel // 3.5)))
        
        # Fila Leve (Imagens 30x30): gastam ~0.5GB
        workers_leves = max(1, min(cpu_cores, int(ram_utilizavel // 0.5)))
        
        print(f"\n==================================================")
        print(f"[HARDWARE] CPU Cores: {cpu_cores} | RAM Utilizável: {ram_utilizavel:.1f}GB")
        print(f"[FILA PESADA - 60x60] Capacidade para {workers_pesados} worker(s) simultâneo(s).")
        print(f"[FILA LEVE - 30x30] Capacidade para {workers_leves} worker(s) simultâneo(s).")
        print(f"==================================================\n")
        
        executor_pesado = ProcessPoolExecutor(max_workers=workers_pesados)
        executor_leve = ProcessPoolExecutor(max_workers=workers_leves)
        
    return executor_pesado, executor_leve

# operário isolado (roda em um processo limpo do SO)
def worker_isolado(algorithm, numInput, raw_data):
    # liga o monitor APENAS para este processo (livre de concorrência)
    tracemalloc.start()
    cpu_start_time = time.process_time()

    # chama a sua função original de matemática que já existe neste arquivo
    resultado = process(algorithm, numInput, raw_data)

    cpu_end_time = time.process_time()
    cpu_time_sec = cpu_end_time - cpu_start_time

    # tira a "foto" da memória consumida no pico e desliga o monitor
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    ram_mb = peak_mem / (1024 * 1024)

    # devolve o pacote completo (Imagem + Estatísticas Exatas) pro Flask
    return resultado, cpu_time_sec, ram_mb
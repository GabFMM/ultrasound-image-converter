from processResult import ProcessResult
from constants import *

import datetime
import tempfile
import threading
import shutil
from typing import Literal
from pathlib import Path

# cria um semaforo que permite duas threads "acessa-lo"
semaphore = threading.BoundedSemaphore(value=2)

def CGNE(signalPath: Path, processResult: ProcessResult):
    pass

def CGNR(signalPath: Path, processResult: ProcessResult):
    pass

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
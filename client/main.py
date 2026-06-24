import requests
import numpy as np
import threading
import random
import time
from datetime import datetime

from constants import *
from file import deleteFile, updateResultsCSV, createPDF, generateImage
from data import createTablesAndGraphics

# numInput determina qual arquivo de dados usar
def sendRequest(algorithm: str, numInput: int, timeout: int) -> requests.Response:
    params = {
        "algorithm" : algorithm,
        "num-input" : str(numInput)
    }

    g = np.loadtxt(f"input/G-{numInput}.csv", delimiter=",")

    print(f"Feita requisição com algoritmo {algorithm} e com o arquivo de dados G{numInput}")

    return requests.post(
        URL,
        params=params,
        data=g.astype(">f8").tobytes(), # envia os dados em binário em big-endian
        headers={
            "Content-Type": "application/octet-stream"
        },
        timeout=timeout
    )

def showMainInfos(response: requests.Response, numInput: int, imageFilename: str):
    # preparação para os prints
    format = "%d/%m/%Y %H:%M:%S.%f"
    initial = datetime.strptime(response.headers.get("start-time"), format)
    end = datetime.strptime(response.headers.get("end-time"), format)
    totalTime = end - initial

    # prints
    print(f"Arquivo de dados G-{numInput}:")
    print(f"-> Nome da imagem: {imageFilename}")
    print("-> Algoritmo:", response.headers.get("Algorithm"))
    print("-> Iterações:", response.headers.get("num-iterations"))
    print("-> Início:", response.headers.get("start-time"))
    print("-> Fim:", response.headers.get("end-time"))
    print(f"-> Tempo total: {totalTime.total_seconds():.3f}s")
    print(f"-> Tempo de CPU: {response.headers.get('cpu-time')}s")
    print(f"-> Memória alocada: {response.headers.get('allocated-memory')}MB")
    print("-> Altura:", response.headers.get("height-pixels"))
    print("-> Largura:", response.headers.get("width-pixels"))
    print("=" * 40)

# Para teste de carga do servidor
def test(numThreads: int, numInputs: list[int]):
    try:
        def fun():
            for input in numInputs:
                algorithm = "CGNE" if random.randint(0, 1) == 0 else "CGNR"

                response = sendRequest(algorithm, input, TIMEOUT)
            
                imageFilename = generateImage(response, algorithm, input)

                showMainInfos(response, input, imageFilename)

        threads = []

        for _ in range(numThreads):
            thread = threading.Thread(target=fun)
            thread.start()
            threads.append(thread)

        # bloqueia a thread principal de acabar antes da finalização das threads de requisição
        for thread in threads:
            thread.join()

    except(requests.exceptions.Timeout):
        print("Servidor demorou demais para responder")

# o numThreads determina quantas requisições serão feitas (1 thread por requisição)
# o overwrite indicará se o relatório final deve ser sobreescrito ou reusado
def main(numThreads: int, overwrite: bool):
    def fun():
        algorithm = "CGNE" if random.randint(0, 1) == 0 else "CGNR"

        input = random.randint(1, 6)

        response = sendRequest(algorithm, input, TIMEOUT)
    
        imageFilename = generateImage(response, algorithm, input)

        showMainInfos(response, input, imageFilename)

        updateResultsCSV(response, imageFilename)

    if overwrite:
        deleteFile("output/results.csv")

    threads = []

    for _ in range(numThreads):
        thread = threading.Thread(target=fun)
        thread.start()

        threads.append(thread)

        time.sleep(random.uniform(0, 10))

    # evita do programa terminar antes das threads terminarem de executar
    for thread in threads:
        thread.join()

    createTablesAndGraphics()
    createPDF()

if __name__ == "__main__":
    main(5, False)
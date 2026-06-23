from constants import *
import requests
from pathlib import Path
import numpy as np
import threading
import random
import uuid

import matplotlib
matplotlib.use('Agg') # 'Agg' é o backend que só salva arquivos, não abre janelas
import matplotlib.pyplot as plt

# retorna um nome de arquivo unico com UUID
# evita sobreescrever arquivos existentes
def getFilename(numInput):
    Path("output").mkdir(exist_ok=True)

    return f"output/image-from-G-{numInput}-{uuid.uuid4().hex}.jpg"

# numInput determina qual arquivo de dados usar
def sendRequest(algorithm: str, numInput: int, timeout: int) -> requests.Response:
    params = {
        "algorithm" : algorithm,
        "num-input" : str(numInput)
    }

    g = np.loadtxt(f"input/G-{numInput}.csv", delimiter=",")

    return requests.post(
        URL,
        params=params,
        data=g.astype(">f8").tobytes(), # envia os dados em binário em big-endian
        headers={
            "Content-Type": "application/octet-stream"
        },
        timeout=timeout
    )

def generateImage(response: requests.Response, algorithm: str, numInput: int):
    # recuperar Altura/Largura
    height = response.headers.get("height-pixels")
    width = response.headers.get("width-pixels")

    if not height or not width:
        print("Altura ou largura são inválidos e são None")
        return

    height, width = int(height), int(width)

    # recuperar matriz binária (mantenha a lógica Column-Major que desvira a imagem)
    img = np.frombuffer(response.content, dtype=">f8")
    img = img.reshape((height, width), order='F')

    # configurar o Plot de Alta Resolução (Matplotlib)
    fig, ax = plt.subplots(figsize=(6, 6), dpi=100) # Cria uma figura quadrada decente
    ax.set_title(f"Reconstrução G-{numInput} com {algorithm}")

    # mostrar imagem 
    # interpolation='bicubic'suaviza os pixels 60x60
    im = ax.imshow(img, cmap='gray', interpolation='nearest', extent=[1, width, height, 1])

    # eixos 
    ax.set_xticks(np.arange(10, width + 1, 10))
    ax.set_yticks(np.arange(10, height + 1, 10))

    # salvar a figura no disco
    filename = getFilename(numInput) 
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    fig.clear()
    plt.close(fig)

    print(f"-> Imagem de alta qualidade (suavizada) salva em: {filename}")

def showMainInfos(response: requests.Response, numInput: int):
    print(f"Arquivo de dados G-{numInput}:")
    print("-> Algoritmo:", response.headers.get("Algorithm"))
    print("-> Iterações:", response.headers.get("num-iterations"))
    print("-> Início:", response.headers.get("start-time"))
    print("-> Fim:", response.headers.get("end-time"))
    print(f"-> Memória alocada: {response.headers.get('allocated-memory')}MB")
    print("-> Altura:", response.headers.get("height-pixels"))
    print("-> Largura:", response.headers.get("width-pixels"))
    print("=" * 40)

# Para teste de carga do servidor
def mainTest(numThreads: int, numInputs: list[int]):
    try:
        def fun():
            for input in numInputs:
                algorithm = "CGNE" if random.randint(0, 1) == 0 else "CGNR"

                response = sendRequest(algorithm, input, TIMEOUT)
            
                generateImage(response, algorithm, input)

                showMainInfos(response, input)

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

# Apenas para desenvolvimento
def test():
    try:
        response = sendRequest(ALGORITHM, NUM_INPUT, TIMEOUT)
    
        generateImage(response, ALGORITHM, NUM_INPUT)

        showMainInfos(response, NUM_INPUT)      

    except(requests.exceptions.Timeout):
        print("Servidor demorou demais para responder")

if __name__ == "__main__":
    mainTest(2, [1, 2, 3, 4, 5, 6])
from constants import *

import requests
from pathlib import Path
from PIL import Image
import numpy as np
import cv2

# retorna um nome de arquivo unico
# evita sobreescrever arquivos existentes 
def getFilename(numInput: int) -> str:
    attempts = 0

    name = f"output/image-from-G-{numInput}"
    ext = ".jpg"
    path = Path(name + ext)

    while path.is_file():
        attempts += 1
        path = Path(f"{name}({attempts}){ext}")

    # cria a pasta output se nao existir
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.as_posix()

# numInput determina qual arquivo de dados usar
def sendRequest(algorithm: str, numInput: int, timeout: int) -> requests.Response:
    param = {
        "algorithm" : algorithm
    }

    g = np.loadtxt(f"input/G-{numInput}.csv", delimiter=",")

    return requests.post(
        URL,
        params=param,
        data=g.astype(">f8").tobytes(), # envia os dados em binário em big-endian
        headers={
            "Content-Type": "application/octet-stream"
        },
        timeout=timeout
    )

def generateImage(response: requests.Response, numInput: int):
    height = response.headers.get("height-pixels")
    width = response.headers.get("width-pixels")

    if height and width:
        height = int(height)
        width = int(width)

        # salva o arquivo retornado
        # >f8 significa para interpretar o response.content como doubles em big-endian
        # o big-endian eh determinado pelo DataOutputStream do server Java
        img = np.frombuffer(response.content, dtype=">f8")
        
        img = img.reshape((height, width))

        # normaliza valores entre 0 e 1
        img = (img - img.min()) / (img.max() - img.min())
        
        # transforma valores entre 0 e 255
        img = (img * 255).astype(np.uint8)

        filename = getFilename(numInput)
        Image.fromarray(img).save(filename)

        enlargeImage(filename)
    else:
        print("Altura ou largura sao invalidos e sao None")

def enlargeImage(filename: str):
    # Carrega a imagem em escala de cinza (0 a 255)
    # O argumento 0 garante que o OpenCV leia exatamente como matriz única (tons de cinza)
    img = cv2.imread(filename, 0)

    height, width = img.shape

    newSize = (height * 12, width * 12)

    # Redimensiona usando Lanczos
    enlargedImg = cv2.resize(img, newSize, interpolation=cv2.INTER_LANCZOS4)

    # remove "output/"
    filename = filename[7:]

    # Salva o resultado
    cv2.imwrite(f"output/enlarged-{filename}", enlargedImg)

def showMainInfos(response: requests.Response, numInput: int):
    print(f"Arquivo de dados G-{numInput}:")
    print("-> Algoritmo:", response.headers.get("Algorithm"))
    print("-> Iterações:", response.headers.get("num-iterations"))
    print("-> Início:", response.headers.get("start-time"))
    print("-> Fim:", response.headers.get("end-time"))
    print("-> Altura:", response.headers.get("height-pixels"))
    print("-> Largura:", response.headers.get("width-pixels"))
    print("=" * 40)

if __name__ == "__main__":
    try:
        numInputs = [3]
        for numInput in numInputs:
            response = sendRequest(ALGORITHM, numInput, TIMEOUT)
            
            generateImage(response, numInput)

            showMainInfos(response, numInput)

    except(requests.exceptions.Timeout):
        print("Servidor demorou demais para responder")
    
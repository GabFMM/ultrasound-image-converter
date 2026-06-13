from constants import *

import requests
from pathlib import Path
from PIL import Image
import numpy as np

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

if __name__ == "__main__":
    param = {
        "algorithm" : ALGORITHM
    }

    try:
        g = np.loadtxt(f"input/G-{NUM_INPUT}.csv", delimiter=",")

        response = requests.post(
            URL,
            params=param,
            data=g.astype(">f8").tobytes(), # envia os dados em binário mesmo em big-endian
            headers={
                "Content-Type": "application/octet-stream"
            },
            timeout=120
        )
        
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

            Image.fromarray(img).save(getFilename(NUM_INPUT))

        # lê os headers enviados pelo servidor
        print("Algoritmo:", response.headers.get("Algorithm"))
        print("Iterações:", response.headers.get("num-iterations"))
        print("Início:", response.headers.get("start-time"))
        print("Fim:", response.headers.get("end-time"))
        print("Altura:", height)
        print("Largura:", width)

    except(requests.exceptions.Timeout):
        print("Servidor demorou demais para responder")
    
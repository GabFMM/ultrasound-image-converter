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
        with open(f"input/G-{NUM_INPUT}.csv", "rb") as f:
            response = requests.post(
                URL,
                params=param,
                data=f,
                headers={
                    "Content-Type": "application/octet-stream"
                },
                timeout=120
            )
        
        height = response.headers.get("height-pixels")
        width = response.headers.get("width-pixels")

        if height is str and width is str:
            height = int(height)
            width = int(width)

            # salva o arquivo retornado
            img = np.frombuffer(response.content, dtype=np.float64)
            img = img.reshape((height, width))

            img = np.clip(img * 255, 0, 255).astype(np.uint8)

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
    
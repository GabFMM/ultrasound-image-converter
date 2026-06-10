from constants import *

import requests
from pathlib import Path

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

    with open(f"input/G-{NUM_INPUT}.csv", "rb") as f:
        response = requests.post(
            URL,
            params=param,
            data=f,
            headers={
                "Content-Type": "application/octet-stream"
            }
        )
    
    # salva o arquivo retornado
    with open(getFilename(NUM_INPUT), "wb") as out:
        out.write(response.content)

    # lê os headers enviados pelo servidor
    print("Algoritmo:", response.headers.get("Algorithm"))
    print("Iterações:", response.headers.get("num-iterations"))
    print("Início:", response.headers.get("start-time"))
    print("Fim:", response.headers.get("end-time"))
    print("Largura:", response.headers.get("width-pixels"))
    print("Altura:", response.headers.get("height-pixels"))
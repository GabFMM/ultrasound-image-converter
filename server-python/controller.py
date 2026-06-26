from flask import request, Response, jsonify
import time
import tracemalloc
from threading import Lock

import service
from appConfig import app

# catraca global para isolar a medição de memória
memory_lock = Lock()

@app.route("/image", methods=["POST"])
def process():
    # checa se o formato do header ta certinho
    contentType = request.headers.get("Content-Type")
    if contentType != "application/octet-stream":
        return jsonify({"error": "Header inválido. Esperado application/octet-stream"}), 400

    # pega o algoritmo que o cliente mandou (default eh CGNE)
    algorithm = request.args.get("algorithm", default="CGNE", type=str)

    if algorithm not in ("CGNE", "CGNR"):
        return jsonify({"error": "Algoritmo inválido, esperado CGNE ou CGNR"}), 400

    # pega o input pra saber o tamanho da imagem
    numInput = request.args.get("num-input", default=4, type=int)

    # 1 requisição passa por vez
    with memory_lock:
        tracemalloc.start()
        cpu_start_time = time.process_time()

        # faz o trabalho pesado de reconstrução da matriz
        processResult = service.process(algorithm, numInput, request.get_data())

        cpu_end_time = time.process_time()
        cpu_time_sec = (cpu_end_time - cpu_start_time)

        # salva o pico e desliga o monitor sem que outra thread interfira
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    # converte de bytes pra MB
    ram_allocated_mb = peak_mem / (1024 * 1024)

    # arruma as datas pro formato especifico que o cliente ta esperando
    if processResult.startDateTime is None:
        startDateTime = "Error"
    else:
        startDateTime = processResult.startDateTime.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

    if processResult.endDateTime is None:
        endDateTime = "Error"
    else:
        endDateTime = processResult.endDateTime.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

    # manda os dados com as chaves que o file.py lê
    headers = {
        "algorithm": processResult.algorithm,
        "num-iterations": str(processResult.numIterations),
        "start-time": startDateTime,
        "end-time": endDateTime,
        "height-pixels": str(processResult.heightPixels),
        "width-pixels": str(processResult.widthPixels),
        "cpu-time": f"{cpu_time_sec:.3f}",
        "allocated-memory": f"{ram_allocated_mb:.3f}"
    }

    # Lê os bytes para a memória, deleta o arquivo físico e envia (Bypass do Windows)
    with open(processResult.finalOutputPath, 'rb') as f:
        file_bytes = f.read()

    service.deleteFile(processResult.finalOutputPath)

    response = Response(
        file_bytes,
        mimetype="application/octet-stream"
    )
    
    response.headers["Content-Disposition"] = "attachment; filename=result.bin"
    response.headers.extend(headers)

    return response
from flask import request, Response, jsonify
import os

import service
from appConfig import app

@app.route("/image", methods=["POST"])
def process_image():
    # valida o tipo do conteudo
    contentType = request.headers.get("Content-Type")
    if contentType != "application/octet-stream":
        return jsonify({"error": "Header inválido. Esperado application/octet-stream"}), 400

    # recupera o algoritmo e o input
    algorithm = request.args.get("algorithm", default="CGNE", type=str)
    if algorithm not in ("CGNE", "CGNR"):
        return jsonify({"error": "Algoritmo inválido, esperado CGNE ou CGNR"}), 400

    numInput = request.args.get("num-input", default=4, type=int)

    # delegação inteligente: vai pra pool certa
    pool_pesada, pool_leve = service.get_executors()
    
    # Se for imagem grande (G1, G2, G3 - numInput de 1 a 3) vai pra Fila Pesada
    if 1 <= numInput <= 3:
        # O Flask agenda a tarefa e fica esperando a resposta (future.result)
        future = pool_pesada.submit(service.worker_isolado, algorithm, numInput, request.get_data())
    # Se for imagem pequena (G4, G5, G6 - numInput de 4 a 6) vai pra Fila Leve
    else:
        future = pool_leve.submit(service.worker_isolado, algorithm, numInput, request.get_data())
        
    processResult, cpu_time_sec, ram_allocated_mb = future.result()

    # arruma as datas pro formato do cliente
    if processResult.startDateTime is None:
        startDateTime = "Error"
    else:
        startDateTime = processResult.startDateTime.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

    if processResult.endDateTime is None:
        endDateTime = "Error"
    else:
        endDateTime = processResult.endDateTime.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

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

    # Bypass do Windows: Lê para a RAM e deleta o físico antes de enviar
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
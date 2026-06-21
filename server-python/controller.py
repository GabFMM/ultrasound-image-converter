from flask import request, Response, jsonify, send_file, after_this_request

import service
from appConfig import app

@app.route("/image", methods=["POST"])
def process():

    # valida o tipo do conteudo
    contentType = request.headers.get("Content-Type")
    if contentType != "application/octet-stream":
        return jsonify({"error": "Header inválido. Esperado application/octet-stream"}), 400

    # recupera o algoritmo requisitado
    algorithm = request.args.get("algorithm", default="CGNE", type=str)

    if algorithm not in ("CGNE", "CGNR"):
        return jsonify({"error": "Algoritmo inválido, esperado CGNE ou CGNR"}), 400

    # recupera os dados de sinais de entrada
    numInput = request.args.get("num-input", default=4, type=int)

    processResult = service.process(algorithm, numInput, request.get_data())

    if processResult.startDateTime is None:
        startDateTime = "Error"
    else:
        startDateTime = processResult.startDateTime.strftime("%d/%m/%Y %H:%M:%S")

    if processResult.endDateTime is None:
        endDateTime = "Error"
    else:
        endDateTime = processResult.endDateTime.strftime("%d/%m/%Y %H:%M:%S")

    headers = {
        "algorithm": processResult.algorithm,
        "num-iterations": processResult.numIterations,
        "start-time": startDateTime,
        "end-time": endDateTime,
        "height-pixels": processResult.heightPixels,
        "width-pixels": processResult.widthPixels
    }

    @after_this_request
    def cleanup(response: Response) -> Response:  
        service.deleteFile(processResult.finalOutputPath)
        return response

    response = send_file(
        processResult.finalOutputPath,
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="result.bin"
    )

    response.headers.extend(headers)

    return response
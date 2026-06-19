from flask import Flask, request, jsonify, send_file

import service
from processResult import ProcessResult

app = Flask(__name__)

@app.route("/image", methods=["POST"])
def process():

    # valida o tipo do conteudo
    contentType = request.headers.get("Content-Type")
    if contentType != "application/octet-stream":
        return jsonify({"error": "Header inválido. Esperado application/octet-stream"}), 400

    # recupera o algoritmo requisitado
    algorithm = request.args.get("algorithm", default="CGNE", type=str)

    processResult: ProcessResult = service.process(algorithm, request.get_data())

    headers = {
        "algorithm": processResult.algorithm,
        "num-iterations": processResult.numIterations,
        "start-time": processResult.startDateTime.strftime("%d/%m/%Y %H:%M:%S"),
        "end-time": processResult.endDateTime.strftime("%d/%m/%Y %H:%M:%S"),
        "height-pixels": processResult.heightPixels,
        "width-pixels": processResult.widthPixels
    }

    @after_this_request
    def cleanup(response):  
        service.deleteFile(processResult.finalOutputPath)
        return response

    return send_file(
        processResult.finalOutputPath.read_bytes(),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name='result.bin',
        headers=headers
    )
# Módulo que contêm funções para criação de arquivos

import threading
import requests
import csv
import uuid
import base64
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg') # 'Agg' é o backend que só salva arquivos, não abre janelas
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from constants import URL

lockCSV = threading.Lock()

def deleteFile(path: str):
    filePath = Path(path)
    filePath.unlink(missing_ok=True)

# retorna um nome de arquivo unico com UUID
# evita sobreescrever arquivos existentes
def getFilename(numInput):
    # Gera o UUID em bytes e compacta em Base64 (22 chars)
    uuid_bytes = uuid.uuid4().bytes
    uuid_curto = base64.urlsafe_b64encode(uuid_bytes).rstrip(b'=').decode('ascii')
    
    return f"image-from-G{numInput}-{uuid_curto}.jpg"

# Usado em data.py
def createPDF():
    # pagesize=letter determina o tamanho das páginas para A4
    doc = SimpleDocTemplate("output/report.pdf", pagesize=letter)

    elements = []

    # Configuração de Estilos de Texto
    styles = getSampleStyleSheet()

    titleStyle = ParagraphStyle(
        'TituloCustomizado',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        leading=28,
        textColor=colors.HexColor("#000000"),
        spaceAfter=20
    )

    tableStyle = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0C005B")), # Cor de fundo do cabeçalho
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),             # Cor do texto do cabeçalho
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),                         # Alinha tudo no centro
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),               # Negrito no cabeçalho
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),                         # Espaçamento interno do cabeçalho
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")), # Cor de fundo das linhas de dados
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),   # Linhas da tabela (bordas)
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ])

    elements.append(Paragraph("Relatório de Desempenho", titleStyle))
    elements.append(Spacer(1, 15)) # Dá um espaço vertical de 15 pontos

    # Tabelas
    table1 = Table(readCSV("data/general-table.csv"), colWidths=[120, 120, 120, 120, 120])
    table1.setStyle(tableStyle)

    elements.append(table1)
    elements.append(Spacer(1, 15)) # Espaço maior antes de começarem os gráficos

    table2 = Table(readCSV("data/algorithm-table.csv"), colWidths=[100, 100, 100])
    table2.setStyle(tableStyle)

    elements.append(table2)
    elements.append(Spacer(1, 30)) # Espaço maior antes de começarem os gráficos

    # Gráficos
    elements.append(Image("data/avg-total-time.png", height=350, width=450))
    elements.append(Spacer(1, 15))
    elements.append(Image("data/avg-cpu-time.png", height=350, width=450))
    elements.append(Spacer(1, 15))
    elements.append(Image("data/avg-allocated-memory.png", height=350, width=450))

    doc.build(elements)

# usado no main.py
def updateResultsCSV(response: requests.Response, imageFilename: str):
    with lockCSV:
        # preparação para os dados
        format = "%d/%m/%Y %H:%M:%S.%f"
        initial = datetime.strptime(response.headers.get("start-time"), format)
        end = datetime.strptime(response.headers.get("end-time"), format)
        totalTime = end - initial

        server = "Spring" if "8080" in URL else "Flask"

        # cria o diretório data se não existir
        dataDirectory = Path("data/")
        dataDirectory.mkdir(parents=True, exist_ok=True)

        filePath = "data/results.csv"
        fileExists = os.path.exists(filePath) and os.path.getsize(filePath) > 0

        with open(filePath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Se o arquivo for novo, escreve o cabeçalho primeiro
            if not fileExists:
                writer.writerow([
                    "image_filename", "algorithm", "num_iterations", 
                    "total_time", "cpu_time", "allocated_memory", 
                    "height_pixels", "width_pixels", "server"
                ])
            
            # Escreve os dados
            writer.writerow([
                imageFilename,
                response.headers.get("algorithm"),
                response.headers.get("num-iterations"),
                f"{totalTime.total_seconds():.3f}",
                response.headers.get('cpu-time'),
                response.headers.get('allocated-memory'),
                response.headers.get("height-pixels"),
                response.headers.get("width-pixels"),
                server
            ])

def readCSV(path: str) -> list[list[str]]:
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # O csv.reader já lê cada linha como uma lista de strings
        return list(reader)

# returns the image filename
def generateImage(response: requests.Response, algorithm: str, numInput: int) -> str:
    # recuperar Altura/Largura
    height = response.headers.get("height-pixels")
    width = response.headers.get("width-pixels")

    if not height or not width:
        print("Altura ou largura são inválidos e são None")
        return ""

    height, width = int(height), int(width)

    # recuperar matriz binária (mantenha a lógica Column-Major que desvira a imagem)
    img = np.frombuffer(response.content, dtype=">f8")
    img = img.reshape((height, width), order='F')

    # configurar o Plot de Alta Resolução (Matplotlib)
    fig, ax = plt.subplots(figsize=(6, 6), dpi=100) # Cria uma figura quadrada decente
    ax.set_title(f"Reconstrução G-{numInput} com {algorithm}")

    # mostrar imagem 
    # interpolation='bicubic'suaviza os pixels 60x60
    ax.imshow(img, cmap='gray', interpolation='nearest', extent=[1, width, height, 1])

    # eixos 
    ax.set_xticks(np.arange(10, width + 1, 10))
    ax.set_yticks(np.arange(10, height + 1, 10))

    # salva a figura no disco
    filename = getFilename(numInput)

    # cria os diretórios output e images se não existirem
    path = Path(f"output/images/{filename}") 
    path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(path, dpi=150, bbox_inches='tight')
    fig.clear()
    plt.close(fig)

    return filename
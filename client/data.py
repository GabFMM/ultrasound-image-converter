# Módulo para análise de dados disponibilizados em output/results.csv

import pandas as pd
import matplotlib
matplotlib.use('Agg') # 'Agg' é o backend que só salva arquivos, não abre janelas
import matplotlib.pyplot as plt

def createTablesAndGraphics():
    df = pd.read_csv("data/results.csv")

    # Reinterpretação dos tipos de dados (string para um tipo numérico)
    df["total_time"] = df["total_time"].astype(float)
    df["cpu_time"] = df["cpu_time"].astype(float)
    df["allocated_memory"] = df["allocated_memory"].astype(float)
    df["num_iterations"] = df["num_iterations"].astype(int)

    # Gráficos
    df.groupby("server")["total_time"].mean().round(3).plot(kind="bar")
    plt.ylabel("Tempo (s)")
    plt.xlabel("Servers")
    plt.title("Tempo total médio de reconstrução")
    plt.savefig("data/avg-total-time.png")
    plt.close()

    df.groupby("server")["cpu_time"].mean().round(3).plot(kind="bar")
    plt.ylabel("Tempo (s)")
    plt.xlabel("Servers")
    plt.title("Tempo de CPU médio de reconstrução")
    plt.savefig("data/avg-cpu-time.png")
    plt.close()

    df.groupby("server")["allocated_memory"].mean().round(3).plot(kind="bar")
    plt.ylabel("Memória alocada (MB)")
    plt.xlabel("Servers")
    plt.title("Custo de memória RAM médio de reconstrução")
    plt.savefig("data/avg-allocated-memory.png")
    plt.close()

    # Tabelas
    (df.groupby("server")
   .agg({
       "total_time": "mean",
       "cpu_time": "mean",
       "allocated_memory": "mean",
       "num_iterations": "mean"
   })
   .rename(columns=lambda x: f"avg_{x}")
   .round(3)
   .to_csv("data/general-table.csv"))

    (df.groupby(["server", "algorithm"])["total_time"]
   .mean()
   .round(3)
   .reset_index(name="avg_total_time")
   # index=False evita uma coluna extra de IDs
   .to_csv("data/algorithm-table.csv", index=False))
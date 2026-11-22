import sqlite3
from pathlib import Path

import pandas as pd

raiz = Path(__file__).resolve().parent.parent
arquivos = sorted((raiz / "data" / "raw").glob("*.xlsx"))
caminho_banco = raiz / "data" / "db" / "crimes.db"

abas = []
for arquivo in arquivos:
    print("Lendo", arquivo.name)
    abas.extend(pd.read_excel(arquivo, sheet_name=None).values())
df = pd.concat(abas, ignore_index=True)
print("Linhas lidas:", len(df))

df["municipio"] = df["municipio"].str.strip().str.upper()
df["evento"] = df["evento"].str.strip()
df["data_referencia"] = pd.to_datetime(df["data_referencia"])
df["metrica"] = None
df.loc[df["total"].notna(), "metrica"] = "total"
df.loc[df["total_vitima"].notna(), "metrica"] = "vítimas"
df.loc[df["total_peso"].notna(), "metrica"] = "peso"
df["quantidade"] = df["total_vitima"].fillna(df["total"])
df = df.rename(columns={"total_peso": "peso"})

df = df.dropna(subset=["quantidade", "peso"], how="all")
print("Linhas com valor:", len(df))
print(df.groupby("evento")["metrica"].nunique().value_counts())
df["metrica"] = df.groupby("evento")["metrica"].transform("first")

chave = ["uf", "municipio", "evento", "metrica", "data_referencia", "agente", "arma", "faixa_etaria", "abrangencia"]
valores = ["feminino", "masculino", "nao_informado", "quantidade", "peso"]
df = df.groupby(chave, dropna=False, as_index=False)[valores].sum(min_count=1)
print("Linhas após agrupar repetidas:", len(df))

df["ano"] = df["data_referencia"].dt.year
df["mes"] = df["data_referencia"].dt.month
df["data_referencia"] = df["data_referencia"].dt.strftime("%Y-%m-%d")
for coluna in ["feminino", "masculino", "nao_informado", "quantidade"]:
    df[coluna] = df[coluna].astype("Int64")

colunas = ["uf", "municipio", "evento", "metrica", "ano", "mes", "data_referencia", "abrangencia",
           "agente", "arma", "faixa_etaria", "feminino", "masculino", "nao_informado",
           "quantidade", "peso"]
df = df[colunas]

caminho_banco.parent.mkdir(parents=True, exist_ok=True)
conexao = sqlite3.connect(caminho_banco)
df.to_sql("ocorrencias", conexao, if_exists="replace", index=False, chunksize=50000)
conexao.execute("CREATE INDEX idx_evento_data ON ocorrencias (evento, ano, mes)")
conexao.execute("CREATE INDEX idx_uf_municipio ON ocorrencias (uf, municipio)")
conexao.commit()
conexao.close()
print("Banco criado em", caminho_banco)

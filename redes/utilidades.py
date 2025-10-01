# src/utils.py
import hashlib #biblio q calcula hash (transforma dados em strings de tamanho fixo)
import time
import os
import json

def sha256_file(path): #calcula o hash sha256 de um arquivo
    h = hashlib.sha256() 
    with open(path, "rb") as f: #abre o arquivo em modo leitura binaria
        for chunk in iter(lambda: f.read(1024 * 1024), b""): #lê o arquivo em pedaços de 1MB
            h.update(chunk)
    return h.hexdigest()

def now_ts(): #retorna o timestamp atual
    return int(time.time()) 

def safe_join(root, rel): # junta dois caminhos de forma segura
    # Evita paths fora do diretório raiz
    rel = rel.lstrip("/").replace("..", "")
    return os.path.abspath(os.path.join(root, rel))

def read_json(path, default): #lê um arquivo json e retorna o conteúdo como dicionário
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data): #escreve um dicionário em um arquivo json
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

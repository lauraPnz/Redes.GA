# main.py
import argparse #é uma biblio que processa argumentos da linha de comando
import time # Importar time
from utilidades import read_json
from status_node import NodeState
from servidor import UDPServer 
from cliente import sync_loop 
import threading

def main(): 
    parser = argparse.ArgumentParser(description="P2P File Sync (UDP)") #descrição do programa
    parser.add_argument("--config", required=True, help="Caminho para o arquivo de configuração")
    args = parser.parse_args()

    cfg = read_json(args.config, None)
    if not cfg:
        raise SystemExit("Erro ao ler arquivo de configuração.")

    state = NodeState(cfg) #cria o estado do nó
    
    server_thread = UDPServer(state) 
    client_thread = threading.Thread(target=sync_loop, args=(state,), daemon=True)

    # Inicia PRIMEIRO o servidor para que ele possa receber conexões
    server_thread.start()
    
    
    print("Aguardando 5 segundos para a rede estabilizar...")
    time.sleep(5)  # Pausa de 5 segundos

    # Inicia o cliente, que começará a procurar outros peers
    client_thread.start()

    print(f"[OK] Nó {state.node_id} (Porta UDP: {state.port}) iniciado. Diretório: {state.directory}") #status do nó
    print(f"Pressione Ctrl+C para encerrar.")
    
    try:
        server_thread.join() #aguarda o término da thread do servidor
    except KeyboardInterrupt:
        print("\nEncerrando...")
        server_thread.stop()

if __name__ == "__main__":
    main()
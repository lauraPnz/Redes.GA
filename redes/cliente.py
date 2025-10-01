# cliente.py
import socket #biblio para comunicação d redes
import json   #codificar e decodificar dados JSON
import time   #usei para as pausas sleep de 5 segundos no loop de sincronização
import os     #interagir com o sistema operacional (arquivos e diretórios)

MAX_DATAGRAM_SIZE = 65507 #Tamanho máximo de um datagrama UDP 
TIMEOUT = 5               # Tempo de espera para respostas UDP em segundos
MAX_RETRIES = 3           # Número máximo de tentativas para requisições UDP

def udp_request(peer_address, command: str): # Função para enviar requisições UDP e receber respostas
    server_host, server_port = peer_address.split(':') #endereço do peer dividio em host e porta
    server_addr = (server_host, int(server_port)) #tupla (host, porta) para o socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket: #af_inet é do protocolo ipv4, sock_dgram é do protocolo udp
        client_socket.settimeout(TIMEOUT)
        request_message = f"{command}|".encode('utf-8')
        for attempt in range(MAX_RETRIES): #tenta enviar a requisição n(max_retires) vezes se necessário
            try:
                client_socket.sendto(request_message, server_addr)  #tenta enviar a mensagem pro servidor
                response_data, _ = client_socket.recvfrom(MAX_DATAGRAM_SIZE) #tenta receber a resposta
                response_message = response_data.decode('utf-8') #decodifica a resposta byte ou str
                res_parts = response_message.split('|', 1) #divide a resposta em comando e dados json
                return res_parts[0], json.loads(res_parts[1]) if len(res_parts) > 1 else {} #retorna o comando e os dados json decodificados
            except socket.timeout:
                continue
    raise TimeoutError(f"Nenhuma resposta de {peer_address}")

def udp_get_file_content(peer_address, filename: str) -> bytes: #baixa o conetudo do peer via udp 
    server_host, server_port = peer_address.split(':') #que nem o anterior, divide em host e porta
    server_addr = (server_host, int(server_port))
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as file_socket: #cria o socket udp
        file_socket.settimeout(TIMEOUT)
        request_message = f"FILE_REQ|{filename}".encode('utf-8')
        
        chunks = {} #dicionario para armazenar os pedaços do arquivo
        total_chunks = -1

        for attempt in range(MAX_RETRIES): #tenta n vezes se necessário(eh um loop)
            try:
                file_socket.sendto(request_message, server_addr)
                while True: #loop infinito, só sai quando o arquivo for completamente baixado ou der erro
                    packet, source_addr = file_socket.recvfrom(MAX_DATAGRAM_SIZE)
                    if source_addr[0] != server_addr[0]: continue
                    # Divide o pacote em comando, sequência, total e dados
                    parts = packet.split(b'|', 3)
                    command = parts[0].decode('utf-8')
                    
                    if command == "FILE_CHUNK": #se o comando for FILE_CHUNK, significa que é um pedaço do arquivo
                        seq, total, data_chunk = int(parts[1]), int(parts[2]), parts[3]
                        if total_chunks == -1: total_chunks = total
                        if seq not in chunks: chunks[seq] = data_chunk 
                        
                        ack_message = f"ACK|{seq}".encode('utf-8')
                        file_socket.sendto(ack_message, source_addr) #envia o ack pro peer

                        if len(chunks) == total_chunks:
                            return b"".join(chunks[i] for i in sorted(chunks.keys())) #junta os pedaços e retorna o arquivo completo
                    elif command == "FILE_ERR":
                        raise ConnectionAbortedError(f"Erro no servidor: {parts[1].decode('utf-8')}")
            except socket.timeout:
                continue
        raise TimeoutError(f"Falha no download de {filename} após {MAX_RETRIES} tentativas.")

def sync_loop(state): # Função principal do loop de sincronização
    while True:
        try:
            state.scan_and_update_meta()
            print(f"\n[{state.node_id}] Iniciando ciclo de sincronização...")

            for peer in state.peers: #para cada peer na lista de peers
                try:
                    res_cmd, idx = udp_request(peer, "INDEX_REQ")  #pede o index pro peer
                    if res_cmd != "INDEX_RSP": continue

                    rfiles = idx.get("files", {}) #pega os arquivos do index recebido
                    for name, info in rfiles.items():
                        r_mtime, r_hash = int(info.get("mtime", 0)), info.get("sha256") #pega o mtime e o hash do arquivo
                        
                        if state.need_download(name, r_mtime, r_hash, peer): #verifica se precisa baixar o arquivo
                            print(f"[{state.node_id}] ⬇️  Baixando: {name} de {peer}...")
                            try:
                                data = udp_get_file_content(peer, name) #tenta baixar o arquivo
                                 #salva o arquivo baixado no diretório local
                                state.save_downloaded_file(name, data, r_mtime)
                                print(f"[{state.node_id}] ✅ Arquivo {name} baixado e salvo com sucesso.")
                            except Exception as e:
                                print(f"[{state.node_id}] ❌ ERRO no download de {name}: {e}")
                except Exception as e:
                    print(f"[{state.node_id}] Falha ao sincronizar com peer {peer}: {e}")
            
        except Exception as e:
            print(f"[{state.node_id}] ERRO geral no sync loop: {e}")
            
        time.sleep(state.sync_interval)
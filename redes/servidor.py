# servidor.py
import socket
import threading #biblio que permite criar threads
import json
import os
import math
from status_node import NodeState 

MAX_DATAGRAM_SIZE = 65507 
CHUNK_SIZE = 1400      #Tamanho do chunk para transferência de arquivos
TIMEOUT = 5
MAX_RETRIES = 3           

class UDPServer(threading.Thread): #classe udp e cada isntancia roda sua propria thread
    def __init__(self, state: NodeState): 
        super().__init__()
        self.state = state 
        self.host = '0.0.0.0'#escuta em todas as interfaces de rede
        self.port = state.port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #cria o socket udp
        self.server_socket.bind((self.host, self.port)) #associa o socket ao endereço e porta
        self.running = True
        print(f"[Servidor UDP] Escutando em {self.host}:{self.port}")

    def run(self): #aq que inicia a thread
        while self.running: #loop infinito, só sai quando o servidor for parado
            try:
                data, address = self.server_socket.recvfrom(MAX_DATAGRAM_SIZE) #recebe dados do socket
                if not data.startswith(b'ACK|'): 
                    threading.Thread(target=self.handle_request, args=(data, address)).start()#cria uma nova thread para cada requisição recebida
            except Exception as e:
                if self.running: print(f"[Erro Servidor UDP] {e}")

    def handle_request(self, data, address): #roda as requisições do cliente em threads separadas
        try:
            message = data.decode('utf-8', errors='ignore') 
            parts = message.split('|', 1)
            command, payload = parts[0], parts[1] if len(parts) > 1 else "" #divide a mensagem em comando e dados json

            if command == "INDEX_REQ": #se o comando for INDEX_REQ, envia o index de arquivos
                self._send_index(address)
            elif command == "FILE_REQ": #se o comando for FILE_REQ, inicia a transferência do arquivo
                self._start_file_transfer(address, payload)
        except Exception as e:
            print(f"Erro ao processar requisição de {address}: {e}")

    def _send_response(self, address, response_type: str, data): #envia a resposta pro cliente
        message = f"{response_type}|{json.dumps(data)}".encode('utf-8') 
        self.server_socket.sendto(message, address) #

    def _send_index(self, address): #envia o index de arquivos pro cliente
        payload = self.state.index_payload()
        self._send_response(address, "INDEX_RSP", payload) 
        
    def _start_file_transfer(self, client_address, filename): #inicia a transferência do arquivo pro cliente
        file_path = os.path.join(self.state.directory, filename) #caminho completo do arquivo
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as transfer_socket: #cria um novo socket udp para a transferência do arquivo
            transfer_socket.settimeout(TIMEOUT)
            if not os.path.exists(file_path): #se o arquivo não existir, envia uma mensagem de erro pro cliente
                transfer_socket.sendto(b"FILE_ERR|NotFound", client_address)
                return

            with open(file_path, "rb") as f: file_data = f.read()
            
            chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)] if file_data else [b''] #divide o arquivo em pedaços
            total_chunks = len(chunks)

            for seq, chunk_data in enumerate(chunks): #envia cada pedaço do arquivo pro cliente
                header = f"FILE_CHUNK|{seq}|{total_chunks}|".encode('utf-8')
                message = header + chunk_data
                ack_received = False
                for attempt in range(MAX_RETRIES): #tenta enviar o pedaço n(max_retires) vezes se necessário
                    try:
                        transfer_socket.sendto(message, client_address)
                        ack_data, addr = transfer_socket.recvfrom(1024)
                        if addr == client_address and ack_data.decode('utf-8') == f"ACK|{seq}": # ve se a resposta eh do cliente correto
                            ack_received = True
                            break
                    except socket.timeout: 
                        continue
                if not ack_received:
                    raise TimeoutError(f"Falha ao receber ACK para o chunk {seq}")
            print(f"[{self.state.node_id}] Transferência de '{filename}' concluída para {client_address}")

    def stop(self):
        print("Parando o servidor UDP...")
        self.running = False
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(b'', (self.host, self.port))
        self.server_socket.close()
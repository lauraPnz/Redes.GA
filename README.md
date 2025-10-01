# Redes.GA 🌐

Este projeto implementa um sistema básico de sincronização de arquivos distribuídos (Peer-to-Peer - P2P) utilizando o **protocolo UDP** em Python. O objetivo é manter um diretório local sincronizado de forma consistente entre todos os nós da rede, simulando um ambiente distribuído.

## 

O projeto foi desenvolvido para cumprir os seguintes requisitos principais da avaliação:

| Requisito | Detalhe da Implementação |
| :--- | :--- |
| **Protocolo** | Uso obrigatório do protocolo **UDP** (User Datagram Protocol). |
| **Confiabilidade** | Implementação de um Protocolo de Transferência Confiável, customizado sobre UDP para garantir a entrega de metadados e fragmentos de arquivos. |
| **Estrutura** | Rede P2P estática com 4 nodos, onde cada um atua como Cliente e Servidor. |
| **Sincronização** | Suporte dinâmico para adição/remoção de arquivos, usando **Tombstones** para propagar exclusões. |
| **Hashing** | Utiliza **SHA-256** para verificação de integridade e resolução de conflitos (`need_download`). |

---

### 1. Pré-requisitos
* Python 3.x
## Para execução local 
* Abra 4 Terminais: Você usará 3 para os nós e 1 como "Terminal de Controle".
* Navegue até a Pasta Raiz: Em todos os quatro terminais, execute o comando cd para entrar na pasta do seu projeto.
* Limpe Dados Antigos: No Terminal de Controle, execute o comando abaixo para apagar a pasta sync_data de testes anteriores.
* Crie as Pastas de Sincronização: No Terminal de Controle, crie a estrutura de diretórios limpa.
   * mkdir sync_data/nodo1, sync_data/nodo2, sync_data/nodo3
*-Execute um comando em cada um dos três terminais reservados para os nós.
  * No Terminal 1:
      * python3 main.py --config config/node1.json
  * No Terminal 2:
      * python3 main.py --config config/node2.json
  * No Terminal 3:
      * python3 main.py --config config/node3.json
* Use o Terminal de controle para realizar os testes:
   * Cirar Arquivo:
        *echo "teste local" > sync_data/node1/local.txt
    *Deletar Arquivo:
        * del sync_data/node3/local.txt

## Para execução com Docker
* Inicie o Docker Desktop: Garanta que o aplicativo esteja aberto e o motor em execução.
* Abra 1 Terminal: Você só precisa de um terminal principal para o Docker Compose.
* Navegue até a Pasta Raiz: Execute o cd para entrar na pasta do projeto.
* Construa e Inicie os Containers: No terminal principal, execute:
    * docker compose up --build
* No segundo terminal, crie:
       * echo "teste com docker" > sync_data/nodo1/docker.txt
* Deletar: Repita os mesmos testes de modificação e exclusão da execução local. O comportamento será o mesmo.
## Funcionalidades Principais

-   **Rede P2P Estática:** A topologia da rede é definida por arquivos de configuração, onde cada nó conhece os outros peers.
-   **Sincronização Automática:** Os nós verificam periodicamente o estado dos outros peers e iniciam a sincronização quando detectam diferenças.
-   **Detecção de Mudanças por Metadados:** As alterações são detectadas comparando metadados dos arquivos, incluindo **data de modificação** e **hash SHA256**, garantindo precisão e eficiência.
-   **Protocolo de Transferência Confiável sobre UDP:**
    -   **Segmentação:** Arquivos são divididos em pequenos pacotes (`chunks`) para transmissão.
    -   **Confirmação e Retransmissão:** Cada `chunk` enviado exige uma confirmação (`ACK`) do receptor. Se o `ACK` não chegar dentro de um tempo limite (timeout), o `chunk` é reenviado.
-   **Suporte a Múltiplos Ambientes:** O sistema pode ser executado e testado tanto em ambiente **local** (localhost) quanto em um ambiente de **containers com Docker**, simulando uma rede real.

## main.py 
* Função: Inicia e gerencia o ciclo de vida do nó (peer).
* Lê o arquivo de configuração JSON, inicializa o NodeState, e, crucialmente, inicia o Servidor UDP e o Cliente (sync_loop) em threads separadas, permitindo que o nó escute e envie requisições ao mesmo tempo.

## servidor.py 
* Atua como o lado Servidor do peer, escutando a rede.
* Recebe datagramas UDP de outros peers, processa e envia a resposta. Contém a lógica de envio de arquivos, que divide e reenvia chunks de dados.

## cliente.py 
 * Atua como o lado Cliente do peer, iniciando a comunicação.
 * Contém o sync_loop que executa o ciclo de sincronização a cada 5 segundos. Ele usa a função udp_request para enviar comandos (requerindo metadados ou arquivos) e implementa a lógica de timeout e retransmissão para garantir a entrega das requisições via UDP.

## status_node.py 
* Gerencia o estado local, os metadados e as regras de sincronização.
* Contém a classe NodeState, que monitora o diretório local, armazena o índice de arquivos (.p2pmeta.json), gera os índices e tombstones e contém a lógica crítica para decidir se um arquivo precisa ser baixado (need_download).

## utilidades.py (A Caixa de Ferramentas)
* Fornece funções de baixo nível para manipulação segura de dados e arquivos.
* Contém funções essenciais como cálculo do hash SHA-256 (para verificar integridade dos arquivos), leitura/escrita segura de arquivos JSON (read_json, write_json), e garantia de segurança de diretório (safe_join).

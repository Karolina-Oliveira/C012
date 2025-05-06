import threading
import time
import random
import matplotlib.pyplot as plt

# Classe que representa um veículo (cruzamento) chegando ao semáforo
class Cruzamento(threading.Thread):
    def __init__(self, id, tempo_chegada, semaforo, log):
        super().__init__()
        self.id = id  # identificador do cruzamento
        self.tempo_chegada = tempo_chegada  # timestamp em que "chega" ao semáforo
        self.semaforo = semaforo  # semáforo compartilhado (lock) para exclusão mútua
        self.log = log  # lista para registrar tempos de espera
        self.prioridade = None  # prioridade atribuída para escalonamento
        self.show_prioridade = False  # flag para exibir a prioridade no print
        self.tempo_entrada = None  # timestamp do início de passagem pelo semáforo

    # Método executado quando a thread é iniciada
    def run(self):
        now = time.time()
        # calcula quanto tempo deve esperar até que o veículo "chegue"
        delay = max(0, self.tempo_chegada - now)
        time.sleep(delay)

        # tenta entrar na seção crítica (o semáforo) garantindo exclusão mútua
        with self.semaforo:
            self.tempo_entrada = time.time()
            espera = self.tempo_entrada - self.tempo_chegada
            # registra (id do cruzamento, tempo de espera) no log
            self.log.append((self.id, espera))
            # exibe mensagem de passagem
            if self.show_prioridade:
                print(f"Cruzamento {self.id} (Prioridade {self.prioridade}) está passando... esperou {espera:.3f}s")
            else:
                print(f"Cruzamento {self.id} está passando... esperou {espera:.3f}s")
            # simula tempo de travessia pelo semáforo
            time.sleep(random.uniform(1, 2))

# FCFS: ordena os cruzamentos pela ordem de chegada (timestamp)
def escalonador_fcfs(cruzamentos):
    return sorted(cruzamentos, key=lambda c: c.tempo_chegada)

# Prioridade: ordena primeiramente pela prioridade (1 = maior) e depois pela chegada
def escalonador_prioridade(cruzamentos):
    return sorted(cruzamentos, key=lambda c: (c.prioridade, c.tempo_chegada))

# Função que executa a simulação de um algoritmo dado
# Retorna o tempo médio de espera e a quantidade de passagens (conflitos evitados)
def simular(algoritmo):
    print(f"\n--- Simulando com algoritmo: {algoritmo.upper()} ---\n")
    num_cruzamentos = 5
    semaforo = threading.Semaphore(1)  # semáforo com capacidade 1 (lock)
    log = []  # lista para armazenar tempos de espera de cada thread
    cruzamentos = []  # lista de objetos Cruzamento

    # Cria instâncias de Cruzamento com tempos de chegada e prioridades aleatórias
    for i in range(num_cruzamentos):
        tempo_chegada = time.time() + random.uniform(0, 3)
        prioridade = random.randint(1, 10)
        cruz = Cruzamento(i, tempo_chegada, semaforo, log)
        cruz.prioridade = prioridade
        cruzamentos.append(cruz)

    # Aguarda até que todos os cruzamentos "cheguem" (tempo máximo de 3s)
    time.sleep(3.5)

    # Escolhe o algoritmo de escalonamento e dispara as threads
    if algoritmo.lower() == "fcfs":
        ordem = escalonador_fcfs(cruzamentos)
        # não mostra prioridades nesta simulação
        for c in ordem:
            c.show_prioridade = False
        # inicia todas as threads simultaneamente, sem controle de ordem além do semáforo
        for c in ordem:
            c.start()
        for c in ordem:
            c.join()

    else:
        # simulação por prioridade: define flag para mostrar prioridade
        ordem = escalonador_prioridade(cruzamentos)
        for c in ordem:
            c.show_prioridade = True

        # exibe a ordem definida pelo escalonador antes de executar
        print("Ordem de execução por prioridade:")
        for c in ordem:
            print(f"  Cruzamento {c.id}: Prioridade {c.prioridade}")
        print()

        # inicia as threads uma a uma, respeitando a ordem de prioridade
        for c in ordem:
            c.start()
            c.join()

    # Cálculo de métricas:
    tempos_espera = [e for (_, e) in log]
    media_espera = sum(tempos_espera) / len(tempos_espera)
    conflitos = len(log)  # cada passagem é considerada um conflito evitado

    print(f"\nTempo médio de espera: {media_espera:.2f}s")
    print(f"Conflitos evitados: {conflitos}")

    return media_espera, conflitos

# Ponto de entrada do script: executa simulações e gera gráfico comparativo
if __name__ == "__main__":
    resultados = {}
    # simula FCFS
    resultados["FCFS"], _ = simular("fcfs")
    # simula Prioridade
    resultados["Prioridade"], _ = simular("prioridade")

    # Geração de gráfico de barras comparando tempos médios de espera
    plt.figure(figsize=(6, 4))
    plt.bar(resultados.keys(), resultados.values(), color=['skyblue','lightgreen'])  # cores para diferenciar
    plt.ylabel("Tempo médio de espera (s)")
    plt.title("Comparação de Algoritmos de Escalonamento")
    plt.ylim(0, max(resultados.values()) + 1)  # ajusta eixo y
    # escreve o valor exato acima de cada barra
    for i, v in enumerate(resultados.values()):
        plt.text(i, v + 0.1, f"{v:.2f}s", ha='center', fontweight='bold')
    plt.tight_layout()
    plt.show()

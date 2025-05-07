import threading
import time
import random
import matplotlib.pyplot as plt

# Classe que representa cada veículo passando por um semáforo
class Carro(threading.Thread):
    def __init__(self, semaforo_id, carro_idx, tempo_chegada, semaforo, log, prioridade, prob):
        super().__init__()
        # Identificação do semáforo ao qual este carro pertence
        self.semaforo_id = semaforo_id
        # Índice único do carro dentro do semáforo
        self.carro_idx = carro_idx
        # Timestamp em que o carro "chega" ao semáforo
        self.tempo_chegada = tempo_chegada
        # Lock compartilhado para garantir exclusão mútua
        self.semaforo = semaforo
        # Lista compartilhada para registrar tempos de espera
        self.log = log
        # Prioridade do semáforo (menor valor = mais alta prioridade)
        self.prioridade = prioridade
        # Probabilidade associada ao semáforo (usada apenas no print)
        self.prob = prob
        # Flags para controlar o formato do print durante a simulação
        self.show_prioridade = False
        self.position = None
        # Timestamp de início de passagem pelo semáforo
        self.tempo_entrada = None

    def run(self):
        """
        Executado quando a thread é iniciada:
        1) Aguarda até o momento de chegada.
        2) Adquire o lock do semáforo para simular a travessia.
        3) Calcula e registra o tempo de espera.
        4) Imprime detalhes conforme o algoritmo (FCFS ou Prioridade).
        5) Simula tempo de travessia.
        """
        # 1) Aguarda até o instante de chegada
        time.sleep(max(0, self.tempo_chegada - time.time()))

        # 2) Seção crítica: somente um carro por vez
        with self.semaforo:
            # Marca o instante de início da travessia
            self.tempo_entrada = time.time()
            # 3) Cálculo do tempo de espera
            espera = self.tempo_entrada - self.tempo_chegada
            # Registra no log compartilhado
            self.log.append((self, espera))

            # 4) Impressão do resultado para o usuário
            if self.show_prioridade:
                # Mostra probabilidade e prioridade no algoritmo de prioridades
                print(
                    f"Carro {self.carro_idx} do semáforo {self.semaforo_id} "
                    f"(Prob: {self.prob*100:.1f}%, Pri: {self.prioridade}) "
                    f"esperou {espera:.3f}s"
                )
            else:
                # Mostra posição e tempo de espera no algoritmo FCFS
                print(
                    f"Carro {self.carro_idx} do semáforo {self.semaforo_id} "
                    f"- posição {self.position}: esperou {espera:.3f}s"
                )

            # 5) Tempo de travessia aleatório (1 a 2 segundos)
            time.sleep(random.uniform(1, 2))


# ----------------------
# Funções de escalonamento
# ----------------------

def escalonador_fcfs(carros):
    """
    Retorna a lista de carros ordenada pelo tempo de chegada (First-Come, First-Served).
    """
    return sorted(carros, key=lambda c: c.tempo_chegada)


def escalonador_prioridade(carros):
    """
    Retorna a lista de carros ordenada pela prioridade do semáforo (menor valor primeiro).
    """
    return sorted(carros, key=lambda c: c.prioridade)


# -------------------------------------
# Função principal de simulação genérica
# -------------------------------------

def simular(algoritmo, semaforos, cars_data):
    """
    Executa a simulação de controle de tráfego para o algoritmo especificado:
    - FCFS: usa delays para chegar e executa todos os carros em paralelo.
    - Prioridade: ignora delays e processa um a um conforme prioridade.

    Parâmetros:
        algoritmo (str): 'fcfs' ou 'prioridade'
        semaforos (list): lista de dicts com keys 'id','prob','cars','priority'
        cars_data (list): lista de dicts com keys 'semaforo_id','carro_idx','delay'

    Retorna:
        float: tempo médio de espera de todos os carros.
    """
    print(f"\n--- Simulando {algoritmo.upper()} ---\n")
    # Marca início da simulação para calcular tempos relativos
    sim_start = time.time()

    log = []                   # para registrar cada espera
    lock = threading.Semaphore(1)  # semáforo geral
    threads = []               # lista de threads Carro

    # 1) Criação das threads de Carro
    for data in cars_data:
        # Busca configurações do semáforo do carro
        sem = next(s for s in semaforos if s['id'] == data['semaforo_id'])
        # FCFS: aplica delay simulado; Prioridade: chega imediatamente
        tempo_chegada = (sim_start + data['delay']
                         if algoritmo.lower() == 'fcfs'
                         else time.time())
        carro = Carro(
            semaforo_id=sem['id'],
            carro_idx=data['carro_idx'],
            tempo_chegada=tempo_chegada,
            semaforo=lock,
            log=log,
            prioridade=sem['priority'],
            prob=sem['prob']
        )
        threads.append(carro)

    # 2) Determinação da ordem de saída e configuração de flags de impressão
    if algoritmo.lower() == 'fcfs':
        ordem = escalonador_fcfs(threads)
        print("Ordem de chegada dos carros:")
        for pos, carro in enumerate(ordem, start=1):
            carro.position = pos        # posição na fila FCFS
            carro.show_prioridade = False
            print(f"  Posição {pos}: Carro {carro.carro_idx} do semáforo {carro.semaforo_id}")
        # 3a) Execução em paralelo
        for carro in threads:
            carro.start()
        for carro in threads:
            carro.join()

    else:
        ordem = escalonador_prioridade(threads)
        print("Ordem de execução por prioridade:")
        for carro in ordem:
            carro.show_prioridade = True
            print(
                f"  Carro {carro.carro_idx} do semáforo {carro.semaforo_id} "
                f"(Prob: {carro.prob*100:.1f}%, Pri: {carro.prioridade})"
            )
        # 3b) Execução sequencial conforme prioridade
        for carro in ordem:
            carro.start()
            carro.join()

    # 4) Cálculo e exibição do tempo médio de espera
    esperas = [esp for (_, esp) in log]
    media = sum(esperas) / len(esperas) if esperas else 0
    print(f"\nTempo médio de espera ({algoritmo.upper()}): {media:.2f}s")
    return media


# ----------------------
# Bloco principal (ENTRYPOINT)
# ----------------------
if __name__ == '__main__':
    random.seed()
    num_semaforos = 4
    semaforos = []

    # 1) Geração de probabilidades e número de carros por semáforo
    for s_id in range(num_semaforos):
        prob = random.random()            # probabilidade simulada (0.0 a 1.0)
        cnt = random.randint(0, 10)       # número de carros (0 a 10)
        semaforos.append({'id': s_id, 'prob': prob, 'cars': cnt})

    # 2) Definição de prioridade baseada na probabilidade (maior prob = Pri 1)
    semaforos.sort(key=lambda s: s['prob'], reverse=True)
    for rank, sem in enumerate(semaforos, start=1):
        sem['priority'] = rank

    # 3) Impressão das configurações iniciais para o usuário
    print("Configurações iniciais dos semáforos:")
    for sem in semaforos:
        print(
            f"  Semáforo {sem['id']}: Prob={sem['prob']*100:.1f}%, "
            f"Carros={sem['cars']}, Pri={sem['priority']}"
        )

    # 4) Geração de delays aleatórios para FCFS (usado por ambos para mesma base)
    cars_data = []
    for sem in semaforos:
        for i in range(sem['cars']):
            cars_data.append({
                'semaforo_id': sem['id'],
                'carro_idx': i,
                'delay': random.uniform(0, 3)
            })

    # 5) Simulação sequencial de FCFS e Prioridade, reaproveitando dados
    m_fcfs = simular('fcfs', semaforos, cars_data)
    m_prio = simular('prioridade', semaforos, cars_data)

    # 6) Plotagem comparativa dos resultados
    plt.figure(figsize=(6, 4))
    plt.bar(['FCFS', 'Prioridade'], [m_fcfs, m_prio])
    plt.ylabel('Tempo médio de espera (s)')
    plt.title('Comparação de Algoritmos')
    for idx, val in enumerate([m_fcfs, m_prio]):
        plt.text(idx, val + 0.1, f"{val:.2f}s", ha='center', fontweight='bold')
    plt.tight_layout()
    plt.show()

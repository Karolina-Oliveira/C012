import threading
import time
import random

# === Configurações da simulação ===
NUM_SEMAFOROS        = 4       # número total de semáforos interligados
TEMPO_SIMULACAO      = 30.0    # duração total da simulação (segundos)
TEMPO_VERDE          = 3.0     # tempo que cada semáforo permanece VERDE (segundos)
INTERVALO_TICK       = 0.3     # intervalo entre tentativas de liberar carro (segundos)
PROBABILIDADE_LIB    = 0.2     # probabilidade de liberar um carro em cada tick (0.0 a 1.0)
JANELA_COLISAO       = 0.3     # janela extra para considerar colisão (segundos)

# Variáveis de controle da simulação
semaforo_verde_atual = 1                  # ID do semáforo que está com sinal VERDE
evento_simulacao     = threading.Event()  # Evento para sinalizar término ou acidente

# Estruturas para coleta de estatísticas
dicionario_valores = range(1, NUM_SEMAFOROS+1)
carros_liberados     = {i: 0 for i in dicionario_valores}  # total de carros liberados por semáforo
tempos_liberacao     = {i: [] for i in dicionario_valores}  # timestamps de cada liberação
contagens_liberacao  = {i: 0 for i in dicionario_valores}  # contador sequencial de IDs de carros
semaforos_acidente   = set()                                  # semáforos envolvidos em colisão

# Lista de tuplas representando carros em travessia:
# (id_carro, tempo_fim_travessia, momento_liberacao, id_semaforo)
carros_atuais        = []


def trabalhador_semaforo(id_semaforo):
    """
    Função executada por cada thread de semáforo.
    Espera sua vez de ficar VERDE, libera carros aleatoriamente,
    detecta possíveis colisões e sinaliza fim da simulação.
    """
    global semaforo_verde_atual

    # Loop principal: continua enquanto a simulação não terminar
    while not evento_simulacao.is_set():
        # Aguarda o semáforo ficar VERDE para este ID
        while semaforo_verde_atual != id_semaforo and not evento_simulacao.is_set():
            time.sleep(0.01)  # breve pausa para evitar busy-wait intenso
        # Se a simulação foi sinalizada para encerrar, sai da thread
        if evento_simulacao.is_set():
            return

        # Início do período VERDE deste semáforo
        print(f"\n[S{id_semaforo}] — VERDE ({TEMPO_VERDE:.0f}s)")
        inicio_verde = time.time()
        fim_verde    = inicio_verde + TEMPO_VERDE

        # Durante o tempo VERDE, a cada tick tenta liberar um carro
        while time.time() < fim_verde and not evento_simulacao.is_set():
            time.sleep(INTERVALO_TICK)
            agora = time.time()
            # Se acabou o tempo VERDE, interrompe o loop
            if agora >= fim_verde:
                break

            # Decide aleatoriamente se libera um carro neste instante
            if random.random() < PROBABILIDADE_LIB:
                tempo_no_verde = agora - inicio_verde

                # Atualiza contador e gera ID único pro carro
                contagens_liberacao[id_semaforo] += 1
                id_carro = f"carro{contagens_liberacao[id_semaforo]}_s{id_semaforo}"
                carros_liberados[id_semaforo] += 1
                tempos_liberacao[id_semaforo].append(agora)

                # Calcula tempo de travessia e agenda remoção desse carro
                tempo_travessia = NUM_SEMAFOROS - id_semaforo + 2  # ex: carros de semáforo 1 demoram mais
                fim_travessia   = agora + tempo_travessia
                carros_atuais.append((id_carro, fim_travessia, agora, id_semaforo))

                # Imprime estado atual da rua após liberação
                estados = [(c, f"{agora - tl:.2f}s") for c, _, tl, _ in carros_atuais]
                print(f"  • S{id_semaforo} liberou {id_carro} em {tempo_no_verde:.2f}s do verde. Rua:", estados)

                # Verifica colisão com o semáforo anterior
                sema_ante = id_semaforo - 1
                if sema_ante >= 1:
                    envolvidos = []
                    tempo_ate_anterior = 1 + abs(id_semaforo - sema_ante)
                    # Percorre carros atuais buscando aqueles do semáforo anterior
                    for c, _, tl, sid in carros_atuais:
                        if sid == sema_ante:
                            delta = agora - tl
                            # Se estiver dentro da janela de colisão
                            if tempo_ate_anterior <= delta <= tempo_ate_anterior + JANELA_COLISAO:
                                envolvidos.append(c)
                    # Se houve colisão, sinaliza e encerra simulação
                    if envolvidos:
                        envolvidos.append(id_carro)
                        semaforos_acidente.update({sema_ante, id_semaforo})
                        print("💥 ACIDENTE! Semáforos envolvidos:", sorted(semaforos_acidente))
                        print("  • Carros envolvidos:", envolvidos)
                        evento_simulacao.set()
                        return

        # Fim do periodo VERDE: imprime VERMELHO e passa a vez
        print(f"[S{id_semaforo}] — VERMELHO")
        semaforo_verde_atual = (id_semaforo % NUM_SEMAFOROS) + 1


# === Inicialização das threads de semáforos ===
threads = []
for s in range(1, NUM_SEMAFOROS+1):
    t = threading.Thread(target=trabalhador_semaforo, args=(s,), daemon=True)
    t.start()
    threads.append(t)

# === Loop principal controla duração da simulação ===
inicio_sim = time.time()
while time.time() - inicio_sim < TEMPO_SIMULACAO and not evento_simulacao.is_set():
    time.sleep(0.2)
# Sinaliza término da simulação (tempo esgotado ou acidente)
evento_simulacao.set()

# Aguarda todas as threads de semáforo terminarem
for t in threads:
    t.join()

# === Pós-simulação: esvaziamento final e relatório ===
print("\nEsvaziando rua restante…")
agora = time.time()
for c, fim, _, _ in carros_atuais:
    if fim > agora:
        print(f"  • Carro {c} removido (tarde).")

print("\n=== SIMULAÇÃO ENCERRADA ===")
# Exibe quantos carros cada semáforo liberou
for sid, cnt in carros_liberados.items():
    print(f"  S{sid}: {cnt}")
# Indica se houve acidente e quais semáforos foram afetados
if semaforos_acidente:
    print("Semáforos no acidente:", sorted(semaforos_acidente))
else:
    print("Nenhum acidente ocorreu.")

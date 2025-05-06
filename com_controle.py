import threading
import time
import random

# === Configurações gerais da simulação ===
NUM_SEMAFOROS        = 4      # Quantidade de semáforos interligados
TEMPO_SIMULACAO      = 30.0   # Duração total da simulação em segundos
TEMPO_VERDE          = 3.0    # Tempo (s) que cada semáforo fica VERDE
INTERVALO_TICK       = 0.3    # Intervalo (s) entre tentativas de liberação de carro
PROBABILIDADE_LIB    = 0.2    # Probabilidade de liberar um carro a cada tick (0.0 a 1.0)
JANELA_COLISAO       = 0.3    # Janela (s) para detectar colisão entre semáforos adjacentes

# === Objetos de sincronização ===
trava_impressao      = threading.Lock()      # Garante prints sem sobreposição
evento_simulacao     = threading.Event()     # Sinaliza fim imediato da simulação
condicao_verde       = threading.Condition() # Coordena qual semáforo está com VERDE
semaforo_verde_atual = 1                     # ID do semáforo que iniciou em VERDE

# === Estatísticas de liberação ===
carros_liberados    = {i: 0 for i in range(1, NUM_SEMAFOROS + 1)}   # total liberado por semáforo
tempos_liberacao    = {i: [] for i in range(1, NUM_SEMAFOROS + 1)} # timestamps de liberação
contagens_liberacao = {i: 0 for i in range(1, NUM_SEMAFOROS + 1)} # contador sequencial de carros
semaforos_acidente  = set()                                    # IDs de semáforos envolvidos em colisão

# Lista compartilhada de carros em travessia: tuplas (id_carro, fim_trav, inicio_lib, id_semaforo)
carros_atuais = []
trava_carros   = threading.Lock()  # Protege acesso à lista carros_atuais


def evento_travessia(id_carro):
    """
    Invocada quando um carro termina de atravessar. Remove da lista de ativos.
    """
    with trava_impressao:
        print(f"  ▶ O {id_carro} atravessou a rua completamente.")
    # Remove todas as entradas correspondentes a este carro
    carros_atuais[:] = [
        (c, tf, tl, sid)
        for c, tf, tl, sid in carros_atuais
        if c != id_carro
    ]


def trabalhador_semaforo(id_semaforo):
    """
    Thread que gerencia o ciclo de VERDE/VERMELHO de um semáforo.
    Executa até o evento de simulação ser disparado ou até colisão.
    """
    global semaforo_verde_atual

    while not evento_simulacao.is_set():
        # Aguarda ser notificado de que é sua vez de ficar VERDE
        with condicao_verde:
            while semaforo_verde_atual != id_semaforo and not evento_simulacao.is_set():
                condicao_verde.wait()
            if evento_simulacao.is_set():
                return  # sai se simulação finalizada

        # Início do ciclo VERDE deste semáforo
        with trava_impressao:
            print(f"\n[S{id_semaforo}] — VERDE ({TEMPO_VERDE:.0f}s)")

        inicio_verde = time.time()
        fim_verde    = inicio_verde + TEMPO_VERDE

        # Durante o período VERDE, a cada tick tenta liberar um carro
        while time.time() < fim_verde and not evento_simulacao.is_set():
            time.sleep(INTERVALO_TICK)
            agora = time.time()
            if agora > fim_verde:
                break

            # Sorteia se um carro é liberado neste tick
            if random.random() < PROBABILIDADE_LIB:
                # Cria um novo carro com ID sequencial baseado no semáforo
                contagens_liberacao[id_semaforo] += 1
                id_carro = f"carro{contagens_liberacao[id_semaforo]}_s{id_semaforo}"
                tempos_liberacao[id_semaforo].append(agora)
                carros_liberados[id_semaforo] += 1

                # Tempo estimado para completar travessia: função da posição do semáforo
                tempo_viagem = NUM_SEMAFOROS - id_semaforo + 2
                fim_travessia = agora + tempo_viagem

                # Adiciona carro à lista de atravessamento ativo
                with trava_carros:
                    carros_atuais.append((id_carro, fim_travessia, agora, id_semaforo))

                # Agenda evento que remove o carro ao fim da travessia
                timer = threading.Timer(tempo_viagem, evento_travessia, args=(id_carro,))
                timer.daemon = True
                timer.start()

                # Imprime estado atual da rua após liberação
                with trava_impressao:
                    estados = [
                        f"({c}, {(agora - tl):.2f}s)"
                        for c, _, tl, _ in carros_atuais
                    ]
                    print(f"  • S{id_semaforo} liberou {id_carro} em {(agora - inicio_verde):.2f}s do verde. Rua:",
                          " ".join(estados))

                # Verifica colisão com semáforo anterior adjacente
                sema_ante = id_semaforo - 1
                if sema_ante >= 1:
                    envolvidos = []
                    # tempo de trânsito até semáforo anterior (exemplo fixo)
                    tempo_ate_ante = 1 + abs(id_semaforo - sema_ante)
                    with trava_carros:
                        for c_prev, _, tl_prev, sid_prev in carros_atuais:
                            if sid_prev == sema_ante:
                                delta = agora - tl_prev
                                # colisão se cruzamentos próximos chocam dentro da janela
                                if tempo_ate_ante <= delta <= tempo_ate_ante + JANELA_COLISAO:
                                    envolvidos.append(c_prev)
                    if envolvidos:
                        envolvidos.append(id_carro)
                        semaforos_acidente.update({sema_ante, id_semaforo})
                        with trava_impressao:
                            print(f"💥 ACIDENTE! Semáforos envolvidos: {sorted(semaforos_acidente)}")
                            print(f"  • Carros envolvidos: {envolvidos}")
                        # encerra simulação em caso de acidente
                        evento_simulacao.set()
                        return

        # Fim do período VERDE: semáforo volta ao estado VERMELHO
        with trava_impressao:
            print(f"[S{id_semaforo}] — VERMELHO")

        # Passa o VERDE para o próximo semáforo e notifica todas threads
        with condicao_verde:
            semaforo_verde_atual = (id_semaforo % NUM_SEMAFOROS) + 1
            condicao_verde.notify_all()


# === Inicialização das threads de semáforos ===
threads = []
for s in range(1, NUM_SEMAFOROS + 1):
    t = threading.Thread(target=trabalhador_semaforo, args=(s,), daemon=True)
    t.start()
    threads.append(t)

# === Loop principal controla duração da simulação ===
inicio = time.time()
while time.time() - inicio < TEMPO_SIMULACAO and not evento_simulacao.is_set():
    time.sleep(0.2)
# Sinaliza término caso o tempo acabe ou ocorra acidente
evento_simulacao.set()

# Destrava possíveis threads em espera e aguarda todas encerrarem
with condicao_verde:
    condicao_verde.notify_all()
for t in threads:
    t.join()

# === Finalização: limpa rua e exibe estatísticas ===
with trava_impressao:
    print("\nEsvaziando rua restante…")
    agora = time.time()
    # Remove manualmente qualquer carro que não completou a tempo
    for c, fim, _, _ in carros_atuais:
        if fim > agora:
            print(f"  • Carro {c} removido (tarde).")
    print("\n=== SIMULAÇÃO ENCERRADA ===")
    # Exibe contagem de carros liberados por semáforo
    for sid, cnt in carros_liberados.items():
        print(f"  S{sid}: {cnt}")
    # Informa se houve acidente e quais semáforos foram afetados
    if semaforos_acidente:
        print("Semáforos no acidente:", sorted(semaforos_acidente))
    else:
        print("Nenhum acidente ocorreu.")
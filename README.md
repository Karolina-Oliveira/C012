# Projeto C012 - Simulação de Semáforos com Concorrência

Este repositório contém o projeto desenvolvido por **Karolina Oliveira da Silva** e **Sabrina Ramos Silveira** para a disciplina de **Sistemas Operacionais (C012)**. O projeto simula diferentes abordagens de controle de tráfego em um cruzamento com múltiplos semáforos utilizando conceitos de **concorrência, sincronização** e **escalonamento de threads**.

---

## 🎯 Objetivo Geral

Simular o funcionamento de uma rua com quatro semáforos em sequência, onde veículos são liberados aleatoriamente durante o sinal verde e percorrem a via em tempos definidos. A simulação detecta **colisões** quando dois veículos ocupam o mesmo ponto da rua simultaneamente.

São comparadas três abordagens:
- **Sem controle (sem sincronização):** expõe condições de corrida.
- **Com controle (com sincronização):** utiliza `Lock`, `Condition` e outras primitivas para evitar colisões.
- **Com escalonamento:** simula a ordem de passagem baseada em algoritmos FCFS e Prioridade.

---

## 📂 Estrutura do Repositório

### `sem_controle.py`

**Objetivo:** Demonstrar os riscos de concorrência sem sincronização.

**Descrição:**  
Cada semáforo opera independentemente, liberando veículos durante seu tempo verde com base em sorteio. Sem qualquer mecanismo de controle, múltiplos semáforos podem liberar carros ao mesmo tempo, resultando em **condições de corrida** e **colisões**.

**Trecho relevante:**
```python
while semaforo_verde_atual != id_semaforo and not evento_simulacao.is_set():
    time.sleep(0.01)
```

---

### `com_controle.py`

**Objetivo:** Garantir segurança no tráfego através de sincronização entre semáforos.

**Descrição:**  
Implementa **locks**, **timers** e **condições** para que apenas um semáforo libere veículos por vez. Isso assegura que veículos não ocupem a mesma posição na via simultaneamente, **evitando colisões**.

**Trecho relevante:**
```python
trava_impressao      = threading.Lock()      # Garante prints sem sobreposição
evento_simulacao     = threading.Event()     # Sinaliza fim imediato da simulação
condicao_verde       = threading.Condition() # Coordena qual semáforo está com VERDE

with condicao_verde:
    while semaforo_verde_atual != id_semaforo and not evento_simulacao.is_set():
        condicao_verde.wait()
```

---

### `escalonamento.py`

**Objetivo:** Avaliar estratégias de escalonamento de veículos para melhorar o desempenho do sistema.

**Descrição:**  
Simula dois algoritmos:
- **FCFS (First-Come, First-Served):** veículos são tratados na ordem de chegada.
- **Prioridade:** a ordem de passagem é baseada em uma **probabilidade de travessia**, que representa o fluxo natural do semáforo. Quanto maior a probabilidade, maior a prioridade.

**Destaque:**
```python
# 1) Para cada semáforo, geramos uma probabilidade (0.0 a 1.0)
for s_id in range(num_semaforos):
    prob = random.random()           # tendência de tráfego naquele semáforo
    cnt = random.randint(0, 10)      # número de carros a simular
    semaforos.append({'id': s_id, 'prob': prob, 'cars': cnt})

# 2) Ordenamos os semáforos pela probabilidade decrescente
#    — quem tem maior probabilidade de tráfego fica em primeiro lugar
semaforos.sort(key=lambda s: s['prob'], reverse=True)

# 3) Atribuímos um valor de 'priority' (1, 2, 3, …) em função dessa ordenação
for rank, sem in enumerate(semaforos, start=1):
    sem['priority'] = rank
```

Na simulação por prioridade, a execução é **sequencial** com base nesse ranking.

---

## 📊 Comparações e Resultados

O projeto mostra como:

- A ausência de controle resulta em colisões e inconsistência.
- O uso correto de **sincronismo** assegura a segurança e previsibilidade do sistema.
- Algoritmos de escalonamento, quando bem escolhidos, podem reduzir significativamente o **tempo médio de espera** dos veículos.

---

## 👩‍💻 Autoras

- **Karolina Oliveira da Silva**
- **Sabrina Ramos Silveira**

---

## 🎥 Apresentação do Projeto

Acesse a apresentação completa com detalhes visuais e explicações em:

[🔗 Apresentação no Canva](https://www.canva.com/design/DAGmomCPZ-0/GDSC4DzHYf0DpTQD9Xh1lQ/view?utm_content=DAGmomCPZ-0&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hac17ebf38d)

---

## 🧠 Conclusão

Este projeto destaca a importância de técnicas de concorrência e sincronização para garantir o comportamento correto e seguro em sistemas que compartilham recursos. Ele também mostra como estratégias de escalonamento impactam diretamente na eficiência de execução em ambientes multi-threaded.

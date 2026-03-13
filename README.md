# Desafio 01 — Banco Concorrente: Saldo sob Pressão

## Contexto

O **BancoFast** é uma fintech que processa transferências entre contas de forma assíncrona. Cada operação de transferência é executada por uma thread independente — afinal, o sistema precisa atender centenas de clientes simultaneamente.

O time de engenharia, no entanto, identificou um problema sério em produção: após picos de transferências simultâneas, o saldo total do sistema não bate. Dinheiro "some" misteriosamente. O CEO está em pânico.

Você foi contratado para investigar, reproduzir o bug e corrigi-lo.

---

## Objetivo

Implementar um sistema bancário simplificado em Python que:

1. **Reproduza** a condição de corrida existente na versão sem sincronização
2. **Corrija** o problema usando `threading.Lock`
3. **Valide** que o saldo total do sistema é preservado após todas as transferências

---

## Requisitos

- Cada conta bancária deve ter um saldo inicial configurável
- O sistema deve suportar múltiplas transferências simultâneas entre contas quaisquer
- Uma transferência só deve ocorrer se o saldo da conta de origem for suficiente (sem saldo negativo)
- O saldo total do sistema (soma de todas as contas) deve ser invariante — o dinheiro não é criado nem destruído, apenas transferido
- O programa deve imprimir o saldo total antes e depois das transferências, comprovando a invariância (ou sua violação)
- Usar **Python 3.8+** com o módulo `threading` da biblioteca padrão
- Não utilizar frameworks externos (sem `asyncio`, sem `concurrent.futures` — apenas `threading`)
- O código deve ter **comentários em PT-BR** explicando os pontos críticos de sincronização
- Entregar **duas versões** da função de transferência: uma sem lock (bugada) e uma com lock (correta)
- O número de threads e transferências deve ser parametrizável por constantes no topo do arquivo

---

## Estrutura Disponível

Neste diretório você encontrará:
- `sistema_bancario.py`: O esqueleto do código contendo o bug (Race Condition) estruturado, no qual você deverá implementar o `Lock`.
- `test_sistema_bancario.py`: Um script de testes automatizados para validar sua solução e provar que o dinheiro não se pede mais.

---

## Critérios de Avaliação

| Critério | Descrição | Peso |
|---|---|---|
| **Funcionalidade sem lock** | A race condition é claramente reproduzida (saldo total diverge) | 25% |
| **Funcionalidade com lock** | O saldo total é sempre preservado após todas as transferências | 35% |
| **Qualidade do código** | Estrutura clara, comentários em PT-BR, sem código duplicado desnecessário | 20% |

**Pontuação total:** 10 pontos

---

## Passo a Passo: Instruções de Resolução

1. **Análise Inicial**: Execute o código original (`python sistema_bancario.py`) repetidas vezes e observe que o saldo total final costuma variar confirmando a condição de corrida.
2. **Execute os Testes (Falha)**: Rode os testes unitários (`python -m unittest test_sistema_bancario.py -v`). Eles provarão a vulnerabilidade do sistema falhando propositalmente ao tentar perder/gerar dinheiro ou negativar saldo.
3. **Mecanismo de Sincronização**: Você precisará usar a ferramenta de exclusão mútua do Python: o `threading.Lock()`.
4. **Sincronize a Transferência**: Dentro do método `transferir`, identifique a "Seção Crítica" (momentos de leitura-modificação-escrita do saldo). Garanta que ambas as contas sejam protegidas contra acessos concorrentes simultâneos no exato momento da operação.
5. **Proteja as Transações**: Envolva o trecho crítico adquirindo o lock (`.acquire()`) e o liberando logo em seguida (`.release()`), ou de forma mais idiomática e segura no Python: utilize o contexto `with lock:`.
6. **Validação Final**: Após aplicar a trava com a granularidade apropriada, rode o código novamente. Os testes agora devem **PASSAR** e a execução de `sistema_bancario.py` sempre terminará com Desvio igual a R$ 0.00!

---

## Dica

> A operação de transferência envolve **dois passos** — debitar uma conta e creditar outra. Se o lock proteger apenas um dos passos isoladamente, ou se dois locks distintos forem adquiridos em ordens diferentes por threads diferentes, a integridade geral do sistema não será preservada — correndo perigo inclusive de engilhar num **deadlock**. Pense com muito cuidado em como abraçar essa "transação" antes de implementar.

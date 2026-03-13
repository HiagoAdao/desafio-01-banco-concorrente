import threading
import time
import random
import logging
from dataclasses import dataclass

# Configuração do Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("BancoFast")

# ---------------------------------------------------------------------------
# Constantes de configuração — ajuste para amplificar ou reduzir o efeito
# ---------------------------------------------------------------------------
NUM_CONTAS = 3
SALDO_INICIAL = 1000.0
TRANSFERENCIAS_POR_THREAD = 50_000
NUM_THREADS = 10
VALOR_TRANSFERENCIA = 10.0


@dataclass
class ContaBancaria:
    """Representa uma conta bancária simples, sem qualquer sincronização."""
    id: str
    saldo: float

    def transferir(self, destino: "ContaBancaria", valor: float) -> bool:
        """
        Realiza a transferência de `valor` da conta atual para `destino`.

        ⚠️  VERSÃO COM BUG INTENCIONAL — sem sincronização entre threads.

        O problema reside na separação temporal entre a leitura e a escrita do saldo.
        Como as threads executam essas operações de forma concorrente, 
        podem ocorrer leituras sujas e sobreposições de escritas.

        O `time.sleep(0)` atua apenas para forçar uma troca de contexto, tornando
        a condição de corrida (Race Condition) mais evidente em ambiente de simulação.

        Retorna True se a transferência foi tentada, False se saldo insuficiente.
        """
        if self.saldo < valor:
            return False

        # 👉 O BUG ESTÁ AQUI: Leitura e escrita do saldo não são atômicas
        saldo_lido_origem = self.saldo
        time.sleep(0)
        self.saldo = saldo_lido_origem - valor

        saldo_lido_destino = destino.saldo
        time.sleep(0)
        destino.saldo = saldo_lido_destino + valor

        return True


class TransferWorker:
    """Isola a lógica de execução das transferências disparadas por uma thread."""
    def __init__(self, contas: list[ContaBancaria], num_transferencias: int):
        self.contas = contas
        self.num_transferencias = num_transferencias

    def executar(self) -> None:
        """Função executada por cada thread: realiza múltiplas transferências aleatórias."""
        for _ in range(self.num_transferencias):
            origem, destino = random.sample(self.contas, 2)
            origem.transferir(destino, VALOR_TRANSFERENCIA)

def executar_simulacao() -> None:
    """Cria as contas, dispara as threads e exibe o resultado."""
    contas = [ContaBancaria(f"Conta-{i}", SALDO_INICIAL) for i in range(NUM_CONTAS)]
    saldo_total_antes = sum(c.saldo for c in contas)



    logger.info("=" * 55)
    logger.info("SIMULAÇÃO SEM LOCK — cenário com Race Condition")
    logger.info("=" * 55)
    logger.info(f"Contas criadas: {NUM_CONTAS}")
    logger.info(f"Saldo inicial por conta: R$ {SALDO_INICIAL:,.2f}")
    logger.info(f"Saldo total inicial: R$ {saldo_total_antes:,.2f}")
    logger.info(f"Threads: {NUM_THREADS}")
    logger.info(f"Transferências/thread: {TRANSFERENCIAS_POR_THREAD:,}")
    logger.info("-" * 55)
    logger.info("Executando transferências simultâneas... aguarde.")

    threads = []
    for _ in range(NUM_THREADS):
        worker = TransferWorker(contas, TRANSFERENCIAS_POR_THREAD)
        t = threading.Thread(target=worker.executar)
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    saldo_total_depois = sum(c.saldo for c in contas)
    desvio = saldo_total_depois - saldo_total_antes

    logger.info("-" * 55)
    logger.info(f"Saldo total final: R$ {saldo_total_depois:,.2f}")
    logger.info(f"Desvio (esperado = 0): R$ {desvio:,.2f}")
    logger.info("-" * 55)

    if abs(desvio) > 0.01:
        logger.error("❌ RACE CONDITION DETECTADA! O saldo total mudou.")
        logger.error("   Dinheiro foi criado ou destruído pela falta de sincronização.")
    else:
        # Isso pode ocorrer ocasionalmente — tente aumentar NUM_THREADS
        logger.warning("⚠️  O saldo bateu desta vez, mas o código ainda tem o bug.")
        logger.warning("   Aumente NUM_THREADS ou TRANSFERENCIAS_POR_THREAD para reproduzir.")

    logger.info("=" * 55)


if __name__ == "__main__":
    executar_simulacao()

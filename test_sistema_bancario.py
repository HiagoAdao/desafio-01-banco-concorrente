"""
Testes unitários para sistema_bancario.py.

OBJETIVO DIDÁTICO: Estes testes DEVEM FALHAR na implementação sem lock.
Eles validam as invariantes que qualquer sistema bancário correto deve garantir.

Execute com:
    python -m unittest test_sistema_bancario.py -v
"""

import threading
import time
import sys
import os
import unittest

# Garante que o módulo base seja importado
sys.path.insert(0, os.path.dirname(__file__))
import sistema_bancario as banco
from sistema_bancario import ContaBancaria, VALOR_TRANSFERENCIA


# ---------------------------------------------------------------------------
# Helpers de teste
# ---------------------------------------------------------------------------

def _worker(contas: list, n_transferencias: int) -> None:
    import random
    for _ in range(n_transferencias):
        origem, destino = random.sample(contas, 2)
        origem.transferir(destino, VALOR_TRANSFERENCIA)


def _rodar_simulacao(
    num_contas: int = 3,
    saldo_inicial: float = 500.0,
    num_threads: int = 6,
    transferencias_por_thread: int = 10_000,
) -> tuple[list[ContaBancaria], float]:
    """Cria contas, roda threads e retorna (contas, saldo_antes)."""
    contas = [ContaBancaria(f"Conta-{i}", saldo_inicial) for i in range(num_contas)]
    saldo_antes = sum(c.saldo for c in contas)

    threads = [
        threading.Thread(target=_worker, args=(contas, transferencias_por_thread))
        for _ in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return contas, saldo_antes


# ---------------------------------------------------------------------------
# Casos de teste
# ---------------------------------------------------------------------------

class TestInvarianteMonetaria(unittest.TestCase):
    """
    A soma dos saldos deve ser idêntica antes e depois de qualquer
    quantidade de transferências simultâneas. É a invariante fundamental
    de qualquer sistema bancário.
    """

    def test_saldo_total_preservado_sob_alta_carga(self):
        """Com 6 threads e 10.000 transferências cada, o saldo total não deve mudar."""
        contas, saldo_antes = _rodar_simulacao()
        saldo_depois = sum(c.saldo for c in contas)

        self.assertAlmostEqual(
            saldo_depois,
            saldo_antes,
            delta=0.01,
            msg=(
                f"Invariante violada! Antes: R${saldo_antes:.2f}, "
                f"Depois: R${saldo_depois:.2f}. "
                f"Desvio: R${abs(saldo_depois - saldo_antes):.2f}"
            ),
        )

    def test_saldo_total_preservado_com_muitas_contas(self):
        """Mesmo com 10 contas envolvidas, a invariante deve ser mantida."""
        contas, saldo_antes = _rodar_simulacao(num_contas=10, saldo_inicial=200.0)
        saldo_depois = sum(c.saldo for c in contas)

        self.assertAlmostEqual(saldo_depois, saldo_antes, delta=0.01)


class TestSaldoNaoNegativo(unittest.TestCase):
    """Nenhuma conta deve terminar com saldo negativo."""

    def test_sem_saldo_negativo_em_alta_concorrencia(self):
        """
        O lock deve garantir que a checagem de saldo suficiente e o débito
        sejam atômicos — evitando que múltiplas threads debitam além do saldo.
        """
        contas, _ = _rodar_simulacao(saldo_inicial=VALOR_TRANSFERENCIA * 2)

        for conta in contas:
            self.assertGreaterEqual(
                conta.saldo,
                0.0,
                msg=f"Saldo negativo em {conta.id}: R${conta.saldo:.2f}",
            )


class TestSemDeadlock(unittest.TestCase):
    """A ordenação de locks deve prevenir deadlocks entre quaisquer pares de contas."""

    TIMEOUT_SEGUNDOS = 15

    def test_simulacao_termina_sem_deadlock(self):
        """
        A simulação deve terminar dentro do timeout.
        Se houver deadlock, o join() travará e o teste falhará por timeout.
        """
        contas, _ = _rodar_simulacao(
            num_contas=4,
            num_threads=8,
            transferencias_por_thread=20_000,
        )

        # Se chegou aqui, nenhum deadlock ocorreu
        self.assertTrue(True, "Simulação concluída sem deadlock.")

    def test_transferencia_bidirecional_nao_causa_deadlock(self):
        """
        O cenário clássico de deadlock: thread A transfere A→B enquanto
        thread B transfere B→A. A ordenação global dos locks deve prevenir isso.
        """
        conta_a = ContaBancaria("Conta-A", 1_000.0)
        conta_b = ContaBancaria("Conta-B", 1_000.0)
        saldo_antes = conta_a.saldo + conta_b.saldo

        resultados = []

        def a_para_b():
            for _ in range(3_000):
                conta_a.transferir(conta_b, VALOR_TRANSFERENCIA)
            resultados.append("a_para_b concluída")

        def b_para_a():
            for _ in range(3_000):
                conta_b.transferir(conta_a, VALOR_TRANSFERENCIA)
            resultados.append("b_para_a concluída")

        t1 = threading.Thread(target=a_para_b)
        t2 = threading.Thread(target=b_para_a)
        t1.start()
        t2.start()
        t1.join(timeout=self.TIMEOUT_SEGUNDOS)
        t2.join(timeout=self.TIMEOUT_SEGUNDOS)

        self.assertEqual(len(resultados), 2, "Deadlock detectado: nem todas as threads terminaram.")

        saldo_depois = conta_a.saldo + conta_b.saldo
        self.assertAlmostEqual(saldo_depois, saldo_antes, delta=0.01)


if __name__ == "__main__":
    print("=" * 60)
    print("TESTES DA IMPLEMENTAÇÃO BASE — espera-se que FALHEM (bug didático)")
    print("=" * 60)
    unittest.main(verbosity=2)

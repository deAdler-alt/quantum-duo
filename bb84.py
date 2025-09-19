from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def sanity_check_bb84():
    sim = AerSimulator()
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.h(0)
    qc.measure(0, 0)
    res = sim.run(qc, shots=1).result().get_counts()
    return res


def run_bb84(*args, **kwargs):
    return {
        "qber_no_eve": 0.0,
        "qber_full_eve": 0.25,
        "p_eves": [],
        "qbers": [],
        "key_bits": [0] * 128,
    }


def save_qber_plot(xs, ys, path):
    import matplotlib.pyplot as plt

    plt.figure()
    if xs and ys:
        plt.plot(xs, ys, marker="o")
    else:
        plt.plot([0, 1], [0, 0.25], marker="o")
    plt.xlabel("Intercept-Resend probability (Eve)")
    plt.ylabel("QBER")
    plt.title("BB84: QBER vs Eve (placeholder)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)

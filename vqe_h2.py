from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.circuit.library import EfficientSU2
from qiskit import QuantumCircuit
from scipy.optimize import minimize

H2_COEFFS: Dict[float, Dict[str, float]] = {
    0.30: {"I": -0.8100, "Z0": 0.0450, "Z1": 0.0450, "ZZ": 0.1900, "XX": -0.6800, "YY": -0.6800},
    0.50: {"I": -1.0200, "Z0": 0.0300, "Z1": 0.0300, "ZZ": 0.1200, "XX": -0.7200, "YY": -0.7200},
    0.70: {"I": -1.1200, "Z0": 0.0100, "Z1": 0.0100, "ZZ": 0.0800, "XX": -0.7500, "YY": -0.7500},
    0.90: {"I": -1.0800, "Z0": 0.0050, "Z1": 0.0050, "ZZ": 0.0600, "XX": -0.7000, "YY": -0.7000},
    1.10: {"I": -1.0400, "Z0": 0.0030, "Z1": 0.0030, "ZZ": 0.0500, "XX": -0.6600, "YY": -0.6600},
    1.30: {"I": -1.0100, "Z0": 0.0020, "Z1": 0.0020, "ZZ": 0.0400, "XX": -0.6200, "YY": -0.6200}
}

def nearest_R_key(R: float) -> float:
    keys = sorted(H2_COEFFS.keys())
    return min(keys, key=lambda k: abs(k - R))

def build_qubit_hamiltonian(R: float) -> SparsePauliOp:
    k = nearest_R_key(R)
    c = H2_COEFFS[k]
    paulis = ["II", "ZI", "IZ", "ZZ", "XX", "YY"]
    coeffs = [c["I"], c["Z0"], c["Z1"], c["ZZ"], c["XX"], c["YY"]]
    return SparsePauliOp.from_list(list(zip(paulis, coeffs)))

def expectation(op: SparsePauliOp, state: Statevector) -> float:
    mat = op.to_matrix(sparse=False)
    v = state.data
    val = np.vdot(v, mat @ v)
    return float(np.real(val))

def vqe_energy_for_R(R: float, seed: int = 1, reps: int = 2, maxiter: int = 200) -> float:
    H = build_qubit_hamiltonian(R)
    n = H.num_qubits
    ansatz = EfficientSU2(num_qubits=n, entanglement="full", reps=reps)
    rng = np.random.default_rng(seed)
    theta0 = rng.standard_normal(ansatz.num_parameters) * 0.1

    def objective(theta: np.ndarray) -> float:
        qc: QuantumCircuit = ansatz.assign_parameters(theta)
        state = Statevector.from_instruction(qc)
        return expectation(H, state)

    res = minimize(objective, theta0, method="L-BFGS-B", options={"maxiter": maxiter})
    return float(res.fun)

def run_vqe_curve(R_list: List[float], seed: int = 1, reps: int = 2, maxiter: int = 200) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for R in R_list:
        E = vqe_energy_for_R(R, seed=seed, reps=reps, maxiter=maxiter)
        out.append({"R": float(nearest_R_key(R)), "E": float(E)})
    seen = {}
    dedup = []
    for p in out:
        k = (p["R"], round(p["E"], 6))
        if k in seen:
            continue
        seen[k] = True
        dedup.append(p)
    dedup.sort(key=lambda x: x["R"])
    return dedup

def save_energy_plot(points, path: str):
    xs = [p["R"] for p in points]
    ys = [p["E"] for p in points]
    i_min = min(range(len(ys)), key=lambda i: ys[i])
    plt.figure()
    plt.plot(xs, ys, marker="o")
    plt.scatter([xs[i_min]], [ys[i_min]], s=70)
    plt.xlabel("Bond length R (Å)")
    plt.ylabel("Energy (Hartree)")
    plt.title("H₂ potential energy curve (VQE)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)

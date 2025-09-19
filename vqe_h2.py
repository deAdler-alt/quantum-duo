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

def exact_energy_for_R(R: float) -> float:
    H = build_qubit_hamiltonian(R)
    mat = H.to_matrix(sparse=False)
    w, _ = np.linalg.eigh(mat)
    return float(np.min(np.real(w)))

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
        rkey = float(nearest_R_key(R))
        e_exact = exact_energy_for_R(rkey)
        e_vqe = vqe_energy_for_R(rkey, seed=seed, reps=reps, maxiter=maxiter)
        err = float(abs(e_vqe - e_exact))
        out.append({"R": rkey, "E_vqe": e_vqe, "E_exact": e_exact, "error": err})
    seen = {}
    dedup = []
    for p in out:
        k = (p["R"], round(p["E_vqe"], 6), round(p["E_exact"], 6))
        if k in seen:
            continue
        seen[k] = True
        dedup.append(p)
    dedup.sort(key=lambda x: x["R"])
    return dedup

def save_energy_plot(points, path: str):
    xs = [p["R"] for p in points]
    y_vqe = [p["E_vqe"] for p in points]
    y_exact = [p["E_exact"] for p in points]
    i_min = min(range(len(y_vqe)), key=lambda i: y_vqe[i])
    plt.figure()
    plt.plot(xs, y_vqe, marker="o", label="VQE")
    plt.plot(xs, y_exact, marker="s", label="Exact")
    plt.scatter([xs[i_min]], [y_vqe[i_min]], s=70)
    plt.xlabel("Bond length R (Å)")
    plt.ylabel("Relative energy (a.u.)")
    plt.title("H₂ potential energy curve")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)

def save_error_plot(points, path: str):
    xs = [p["R"] for p in points]
    errs = [p["error"] for p in points]
    plt.figure()
    plt.plot(xs, errs, marker="o")
    plt.xlabel("Bond length R (Å)")
    plt.ylabel("|E_VQE − E_exact| (a.u.)")
    plt.title("VQE absolute error vs bond length")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)

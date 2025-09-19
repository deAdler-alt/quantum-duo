from __future__ import annotations
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np
import matplotlib.pyplot as plt
import csv

def _prepare_state(bit: int, basis: str) -> QuantumCircuit:
    qc = QuantumCircuit(1, 1)
    if basis == 'Z':
        if bit == 1:
            qc.x(0)
    elif basis == 'X':
        qc.h(0)
        if bit == 1:
            qc.z(0)
    else:
        raise ValueError("basis must be 'Z' or 'X'")
    return qc

def _measure_in_basis(qc: QuantumCircuit, basis: str, sim: AerSimulator) -> int:
    mqc = qc.copy()
    if basis == 'X':
        mqc.h(0)
    mqc.measure(0, 0)
    res = sim.run(mqc, shots=1).result().get_counts()
    return 1 if res.get('1', 0) == 1 else 0

def _bb84_single(n=512, p_eve=0.0, p_noise=0.0, seed=123) -> dict:
    rng = np.random.default_rng(seed)
    sim = AerSimulator(seed_simulator=seed)
    alice_bits = rng.integers(0, 2, size=n)
    alice_bases = rng.choice(['Z','X'], size=n)
    bob_bases = rng.choice(['Z','X'], size=n)
    sift_alice, sift_bob = [], []
    for i in range(n):
        qc = _prepare_state(int(alice_bits[i]), alice_bases[i])
        if rng.random() < p_eve:
            eve_basis = rng.choice(['Z','X'])
            eve_bit = _measure_in_basis(qc, eve_basis, sim)
            qc = _prepare_state(eve_bit, eve_basis)
        if p_noise > 0 and rng.random() < p_noise:
            qc.x(0)
        bob_bit = _measure_in_basis(qc, bob_bases[i], sim)
        if alice_bases[i] == bob_bases[i]:
            sift_alice.append(int(alice_bits[i]))
            sift_bob.append(int(bob_bit))
    kept = len(sift_alice)
    if kept == 0:
        return {"qber": None, "key_bits": [], "kept": 0}
    a = np.array(sift_alice, dtype=int)
    b = np.array(sift_bob, dtype=int)
    qber = float(np.mean(a != b))
    return {"qber": qber, "key_bits": sift_alice, "kept": kept}

def _collect_key_minlen(min_len=128, n=512, p_noise=0.0, seed=123) -> list[int]:
    bits = []
    hop = 0
    while len(bits) < min_len and hop < 10:
        r = _bb84_single(n=n, p_eve=0.0, p_noise=p_noise, seed=seed+hop)
        bits.extend(r["key_bits"])
        hop += 1
    return bits[:min_len]

def run_bb84(n=512, p_eve=0.0, p_noise=0.0, seed=123, steps=8) -> dict:
    res_clean = _bb84_single(n=n, p_eve=0.0, p_noise=p_noise, seed=seed)
    res_full = _bb84_single(n=n, p_eve=1.0, p_noise=p_noise, seed=seed)
    p_eves = np.linspace(0.0, 1.0, steps)
    qbers = []
    for k, p in enumerate(p_eves):
        rr = _bb84_single(n=n, p_eve=float(p), p_noise=p_noise, seed=seed+k+1)
        qbers.append(rr["qber"] if rr["qber"] is not None else 0.0)
    key_bits = _collect_key_minlen(min_len=128, n=n, p_noise=p_noise, seed=seed+99)
    return {
        "qber_no_eve": float(res_clean["qber"]) if res_clean["qber"] is not None else None,
        "qber_full_eve": float(res_full["qber"]) if res_full["qber"] is not None else None,
        "p_eves": [float(x) for x in p_eves],
        "qbers": [float(x) for x in qbers],
        "key_bits": [int(b) for b in key_bits],
    }

def save_qber_plot(xs, ys, path: str):
    plt.figure()
    plt.plot(xs, ys, marker='o')
    plt.xlabel("Intercept-Resend probability (Eve)")
    plt.ylabel("QBER")
    plt.title("BB84: QBER vs Eve attack probability")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)

def sanity_check_bb84():
    sim = AerSimulator(seed_simulator=1)
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.h(0)
    qc.measure(0, 0)
    res = sim.run(qc, shots=1).result().get_counts()
    return res

def run_qber_heatmap(n=512, pe_min=0.0, pe_max=1.0, pe_steps=6, pn_min=0.0, pn_max=0.2, pn_steps=6, seed=123, avg=1) -> dict:
    p_eves = np.linspace(pe_min, pe_max, pe_steps)
    p_noises = np.linspace(pn_min, pn_max, pn_steps)
    mat = np.zeros((pn_steps, pe_steps), dtype=float)
    idx = 0
    for i, pn in enumerate(p_noises):
        for j, pe in enumerate(p_eves):
            acc = 0.0
            for k in range(avg):
                r = _bb84_single(n=n, p_eve=float(pe), p_noise=float(pn), seed=seed+idx+k)
                acc += 0.0 if r["qber"] is None else float(r["qber"])
            mat[i, j] = acc / float(avg)
            idx += 17
    return {"p_eves": [float(x) for x in p_eves], "p_noises": [float(x) for x in p_noises], "qber": mat}

def save_qber_heatmap(p_eves, p_noises, mat, path: str):
    plt.figure()
    extent = [min(p_eves), max(p_eves), min(p_noises), max(p_noises)]
    plt.imshow(mat, origin="lower", aspect="auto", extent=extent, interpolation="nearest")
    plt.colorbar(label="QBER")
    plt.xlabel("Eve probability")
    plt.ylabel("Noise probability")
    plt.title("BB84: QBER heatmap")
    plt.tight_layout()
    plt.savefig(path)

def bb84_walkthrough(n=16, p_eve=0.0, p_noise=0.0, seed=123) -> dict:
    rng = np.random.default_rng(seed)
    sim = AerSimulator(seed_simulator=seed)
    alice_bits = rng.integers(0, 2, size=n)
    alice_bases = rng.choice(['Z','X'], size=n)
    bob_bases = rng.choice(['Z','X'], size=n)
    bob_bits = np.zeros(n, dtype=int)
    keep = np.zeros(n, dtype=int)
    sift_a, sift_b = [], []
    for i in range(n):
        qc = _prepare_state(int(alice_bits[i]), alice_bases[i])
        if rng.random() < p_eve:
            eve_basis = rng.choice(['Z','X'])
            eve_bit = _measure_in_basis(qc, eve_basis, sim)
            qc = _prepare_state(eve_bit, eve_basis)
        if p_noise > 0 and rng.random() < p_noise:
            qc.x(0)
        bob_bits[i] = _measure_in_basis(qc, bob_bases[i], sim)
        if alice_bases[i] == bob_bases[i]:
            keep[i] = 1
            sift_a.append(int(alice_bits[i]))
            sift_b.append(int(bob_bits[i]))
    qber = None
    if len(sift_a) > 0:
        a = np.array(sift_a, dtype=int)
        b = np.array(sift_b, dtype=int)
        qber = float(np.mean(a != b))
    return {
        "alice_bits": [int(x) for x in alice_bits],
        "alice_bases": [str(x) for x in alice_bases],
        "bob_bases": [str(x) for x in bob_bases],
        "bob_bits": [int(x) for x in bob_bits],
        "keep": [int(x) for x in keep],
        "qber": qber
    }

def save_walkthrough_csv(walk: dict, path: str):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "alice_bit", "alice_basis", "bob_basis", "bob_bit", "kept"])
        for i in range(len(walk["alice_bits"])):
            w.writerow([
                i,
                walk["alice_bits"][i],
                walk["alice_bases"][i],
                walk["bob_bases"][i],
                walk["bob_bits"][i],
                walk["keep"][i],
            ])

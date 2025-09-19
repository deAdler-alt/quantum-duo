# Quantum Duo: Secure Quantum Chemistry

Think Quantum. Build Beyond.
End-to-end demo that combines **BB84 quantum key distribution** with a **VQE simulation of H₂**.
If the channel looks secure (low QBER), we run VQE, then **encrypt the results** with a key derived from BB84.

<p align="center">
  <img src="outputs/h2_energy_curve.png" alt="H2 energy curve" width="45%"/>
  <img src="outputs/h2_error_curve.png" alt="VQE error" width="45%"/>
</p>

## Why this project?

* Covers two tracks at once: **Cryptography & Secure Communications** + **Quantum Simulations**
* Clear, visual artifacts: QBER plot, energy curve, error curve, optional heatmap and CSV walkthrough
* Minimal setup; runs on a laptop (statevector simulation, no hardware required)

---

## Features

* **BB84 simulation** with intercept-resend attacker and channel noise
* **QBER decision gate** with a configurable threshold
* **VQE for H₂** using a lightweight 2-qubit Hamiltonian and classical optimizer
* **Exact baseline** and per-point **VQE error**
* **Secure output**: by default **AES-CTR** with a **SHA-256 KDF** (fallback: XOR)
* **Auto-generated artifacts**: plots, JSON, CSV, and a single-file **HTML report**
* Optional **QBER heatmap** and **BB84 educational walkthrough** (bit-level CSV)

---

## Project structure

```
.
├── bb84.py                 # BB84 core + heatmap + walkthrough
├── vqe_h2.py               # VQE, exact baseline, plots
├── crypto_utils.py         # KDF, AES-CTR (fallback XOR), base64 helpers
├── main.py                 # CLI, end-to-end flow, report/CSV generation
├── requirements.txt
├── LICENSE
└── outputs/                # generated artifacts (gitignored by default)
```

---

## Quick start

### 1) Environment

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Run the full pipeline (default parameters)

```bash
python main.py
open outputs/report.html     # or: start outputs\report.html on Windows
```

You’ll get (among others):

* `outputs/qber_plot.png`
* `outputs/h2_energy_curve.png`, `outputs/h2_error_curve.png`
* `outputs/vqe_results.aes` and `outputs/vqe_results.aes.b64` (or `.enc`/`.enc.b64` with `--xor`)
* `outputs/points.csv`, `outputs/vqe_results.json`
* `outputs/report.html`

### 3) Examples

Higher QKD load and custom VQE grid:

```bash
python main.py --n 2048 --eve 0.4 --steps 10 --rgrid 0.35,0.45,0.6,0.75,0.9,1.2 --maxiter 150 --reps 2 --seed 7
```

Produce a QBER heatmap and a 16-bit BB84 walkthrough CSV:

```bash
python main.py --heatmap --hm_pe 0.0,1.0,10 --hm_pn 0.0,0.2,10 --hm_avg 2 --demo_bits 16
```

Fallback to XOR encryption (if you want to avoid the `cryptography` dependency):

```bash
python main.py --xor
```

---

## Command-line options

| Flag          |                   Default | Description                                                                 |
| ------------- | ------------------------: | --------------------------------------------------------------------------- |
| `--n`         |                      1024 | Number of raw BB84 rounds per sweep point                                   |
| `--eve`       |                      0.25 | Intercept-resend probability for Eve (sweep uses its own grid for the plot) |
| `--noise`     |                       0.0 | Channel bit-flip probability                                                |
| `--steps`     |                         8 | Points in the QBER vs Eve plot                                              |
| `--rgrid`     | `0.3,0.5,0.7,0.9,1.1,1.3` | Bond lengths (Å) for VQE                                                    |
| `--maxiter`   |                       200 | Max optimizer iterations for VQE                                            |
| `--reps`      |                         2 | Ansatz depth (EfficientSU2 reps)                                            |
| `--seed`      |                         1 | Global seed (BB84 and VQE)                                                  |
| `--xor`       |                       off | Use XOR instead of AES-CTR                                                  |
| `--heatmap`   |                       off | Generate QBER heatmap                                                       |
| `--hm_pe`     |               `0.0,1.0,6` | Heatmap Eve range and steps: min,max,steps                                  |
| `--hm_pn`     |               `0.0,0.2,6` | Heatmap noise range and steps: min,max,steps                                |
| `--hm_avg`    |                         1 | Repeats per heatmap cell (averaging)                                        |
| `--demo_bits` |                         0 | If >0, export a BB84 bit-level walkthrough CSV of that length               |

---

## What it does

1. **BB84 phase**
   Generates random bits and bases for Alice and Bob. Optionally inserts an intercept-resend attacker (Eve) with probability `p_eve` and a simple channel bit-flip noise `p_noise`.
   Keeps only positions with matching bases (sifting) and computes **QBER**. Plots **QBER vs. `p_eve`**. If QBER under a threshold (0.11), we proceed.

2. **VQE phase**
   Builds a compact 2-qubit Hamiltonian for H₂ at selected bond lengths (Å), runs **VQE** with `EfficientSU2` ansatz and **L-BFGS-B** optimizer, and computes the **exact ground state** by diagonalizing the same Hamiltonian.
   Saves the **energy curve** with both **VQE** and **Exact**, plus an **absolute error** plot.

3. **Secure delivery phase**
   Derives a 256-bit key from BB84 bits via **SHA-256** and encrypts the results with **AES-CTR** (nonce prepended). If `--xor` is set or AES is unavailable, uses XOR as a minimal fallback.
   Exports binary and Base64 formats and generates a self-contained **HTML report** with all artifacts linked.

---

## How it works (tech details)

* **BB84**
  State preparation in Z/X, intercept-resend attacker measured in a random basis, optional channel bit-flip noise. Sifting by matching bases, **QBER = mean(bits\_Alice != bits\_Bob)**. We also provide:

  * **Heatmap** of QBER vs `(p_eve, p_noise)`
  * **Walkthrough CSV** tracing each of `N` positions (bits, bases, kept flag)

* **VQE**
  Variational ansatz: `EfficientSU2(num_qubits=2, entanglement="full", reps=REPS)`
  Objective: ⟨ψ(θ)|H|ψ(θ)⟩ evaluated from the statevector. Optimization via **SciPy L-BFGS-B**.
  We include an **exact baseline** by diagonalizing the same 2-qubit Hamiltonian to validate VQE.

* **Security**
  KDF: **SHA-256** over BB84 key material → 32-byte key.
  Cipher: **AES-CTR** with a 16-byte random nonce; output file prepends nonce.
  Fallback: XOR when `--xor` is set or `cryptography` is not installed.
  Files: `.aes`/`.aes.b64` or `.enc`/`.enc.b64` plus `vqe_results.json` (plaintext for inspection).

---

## Outputs

All generated in `outputs/`:

* `qber_plot.png` — QBER vs Eve probability
* `h2_energy_curve.png` — H₂ energy vs bond length (VQE vs Exact)
* `h2_error_curve.png` — |E\_VQE − E\_exact| vs bond length
* `qber_heatmap.png` — enabled with `--heatmap`
* `bb84_walkthrough.csv` — enabled with `--demo_bits N`
* `points.csv`, `vqe_results.json` — numeric results (relative a.u.)
* `vqe_results.aes` and `vqe_results.aes.b64` — encrypted payload (default), or `.enc`/`.enc.b64` with `--xor`
* `report.html` — one-page summary with images, metrics, and links

---

## Reproducibility

* Use `--seed` to get deterministic BB84 sequences and VQE initial parameters.
* Plots and CSVs are regenerated on each run with the same seed and parameters.

---

## Limitations

* The H₂ Hamiltonians are a compact, pre-tabulated 2-qubit model for a fast demo; values are reported in **relative a.u.** to emphasize shape and minima, not absolute chemical accuracy.
* BB84 model is simplified (intercept-resend + bit-flip noise).
* AES-CTR provides confidentiality but not authenticity; for production use prefer **AES-GCM** or AES-CTR + **HMAC-SHA-256**.

---

## Install and dependencies

* Python 3.10+
* `pip install -r requirements.txt` installs:
  `qiskit`, `qiskit-aer`, `numpy`, `matplotlib`, `scipy`, `cryptography`

---

## License

This project is open-sourced under the **MIT License**. See `LICENSE`.

---

## References

* QKD: C. H. Bennett and G. Brassard, *Proceedings of IEEE Int. Conf. on Computers, Systems and Signal Processing*, Bangalore, India, 1984.
* VQE: A. Peruzzo et al., *A variational eigenvalue solver on a photonic quantum processor*, Nat. Commun. 5, 4213 (2014).
* Qiskit documentation: [https://qiskit.org/documentation/](https://qiskit.org/documentation/)
* SciPy optimize: [https://docs.scipy.org/doc/scipy/reference/optimize.html](https://docs.scipy.org/doc/scipy/reference/optimize.html)

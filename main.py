import os, json
from bb84 import sanity_check_bb84, run_bb84, save_qber_plot
from vqe_h2 import run_vqe_curve, save_energy_plot
from crypto_utils import bits_to_key_bytes, json_encrypt, json_decrypt

OUTDIR = "outputs"; os.makedirs(OUTDIR, exist_ok=True)
QBER_THRESHOLD = 0.11

def main():
    print("== Sanity check: Qiskit simulator ==")
    print(sanity_check_bb84())

    print("\n== BB84 (placeholder) ==")
    bb = run_bb84()
    save_qber_plot(bb["p_eves"], bb["qbers"], os.path.join(OUTDIR, "qber_plot.png"))
    print(f"QBER(no attack) ~ {bb['qber_no_eve']}, QBER(full attack) ~ {bb['qber_full_eve']}")

    if bb["qber_no_eve"] > QBER_THRESHOLD:
        print("[ABORT] Channel insecure (placeholder).")
        return

    key_bytes = bits_to_key_bytes(bb["key_bits"])
    print(f"Key bytes length: {len(key_bytes)}")

    print("\n== VQE H2 curve (placeholder) ==")
    points = run_vqe_curve([0.3,0.5,0.7,0.9,1.1,1.3], seed=2)
    save_energy_plot(points, os.path.join(OUTDIR, "h2_energy_curve.png"))

    plain = {"points": points, "unit":"Hartree"}
    enc = json_encrypt(plain, key_bytes)
    with open(os.path.join(OUTDIR,"vqe_results.enc"), "wb") as f: f.write(enc)
    with open(os.path.join(OUTDIR,"vqe_results.json"), "w") as f: json.dump(plain, f)
    # sanity decrypt
    assert json_decrypt(enc, key_bytes) == plain
    print(f"[OK] Files saved in {OUTDIR}/")

if __name__ == "__main__":
    main()

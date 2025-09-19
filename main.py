import os, json, argparse
from bb84 import sanity_check_bb84, run_bb84, save_qber_plot
from vqe_h2 import run_vqe_curve, save_energy_plot
from crypto_utils import bits_to_key_bytes, json_encrypt, json_decrypt, to_base64_str

OUTDIR = "outputs"

def parse_grid(s):
    return [float(x) for x in s.split(",") if x.strip()]

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1024)
    ap.add_argument("--eve", type=float, default=0.25)
    ap.add_argument("--noise", type=float, default=0.0)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--rgrid", type=str, default="0.3,0.5,0.7,0.9,1.1,1.3")
    ap.add_argument("--maxiter", type=int, default=200)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    print("== Sanity check: Qiskit simulator ==")
    print(sanity_check_bb84())

    print("\n== BB84 (real) ==")
    bb = run_bb84(n=args.n, p_eve=args.eve, p_noise=args.noise, seed=args.seed, steps=args.steps)
    qber_path = os.path.join(OUTDIR, "qber_plot.png")
    save_qber_plot(bb["p_eves"], bb["qbers"], qber_path)
    print(f"Params: n={args.n}, eve={args.eve}, noise={args.noise}, steps={args.steps}, seed={args.seed}")
    print(f"QBER(no attack) = {bb['qber_no_eve']:.3f}, QBER(full attack) = {bb['qber_full_eve']:.3f}")
    print(f"Saved: {qber_path}")

    threshold = 0.11
    current_qber = bb["qber_no_eve"]
    if current_qber is None or current_qber > threshold:
        print(f"[ABORT] Channel insecure: QBER={current_qber}, threshold={threshold}")
        return

    key_bytes = bits_to_key_bytes(bb["key_bits"])
    print(f"Key bytes length: {len(key_bytes)}")

    print("\n== VQE H2 curve (real) ==")
    grid = parse_grid(args.rgrid)
    points = run_vqe_curve(grid, seed=args.seed + 1, reps=args.reps, maxiter=args.maxiter)
    for p in points:
        print(f"R={p['R']:.2f} Å, E={p['E']:.6f} a.u.")
    e_path = os.path.join(OUTDIR, "h2_energy_curve.png")
    save_energy_plot(points, e_path)
    print(f"Saved: {e_path}")

    plain = {"points": points, "unit": "Relative a.u."}
    enc = json_encrypt(plain, key_bytes)
    enc_path = os.path.join(OUTDIR, "vqe_results.enc")
    b64_path = os.path.join(OUTDIR, "vqe_results.enc.b64")
    json_path = os.path.join(OUTDIR, "vqe_results.json")
    with open(enc_path, "wb") as f:
        f.write(enc)
    with open(b64_path, "w") as f:
        f.write(to_base64_str(enc))
    with open(json_path, "w") as f:
        json.dump(plain, f)
    dec = json_decrypt(enc, key_bytes)
    assert dec == plain
    print(f"Saved: {enc_path}")
    print(f"Saved: {b64_path}")
    print(f"Saved: {json_path}")
    print("\nSample plaintext:", dec["points"][:2])
    print("\n[OK] End-to-end flow complete")

if __name__ == "__main__":
    main()

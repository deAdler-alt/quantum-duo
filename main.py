import os, json, argparse, csv
from bb84 import sanity_check_bb84, run_bb84, save_qber_plot
from vqe_h2 import run_vqe_curve, save_energy_plot, save_error_plot
from crypto_utils import (
    bits_to_key_bytes, derive_key_sha256, has_aes,
    json_encrypt_xor, json_decrypt_xor,
    aes_ctr_encrypt, aes_ctr_decrypt, to_base64_str
)

OUTDIR = "outputs"

def parse_grid(s):
    return [float(x) for x in s.split(",") if x.strip()]

def write_csv(points, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["R_Angstrom", "E_vqe_au", "E_exact_au", "abs_error_au"])
        for p in points:
            w.writerow([p["R"], p["E_vqe"], p["E_exact"], p["error"]])

def write_report_html(path, args, threshold, bb, points, artifacts):
    rows = "\n".join(
        f"<tr><td>{p['R']:.2f}</td><td>{p['E_vqe']:.6f}</td><td>{p['E_exact']:.6f}</td><td>{p['error']:.3e}</td></tr>"
        for p in points
    )
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Quantum Duo Report</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;color:#111}}
h1{{margin-top:0}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.card{{border:1px solid #e5e7eb;border-radius:12px;padding:16px;box-shadow:0 1px 2px rgba(0,0,0,.05)}}
small{{color:#6b7280}}
table{{border-collapse:collapse;width:100%}}
th,td{{border-bottom:1px solid #eee;padding:8px;text-align:right}}
th:first-child,td:first-child{{text-align:left}}
a{{color:#2563eb;text-decoration:none}}
a:hover{{text-decoration:underline}}
code{{background:#f3f4f6;padding:2px 6px;border-radius:6px}}
img{{max-width:100%;height:auto;border-radius:12px;border:1px solid #eee}}
</style>
</head>
<body>
<h1>Quantum Duo: Secure Quantum Chemistry — Report</h1>
<p><small>Auto-generated artifacts for one run</small></p>

<div class="grid">
  <div class="card">
    <h2>Run parameters</h2>
    <ul>
      <li>n = {args.n}</li>
      <li>eve = {args.eve}</li>
      <li>noise = {args.noise}</li>
      <li>steps = {args.steps}</li>
      <li>rgrid = {args.rgrid}</li>
      <li>maxiter = {args.maxiter}</li>
      <li>reps = {args.reps}</li>
      <li>seed = {args.seed}</li>
      <li>encryption = {artifacts['enc_mode']}</li>
    </ul>
  </div>

  <div class="card">
    <h2>BB84 summary</h2>
    <p>QBER(no attack) = <b>{bb['qber_no_eve']:.3f}</b>, threshold = <b>{threshold}</b></p>
    <p>QBER(full attack) = {bb['qber_full_eve']:.3f}</p>
    <p>Key material bytes = {artifacts['raw_key_bytes']}, derived key bytes = {artifacts['derived_key_bytes']}</p>
  </div>
</div>

<div class="card" style="margin-top:16px">
  <h2>BB84 plot</h2>
  <img src="qber_plot.png" alt="QBER vs Eve">
</div>

<div class="grid" style="margin-top:16px">
  <div class="card">
    <h2>H₂ energy curve</h2>
    <img src="h2_energy_curve.png" alt="Energy curve">
  </div>
  <div class="card">
    <h2>VQE absolute error</h2>
    <img src="h2_error_curve.png" alt="Error curve">
  </div>
</div>

<div class="card" style="margin-top:16px">
  <h2>Data table</h2>
  <table>
    <thead><tr><th>R (Å)</th><th>E_vqe (a.u.)</th><th>E_exact (a.u.)</th><th>|error| (a.u.)</th></tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</div>

<div class="card" style="margin-top:16px">
  <h2>Artifacts</h2>
  <ul>
    <li><a href="points.csv">points.csv</a></li>
    <li><a href="vqe_results.json">vqe_results.json</a></li>
    <li><a href="{artifacts['enc_path_name']}">{artifacts['enc_path_name']}</a> ({artifacts['enc_mode']})</li>
    <li><a href="{artifacts['enc_b64_name']}">{artifacts['enc_b64_name']}</a></li>
    <li><a href="qber_plot.png">qber_plot.png</a></li>
    <li><a href="h2_energy_curve.png">h2_energy_curve.png</a></li>
    <li><a href="h2_error_curve.png">h2_error_curve.png</a></li>
  </ul>
</div>

<p style="margin-top:16px"><small>Unit note: energies are plotted as relative a.u. for a fast demo. Shapes and minima are meaningful; absolute scale is illustrative.</small></p>
</body></html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

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
    ap.add_argument("--xor", action="store_true")
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

    raw_key = bits_to_key_bytes(bb["key_bits"])
    key32 = derive_key_sha256(raw_key) if has_aes() else raw_key
    print(f"Key material bytes: {len(raw_key)}, derived key bytes: {len(key32)}")

    print("\n== VQE H2 curve (real + exact baseline) ==")
    grid = parse_grid(args.rgrid)
    points = run_vqe_curve(grid, seed=args.seed + 1, reps=args.reps, maxiter=args.maxiter)
    for p in points:
        print(f"R={p['R']:.2f} Å, E_vqe={p['E_vqe']:.6f} a.u., E_exact={p['E_exact']:.6f} a.u., error={p['error']:.6e}")
    e_path = os.path.join(OUTDIR, "h2_energy_curve.png")
    err_path = os.path.join(OUTDIR, "h2_error_curve.png")
    save_energy_plot(points, e_path)
    save_error_plot(points, err_path)
    print(f"Saved: {e_path}")
    print(f"Saved: {err_path}")

    enc_mode = "AES-CTR" if has_aes() and not args.xor else "XOR"
    if enc_mode == "AES-CTR":
        data = json.dumps({"points": points, "unit": "Relative a.u."}, separators=(',',':')).encode("utf-8")
        blob = aes_ctr_encrypt(data, key32)
        enc_path = os.path.join(OUTDIR, "vqe_results.aes")
        enc_b64_path = os.path.join(OUTDIR, "vqe_results.aes.b64")
        with open(enc_path, "wb") as f: f.write(blob)
        with open(enc_b64_path, "w") as f: f.write(to_base64_str(blob))
        dec = json.loads(aes_ctr_decrypt(blob, key32).decode("utf-8"))
    else:
        enc = json_encrypt_xor({"points": points, "unit": "Relative a.u."}, raw_key)
        enc_path = os.path.join(OUTDIR, "vqe_results.enc")
        enc_b64_path = os.path.join(OUTDIR, "vqe_results.enc.b64")
        with open(enc_path, "wb") as f: f.write(enc)
        with open(enc_b64_path, "w") as f: f.write(to_base64_str(enc))
        dec = json_decrypt_xor(enc, raw_key)
    assert dec["points"] == points

    json_path = os.path.join(OUTDIR, "points.csv")
    write_csv(points, json_path)
    print(f"Saved: {json_path}")

    artifacts = {
        "enc_mode": enc_mode,
        "enc_path_name": os.path.basename(enc_path),
        "enc_b64_name": os.path.basename(enc_b64_path),
        "raw_key_bytes": len(raw_key),
        "derived_key_bytes": len(key32)
    }
    report_path = os.path.join(OUTDIR, "report.html")
    write_report_html(report_path, args, threshold, bb, points, artifacts)
    print(f"Saved: {report_path}")

    with open(os.path.join(OUTDIR, "vqe_results.json"), "w") as f:
        json.dump({"points": points, "unit": "Relative a.u."}, f)
    print(f"Saved: {os.path.join(OUTDIR, 'vqe_results.json')}")
    print("\n[OK] End-to-end flow complete")

if __name__ == "__main__":
    main()

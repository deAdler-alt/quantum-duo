def run_vqe_curve(R_list, seed=1):
    import math, random
    random.seed(seed)
    out = []
    for R in R_list:
        E = -1.1 + 0.8*(R-0.7)**2 + (random.random()-0.5)*0.01
        out.append({"R": float(R), "E": float(E)})
    return out

def save_energy_plot(points, path):
    import matplotlib.pyplot as plt
    xs = [p["R"] for p in points]
    ys = [p["E"] for p in points]
    i_min = min(range(len(ys)), key=lambda i: ys[i])
    plt.figure()
    plt.plot(xs, ys, marker='o')
    plt.scatter([xs[i_min]],[ys[i_min]], s=60)
    plt.xlabel("Bond length R (Å)")
    plt.ylabel("Energy (Hartree)")
    plt.title("H₂ potential energy curve (placeholder)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)


# MVP: extrai linhas com padrões tipo '123-45: descrição' de um TXT já convertido.
# Para PDF, primeiro converta para texto com pdfminer.six (fora deste script).

import re, argparse, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt", required=True, help="Arquivo texto do MBFT")
    ap.add_argument("--out", required=True, help="CSV de saída")
    args = ap.parse_args()

    pat = re.compile(r"^(\d{3,}-\d{2}):\s*(.+)$")
    out = []
    with open(args.txt, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            m = pat.match(ln.strip())
            if m:
                out.append((m.group(1), m.group(2)))

    with open(args.out, "w", encoding="utf-8") as g:
        g.write("codigo;descricao\n")
        for c,d in out:
            g.write(f"{c};{d}\n")

    print(f"Extraídos {len(out)} códigos para {args.out}")

if __name__ == "__main__":
    main()

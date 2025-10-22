
import argparse, os, sys
import requests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="Pasta com arquivos para enviar ao backend")
    ap.add_argument("--api", default="http://localhost:8000")
    args = ap.parse_args()

    url = args.api.rstrip("/") + "/knowledge/files"
    for fname in os.listdir(args.path):
        fpath = os.path.join(args.path, fname)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                r = requests.post(url, files={"file": (fname, f)})
                print(fname, r.status_code, r.text)

if __name__ == "__main__":
    main()

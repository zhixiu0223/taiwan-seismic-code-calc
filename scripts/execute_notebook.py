"""
自動找出 repo 裡的 .ipynb 並執行,失敗時回傳非 0 讓 CI 判定為失敗。
不寫死檔名/路徑 —— 之後不管 notebook 放在哪個資料夾都能找到。
"""
import sys
import glob

import nbformat
from nbclient import NotebookClient


def find_notebook():
    candidates = [
        p for p in glob.glob("**/*.ipynb", recursive=True)
        if ".git" not in p and ".ipynb_checkpoints" not in p
    ]
    if not candidates:
        print("找不到任何 .ipynb 檔案")
        sys.exit(1)
    return candidates[0]


def main():
    path = find_notebook()
    print(f"Found notebook: {path}")

    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=300, kernel_name="python3")
    client.execute()
    nbformat.write(nb, path)

    print("Executed OK:", path)


if __name__ == "__main__":
    main()

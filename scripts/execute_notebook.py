"""
執行 repo 裡「所有」的 .ipynb,而不是只抓第一個找到的。
任何一份 notebook 的任何一個 cell 出錯(包含 Case-01 那種 assert 檢查失敗),
整個腳本回傳非 0,讓 CI 判定為失敗。
"""
import sys
import glob

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


def find_notebooks():
    candidates = sorted(
        p for p in glob.glob("**/*.ipynb", recursive=True)
        if ".git" not in p and ".ipynb_checkpoints" not in p
    )
    return candidates


def execute_one(path):
    print(f"\n{'='*60}\nExecuting: {path}\n{'='*60}")
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=300, kernel_name="python3")
    try:
        client.execute()
    except CellExecutionError as e:
        print(f"[FAIL] {path} raised an error during execution:\n{e}")
        return False
    nbformat.write(nb, path)
    print(f"[OK] {path}")
    return True


def main():
    notebooks = find_notebooks()
    if not notebooks:
        print("找不到任何 .ipynb 檔案")
        sys.exit(1)

    print(f"共找到 {len(notebooks)} 份 notebook: {notebooks}")

    results = {nb: execute_one(nb) for nb in notebooks}

    print(f"\n{'='*60}\n執行結果總結\n{'='*60}")
    for nb, ok in results.items():
        print(f"  {'[PASS]' if ok else '[FAIL]'} {nb}")

    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()

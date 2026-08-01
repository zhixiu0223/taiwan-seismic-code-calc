"""
迴歸檢查:讀取執行後的 notebook 輸出,把總結表印出的關鍵數字
跟已經核對過的手算結果做比對。

用意:以後如果改了查表值、公式,或不小心動到參數,
這支腳本會在數字跑掉時讓 CI 失敗,而不是悄悄地讓錯誤結果留在 repo 裡。

容許誤差用相對誤差 1e-3(0.1%),浮點運算與四捨五入不會誤觸。

用法:
    python check_key_values.py [notebook路徑]
    若未指定路徑,預設抓 "seismic_design_2story_8col.ipynb"(相容舊用法)。
"""
import re
import sys
import nbformat

DEFAULT_NOTEBOOK_PATH = "seismic_design_2story_8col.ipynb"

# 已核對過的手算結果(見講義「第13~16課」與人工驗算)
EXPECTED = {
    "SDS":   0.550,
    "SD1":   0.450,
    "自然週期 T": 0.3012,
    "Ra":    3.5333,
    "Fu":    2.4631,
    "基底剪力 V": 103.36,
    "2F層剪力 F1": 39.75,
    "屋頂層剪力 F2": 63.60,
    "1F柱端彎矩": 22.61,
    "2F柱端彎矩": 13.91,
    "容許層間位移角": 0.005,
}

REL_TOL = 1e-3


def get_all_stdout(nb):
    text = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                text.append(out.get("text", ""))
            elif out.get("output_type") == "error":
                raise RuntimeError(
                    f"Notebook cell raised an error: {out.get('ename')}: {out.get('evalue')}"
                )
    return "\n".join(text)


def main():
    # 優先吃指令列參數(workflow 用 `python check_key_values.py "$NB"` 呼叫時會傳進來),
    # 沒有給參數時才退回預設檔名,方便本機單獨測試。
    notebook_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_NOTEBOOK_PATH

    nb = nbformat.read(notebook_path, as_version=4)
    stdout = get_all_stdout(nb)

    if not stdout.strip():
        print("找不到任何 stdout 輸出——notebook 是不是還沒被執行過?")
        sys.exit(1)

    failures = []
    for name, expected in EXPECTED.items():
        # 對應總結表格式: "SDS                 0.550 g" 之類
        pattern = re.escape(name) + r"\s+([0-9]+\.?[0-9]*)"
        m = re.search(pattern, stdout)
        if not m:
            failures.append(f"[缺漏] 在輸出裡找不到 '{name}' 這一行")
            continue
        actual = float(m.group(1))
        rel_err = abs(actual - expected) / max(abs(expected), 1e-9)
        if rel_err > REL_TOL:
            failures.append(
                f"[數值偏差] {name}: 預期 {expected}, 實際 {actual} "
                f"(相對誤差 {rel_err:.4%}, 容許 {REL_TOL:.2%})"
            )
        else:
            print(f"[OK] {name}: {actual} (預期 {expected})")

    if failures:
        print("\n".join(failures))
        print(f"\n共 {len(failures)} 項檢查未通過。")
        sys.exit(1)

    print("\n所有關鍵數值均通過迴歸檢查。")


if __name__ == "__main__":
    main()

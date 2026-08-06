"""
tests/test_rc_design_sweep.py

對 rc_design.py 的參數空間掃描測試,跟 notebooks/case08_*.ipynb 完全獨立
——這裡自己造參數網格、自己斷言,不引用任何 notebook 裡的 CASE 字典,
也不會被 notebook 教學案例的參數變動影響。

跑法: pytest tests/test_rc_design_sweep.py -v
"""
import math
import itertools
import pytest

from rc_design import (
    design_rebar, design_doubly_reinforced, design_Tbeam,
    draw_rc_section, draw_Tbeam_section,
)

# ---- 參數網格(涵蓋常見台灣RC設計實務範圍) ----
B_LIST = [20, 25, 30, 40, 50]
H_LIST = [30, 40, 50, 60, 80]
MU_LIST = [30, 80, 150, 250, 400, 600, 900]
FC_LIST = [210, 245, 280, 350]
FY_LIST = [2800, 4200]
COVER_LIST = [3, 4, 5]


@pytest.mark.parametrize(
    "b,h,Mu,fc,fy,cover",
    list(itertools.product(B_LIST, H_LIST, MU_LIST, FC_LIST, FY_LIST, COVER_LIST)),
)
def test_design_rebar_never_crashes_unexpectedly(b, h, Mu, fc, fy, cover):
    """design_rebar() 對任何組合只允許兩種結果: 成功(且強度/拉力控制/排筋間距都合格),
    或乾淨地丟出ValueError——不允許任何其他例外(KeyError/ZeroDivisionError等代表有bug)。"""
    try:
        r = design_rebar(Mu, b, h, fc=fc, fy=fy, cover=cover)
    except ValueError:
        return  # 規範上合理的拒絕, 不是bug
    assert r["phiMn_provided"] >= Mu - 1e-6, "供給強度小於需求, 設計不合格"
    assert r["eps_t"] >= 0.005 - 1e-9, "非拉力控制斷面卻沒被擋下來"
    assert r["clear_spacing"] >= max(r["bar_d"], 2.5) - 1e-6, "排筋間距不足卻沒被擋下來"
    assert not math.isnan(r["As_provided"])


@pytest.mark.parametrize(
    "b,h,Mu,dp,fc,fy",
    list(itertools.product([25, 30, 40, 50], [40, 50, 60, 80],
                            [100, 250, 400, 600, 900, 1300],
                            [5, 6, 8], [210, 280, 350], [2800, 4200])),
)
def test_design_doubly_reinforced_never_crashes(b, h, Mu, dp, fc, fy):
    """雙筋梁設計對任何組合都應該回傳合理dict, 不應該有未預期例外。"""
    r = design_doubly_reinforced(Mu, b, h, dp, fc=fc, fy=fy)
    if r["need_doubly"]:
        assert r["As_total"] > 0 and not math.isnan(r["As_total"])
        assert r["As_prime"] > 0 and not math.isnan(r["As_prime"])


@pytest.mark.parametrize(
    "bw,beff,hf,h,Mu",
    [c for c in itertools.product([20, 25, 30, 40], [60, 90, 120, 150],
                                   [6, 8, 10, 12], [40, 50, 60, 80],
                                   [80, 150, 300, 500, 800, 1200])
     if c[1] > c[0]],
)
def test_design_Tbeam_never_crashes(bw, beff, hf, h, Mu):
    """T形梁設計對任何組合都應該回傳合理dict, 不應該有未預期例外。"""
    r = design_Tbeam(Mu, bw, beff, hf, h)
    if r.get("ok", True) and r.get("mode") == "T-beam":
        assert r["As_total"] > 0 and not math.isnan(r["As_total"])


@pytest.mark.parametrize(
    "b,h,As,bar_d",
    list(itertools.product([20, 25, 30, 50], [30, 50, 80],
                            [3, 7.7, 15, 25, 40], [1.59, 2.22, 2.87, 3.22])),
)
def test_draw_rc_section_never_crashes(b, h, As, bar_d):
    """畫圖函式對極端排筋案例(含刻意排不下的)都應該正常回傳ok=False, 不應該丟例外。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    try:
        _, ok = draw_rc_section(b, h, 4.0, As, bar_d, ax=ax)
        assert isinstance(ok, bool)
    finally:
        plt.close(fig)


def test_case08_1_regression():
    """回歸測試: 對照Case-08.1教學案例的已知答案(跟notebook裡的CASE字典數值一致,
    但這裡是獨立寫死的驗證值, 不是import notebook)。"""
    r = design_rebar(112.5, 30.0, 50.0, cover=4.0)
    assert r["bar_size"] == "#7(D22)"
    assert r["n_bars"] == 2
    assert abs(r["phiMn_provided"] - 119.17) < 0.1

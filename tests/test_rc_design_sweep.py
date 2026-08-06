"""
tests/test_rc_design_sweep.py

對 rc_design.py 的參數空間掃描測試,跟 notebooks/case08_*.ipynb 完全獨立
——這裡自己造參數網格、自己斷言,不引用任何 notebook 裡的 CASE 字典,
也不會被 notebook 教學案例的參數變動影響。

v2 更新:配合 rc_design.py 加入排筋幾何(單層/雙層)後的新回傳結構,
並新增「排筋正確性」測試——不只檢查不崩潰,還要用排筋後的實際 d、
As_provided 重新算一次 Mn,確認真的還滿足 Mu(這是從「robustness
testing」進化到「engineering correctness testing」的關鍵一步)。

跑法: pytest tests/test_rc_design_sweep.py -v
"""
import math
import itertools
import pytest

from rc_design import (
    design_rebar, design_doubly_reinforced, design_Tbeam,
    draw_rc_section, draw_Tbeam_section, compute_bar_layout,
    effective_depth_multilayer,
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
        return
    assert r["phiMn_provided"] >= Mu - 1e-6, "供給強度小於需求, 設計不合格"
    assert r["eps_t"] >= 0.005 - 1e-9, "非拉力控制斷面卻沒被擋下來"
    assert r["clear_spacing"] >= max(r["bar_d"], 2.5) - 1e-6, "排筋間距不足卻沒被擋下來"
    assert not math.isnan(r["As_provided"])
    assert r["layout"]["n_layers"] in (1, 2), "只支援單層/雙層, 不應該出現其他值"
    assert r["n_passes"] in (1, 2), "只做一次修正, 不應該出現其他次數"


@pytest.mark.parametrize(
    "b,h,Mu,dp,fc,fy",
    list(itertools.product([25, 30, 40, 50], [40, 50, 60, 80],
                            [100, 250, 400, 600, 900, 1300],
                            [5, 6, 8], [210, 280, 350], [2800, 4200])),
)
def test_design_doubly_reinforced_never_crashes(b, h, Mu, dp, fc, fy):
    """雙筋梁設計對任何組合都應該回傳合理dict, 不應該有未預期例外。"""
    try:
        r = design_doubly_reinforced(Mu, b, h, dp, fc=fc, fy=fy)
    except ValueError:
        return
    if r["need_doubly"]:
        assert r["As_total"] > 0 and not math.isnan(r["As_total"])
        assert r["As_prime"] > 0 and not math.isnan(r["As_prime"])
        assert r["layout"]["n_layers"] in (1, 2)
        assert r["n_passes"] in (1, 2)


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
    if r.get("ok") and r.get("mode") == "T-beam":
        assert r["As_total"] > 0 and not math.isnan(r["As_total"])
        assert r["layout"]["n_layers"] in (1, 2)


@pytest.mark.parametrize(
    "n_bars,bar_d,b",
    list(itertools.product([2, 3, 4, 5, 6, 8, 10, 13, 20], [1.59, 1.91, 2.22, 2.54, 2.87, 3.22],
                            [20, 25, 30, 40, 50, 90])),
)
def test_draw_rc_section_never_crashes(n_bars, bar_d, b):
    """畫圖函式對極端排筋案例(含刻意排不下的)都應該正常回傳, 不應該丟例外。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    layout = compute_bar_layout(n_bars, bar_d, b, cover_cm=4.0)
    _, ok = draw_rc_section(b, 50.0, 4.0, layout, bar_d)
    assert ok == layout["ok"], "畫圖回傳的ok狀態應該跟layout本身的ok一致"
    plt.close("all")


# ============================================================
# 排筋正確性測試(engineering correctness, 不只是不崩潰)
# 用排筋後的實際d、As_provided重算Mn, 確認真的還滿足Mu
# ============================================================

@pytest.mark.parametrize(
    "b,h,Mu,fc,fy,cover",
    list(itertools.product([20, 25, 30, 40, 50], [30, 50, 80],
                            [50, 150, 300, 500], [210, 280, 350], [2800, 4200], [4])),
)
def test_design_rebar_layout_correctness(b, h, Mu, fc, fy, cover):
    """單筋設計: 用排筋後的實際d、As_provided重算phiMn, 應該仍然>=Mu。"""
    try:
        r = design_rebar(Mu, b, h, fc=fc, fy=fy, cover=cover)
    except ValueError:
        return
    a = r["As_provided"]*fy/(0.85*fc*b)
    Mn_kgfcm = r["As_provided"]*fy*(r["d"]-a/2)
    phiMn_recompute = 0.9*Mn_kgfcm*9.80665e-5
    assert phiMn_recompute >= Mu - 1e-3, (
        f"用排筋後的d={r['d']:.2f}重算, phiMn={phiMn_recompute:.2f} < Mu={Mu}, "
        "排筋幾何修正後的設計不再滿足需求, 這是真正的bug"
    )
    assert abs(phiMn_recompute - r["phiMn_provided"]) < 0.5, (
        "重算的phiMn應該跟函式回傳的phiMn_provided一致(同一個d、同一個As)"
    )


@pytest.mark.parametrize(
    "b,h,Mu,dp,fc,fy",
    list(itertools.product([25, 30, 40], [40, 50, 60],
                            [200, 350, 500, 700, 1000],
                            [5, 6], [210, 280], [4200])),
)
def test_design_doubly_reinforced_layout_correctness(b, h, Mu, dp, fc, fy):
    """雙筋梁: 用排筋後的實際d、As_total、As_prime, 以應變相容法重新
    驗證phiMn是否仍然滿足Mu——這是最嚴謹的閉環檢查。"""
    try:
        r = design_doubly_reinforced(Mu, b, h, dp, fc=fc, fy=fy)
    except ValueError:
        return
    if not r["need_doubly"]:
        return

    Es = 2.0e6
    beta1 = 0.85 if fc <= 280 else max(0.65, 0.85-0.05*(fc-280)/70)
    eps_cu = 0.003
    d = r["d"]
    As_total = r["As_total"]
    As_prime = r["As_prime"]

    def section_force(c):
        a = min(beta1*c, h)
        Cc = 0.85*fc*b*a
        eps_y = fy/Es
        eps_s_prime = eps_cu*(c-dp)/c if c > 0 else 0
        eps_s_prime = max(min(eps_s_prime, eps_y), -eps_y)
        fs_prime = Es*eps_s_prime
        Cs = As_prime*(fs_prime - 0.85*fc if dp <= a else fs_prime)
        eps_s = eps_cu*(c-d)/c if c > 0 else 0
        eps_s = max(min(eps_s, eps_y), -eps_y)
        fs = Es*eps_s
        Ts = As_total*fs
        N = Cc + Cs + Ts
        M = Cc*(d-a/2) + Cs*(d-dp)
        return N, M

    c_lo, c_hi = 0.1, h
    for _ in range(80):
        c_mid = (c_lo+c_hi)/2
        N, _ = section_force(c_mid)
        if N > 0:
            c_hi = c_mid
        else:
            c_lo = c_mid
    _, M_final = section_force((c_lo+c_hi)/2)
    phiMn_strain_compat = 0.9*M_final*9.80665e-5

    tolerance = max(0.03*Mu, 5.0)
    assert phiMn_strain_compat >= Mu - tolerance, (
        f"雙筋排筋後應變相容法驗證: phiMn={phiMn_strain_compat:.2f} < Mu={Mu} "
        f"(容許誤差{tolerance:.1f}), 排筋幾何修正後的設計不再滿足需求"
    )


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))

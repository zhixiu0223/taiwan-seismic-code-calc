"""
rc_design.py — Case-08 系列共用的 RC 配筋設計函式庫

依台灣《混凝土結構設計規範》(ACI 318 中譯本) 強度設計法。
被 Case-08.1(單筋梁)、Case-08.2(雙筋梁+T形梁)、後續 08.3+ 共用,
避免同一個函式在不同 notebook 裡各自定義、容易跑掉不一致。

用法(在 Colab/notebook 裡):
    import os
    if not os.path.exists('rc_design.py'):
        !wget -q https://raw.githubusercontent.com/zhixiu0223/taiwan-seismic-code-calc/main/rc_design.py
    from rc_design import design_rebar, design_doubly_reinforced, design_Tbeam
"""

import math

DEFAULT_BAR_TABLE = {
    "#5(D16)": (1.986, 1.59), "#6(D19)": (2.865, 1.91),
    "#7(D22)": (3.871, 2.22), "#8(D25)": (5.067, 2.54),
    "#9(D29)": (6.469, 2.87), "#10(D32)": (8.143, 3.22),
}


def design_rebar(Mu_kNm, b_cm, h_cm, fc=280.0, fy=4200.0, cover=4.0,
                  stirrup_d=0.95, bar_d_guess=2.5, bar_table=None,
                  phi_target=0.9, beta1=0.85):
    """
    矩形單筋梁撓曲配筋設計(強度設計法)。

    參數
    ----
    Mu_kNm : 設計彎矩需求 (kN-m)
    b_cm, h_cm : 梁寬、梁高 (cm)
    fc, fy : 混凝土抗壓強度、鋼筋降伏強度 (kgf/cm^2, 預設SD420)
    cover : 淨保護層 (cm)
    stirrup_d, bar_d_guess : 箍筋直徑、主筋預估直徑, 用來算有效深度d

    回傳
    ----
    dict, 含需求鋼筋比/As、選筋結果(含排筋間距檢核)、供給強度、使用率

    **不會自動迭代加大斷面或改雙層配筋**——單層排不下就 raise
    ValueError,把決定權留給使用者(見 Case-08.2 說明)。
    """
    if bar_table is None:
        bar_table = DEFAULT_BAR_TABLE

    d = h_cm - cover - stirrup_d - bar_d_guess/2

    Mu_kgfcm = Mu_kNm*1e5/9.80665
    Rn = Mu_kgfcm/(phi_target*b_cm*d**2)
    disc = 1 - 2*Rn/(0.85*fc)
    if disc < 0:
        raise ValueError("斷面太小, 單筋設計無法滿足Mu, 需加大斷面或改用雙筋設計(見Case-08.2)")

    rho_req = (0.85*fc/fy)*(1-math.sqrt(disc))
    rho_min = max(14/fy, 0.8*math.sqrt(fc)/fy)
    rho_used = max(rho_req, rho_min)
    As_req = rho_used*b_cm*d

    a = As_req*fy/(0.85*fc*b_cm)
    c = a/beta1
    eps_t = 0.003*(d-c)/c
    if eps_t < 0.005:
        raise ValueError(f"eps_t={eps_t:.4f}<0.005, 非拉力控制斷面, "
                          "需要用過渡區phi內插或加大斷面")

    best = None
    for name, (Ab, db) in sorted(bar_table.items(), key=lambda kv: kv[1][0]):
        n = max(2, math.ceil(As_req/Ab))
        As_p = n*Ab
        clear_spacing = (b_cm - 2*cover - 2*stirrup_d - n*db)/(n-1) if n > 1 else None
        min_spacing = max(db, 2.5)
        if clear_spacing is None or clear_spacing < min_spacing:
            continue
        over_ratio = As_p/As_req
        if best is None or over_ratio < best['over_ratio']:
            best = dict(bar_size=name, n_bars=n, As_provided=As_p,
                        over_ratio=over_ratio, clear_spacing=clear_spacing, bar_d=db)
    if best is None:
        raise ValueError("所有候選鋼筋尺寸單層都排不下, 需要雙層配筋或加大梁寬"
                          "(這裡不會自動幫你選, 是刻意的設計決定, 留給使用者判斷)")

    a_p = best['As_provided']*fy/(0.85*fc*b_cm)
    Mn_p_kgfcm = best['As_provided']*fy*(d-a_p/2)
    phiMn_p = phi_target*Mn_p_kgfcm*9.80665e-5

    return dict(
        d=d, rho_req=rho_req, rho_min=rho_min, As_req=As_req,
        a=a, c=c, eps_t=eps_t, phi_used=phi_target,
        bar_size=best['bar_size'], n_bars=best['n_bars'], bar_d=best['bar_d'],
        As_provided=best['As_provided'], clear_spacing=best['clear_spacing'],
        phiMn_provided=phiMn_p, Mu_demand=Mu_kNm, utilization=Mu_kNm/phiMn_p,
    )


def design_doubly_reinforced(Mu_kNm, b_cm, h_cm, d_prime_cm, fc=280.0, fy=4200.0,
                               Es=2.0e6, cover=4.0, eps_t_limit=0.005, eps_cu=0.003,
                               phi=0.9, stirrup_d=0.95, bar_d_guess=2.5):
    """雙筋矩形梁設計。d_prime_cm: 壓力鋼筋到受壓邊緣的距離。

    當 Mu 超過單筋斷面在拉力控制極限下的容量時才需要——建議先呼叫
    design_rebar(),如果它 raise ValueError 才改用這個函式。
    """
    beta1 = 0.85 if fc <= 280 else max(0.65, 0.85-0.05*(fc-280)/70)
    d = h_cm - cover - stirrup_d - bar_d_guess/2
    eps_y = fy/Es

    c_max = eps_cu/(eps_cu+eps_t_limit)*d
    a_max = beta1*c_max
    As1 = 0.85*fc*b_cm*a_max/fy
    Mn1_kgfcm = As1*fy*(d-a_max/2)
    Mu1_kNm = phi*Mn1_kgfcm*9.80665e-5

    if Mu_kNm <= Mu1_kNm:
        return dict(need_doubly=False, Mu1=Mu1_kNm, d=d)

    Mu2_kNm = Mu_kNm - Mu1_kNm
    Mu2_kgfcm = Mu2_kNm*1e5/9.80665
    As2 = Mu2_kgfcm/(phi*fy*(d-d_prime_cm))

    eps_s_prime = eps_cu*(c_max-d_prime_cm)/c_max
    compression_yields = eps_s_prime >= eps_y
    if compression_yields:
        As_prime = As2
        fs_prime = fy
    else:
        fs_prime = Es*eps_s_prime
        As_prime = As2*fy/fs_prime

    As_total = As1 + As2
    return dict(need_doubly=True, As_total=As_total, As_prime=As_prime,
                As1=As1, As2=As2, Mu1=Mu1_kNm, Mu2=Mu2_kNm, d=d,
                c_max=c_max, eps_s_prime=eps_s_prime, compression_yields=compression_yields,
                fs_prime=fs_prime)


def design_Tbeam(Mu_kNm, bw_cm, beff_cm, hf_cm, h_cm, fc=280.0, fy=4200.0,
                  cover=4.0, phi=0.9, stirrup_d=0.95, bar_d_guess=2.5, beta1=None):
    """T形梁撓曲設計。先試矩形梁(b=beff), a<=hf則直接採用;
    a>hf才拆成翼板懸挑部分+腹板矩形部分分開算。"""
    if beta1 is None:
        beta1 = 0.85 if fc <= 280 else max(0.65, 0.85-0.05*(fc-280)/70)
    d = h_cm - cover - stirrup_d - bar_d_guess/2
    Mu_kgfcm = Mu_kNm*1e5/9.80665

    Rn = Mu_kgfcm/(phi*beff_cm*d**2)
    disc = 1 - 2*Rn/(0.85*fc)
    if disc < 0:
        return dict(ok=False, reason='超出斷面能力')
    rho_trial = (0.85*fc/fy)*(1-math.sqrt(disc))
    As_trial = rho_trial*beff_cm*d
    a_trial = As_trial*fy/(0.85*fc*beff_cm)

    if a_trial <= hf_cm:
        return dict(ok=True, mode='rectangular', As_total=As_trial, a=a_trial, d=d,
                    bw=bw_cm, beff=beff_cm, hf=hf_cm)

    Asf = 0.85*fc*(beff_cm-bw_cm)*hf_cm/fy
    Mnf_kgfcm = Asf*fy*(d-hf_cm/2)
    Muf_kNm = phi*Mnf_kgfcm*9.80665e-5

    Muw_kNm = Mu_kNm - Muf_kNm
    Muw_kgfcm = Muw_kNm*1e5/9.80665
    Rn_w = Muw_kgfcm/(phi*bw_cm*d**2)
    disc_w = 1 - 2*Rn_w/(0.85*fc)
    if disc_w < 0:
        return dict(ok=False, reason='腹板部分超出單筋能力, 需要雙筋T形梁(這裡未涵蓋)')
    rho_w = (0.85*fc/fy)*(1-math.sqrt(disc_w))
    Asw = rho_w*bw_cm*d
    a_w = Asw*fy/(0.85*fc*bw_cm)

    As_total = Asf + Asw
    return dict(ok=True, mode='T-beam', As_total=As_total, Asf=Asf, Asw=Asw,
                a_w=a_w, hf=hf_cm, d=d, bw=bw_cm, beff=beff_cm)


def draw_rc_section(b_cm, h_cm, cover_cm, As_total_cm2, bar_diameter_cm,
                      As_prime_cm2=None, d_prime_cm=None, title="RC Section", ax=None):
    """矩形斷面配筋圖(單筋或雙筋)。需要 matplotlib.pyplot as plt 已存在於呼叫端命名空間。
    bar_diameter_cm 用公分, 跟 design_rebar() 回傳的 r['bar_d'] 單位一致。"""
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 6))

    ax.add_patch(plt.Rectangle((0, 0), b_cm, h_cm, facecolor='#e8e8e8',
                                 edgecolor='black', linewidth=2))
    ax.add_patch(plt.Rectangle((cover_cm, cover_cm), b_cm-2*cover_cm, h_cm-2*cover_cm,
                                 facecolor='none', edgecolor='#888888', linewidth=1.2, linestyle='--'))

    bar_area = math.pi*(bar_diameter_cm/2)**2
    n_bars = max(2, round(As_total_cm2/bar_area))
    y_bot = cover_cm + 0.95 + bar_diameter_cm/2
    clear_width = b_cm - 2*(cover_cm+0.95) - bar_diameter_cm
    xs = [b_cm/2] if n_bars == 1 else \
        [cover_cm+0.95+bar_diameter_cm/2 + i*clear_width/(n_bars-1) for i in range(n_bars)]
    for x in xs:
        ax.add_patch(plt.Circle((x, y_bot), bar_diameter_cm/2, facecolor='#333333',
                                  edgecolor='black', zorder=5))

    if As_prime_cm2 and d_prime_cm:
        n_bars_top = max(2, round(As_prime_cm2/bar_area))
        y_top = h_cm - d_prime_cm
        xs_top = [b_cm/2] if n_bars_top == 1 else \
            [cover_cm+0.95+bar_diameter_cm/2 + i*clear_width/(n_bars_top-1) for i in range(n_bars_top)]
        for x in xs_top:
            ax.add_patch(plt.Circle((x, y_top), bar_diameter_cm/2, facecolor='#c00000',
                                      edgecolor='black', zorder=5))
        ax.text(b_cm+2, y_top, f"{n_bars_top}-D{bar_diameter_cm*10:.0f}\n(compression)",
                fontsize=8, va='center', color='#c00000')

    available_width = b_cm - 2*(cover_cm+0.95)
    clear_spacing = (available_width - n_bars*bar_diameter_cm)/(n_bars-1) if n_bars > 1 else available_width
    spacing_ok = clear_spacing >= max(2.5, bar_diameter_cm)
    status_color = 'green' if spacing_ok else 'red'
    status_text = 'OK' if spacing_ok else 'FAIL: bars do not fit in single layer'

    ax.text(b_cm+2, y_bot, f"{n_bars}-D{bar_diameter_cm*10:.0f}\n(tension)",
            fontsize=8, va='center', color='#333333')
    ax.text(b_cm/2, -3, f"b={b_cm:.0f}cm", ha='center', fontsize=9)
    ax.text(-3, h_cm/2, f"h={h_cm:.0f}cm", va='center', rotation=90, fontsize=9)
    ax.text(b_cm/2, h_cm+2, f"clear spacing={clear_spacing:.2f}cm [{status_text}]",
            ha='center', fontsize=7.5, color=status_color)

    ax.set_xlim(-8, b_cm+18)
    ax.set_ylim(-6, h_cm+6)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=10)
    ax.axis('off')
    return ax, spacing_ok


def draw_Tbeam_section(bw_cm, beff_cm, hf_cm, h_cm, cover_cm, As_total_cm2,
                         bar_diameter_cm, title="T-beam Section", ax=None):
    """T形斷面配筋圖, 直接吃 design_Tbeam() 輸出的 As_total。"""
    import matplotlib.pyplot as plt
    import matplotlib.path as mpath
    from matplotlib.patches import PathPatch
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))

    web_x0 = (beff_cm-bw_cm)/2
    verts = [(web_x0, 0), (web_x0+bw_cm, 0), (web_x0+bw_cm, h_cm-hf_cm), (beff_cm, h_cm-hf_cm),
              (beff_cm, h_cm), (0, h_cm), (0, h_cm-hf_cm), (web_x0, h_cm-hf_cm), (web_x0, 0)]
    ax.add_patch(PathPatch(mpath.Path(verts), facecolor='#e8e8e8', edgecolor='black', linewidth=2))

    bar_area = math.pi*(bar_diameter_cm/2)**2
    n_bars = max(2, round(As_total_cm2/bar_area))
    y_bot = cover_cm + 0.95 + bar_diameter_cm/2
    available_width = bw_cm - 2*(cover_cm+0.95)
    xs = [web_x0+bw_cm/2] if n_bars == 1 else \
        [web_x0+cover_cm+0.95+bar_diameter_cm/2 + i*(available_width-bar_diameter_cm)/(n_bars-1)
         for i in range(n_bars)]
    for x in xs:
        ax.add_patch(plt.Circle((x, y_bot), bar_diameter_cm/2, facecolor='#333333',
                                  edgecolor='black', zorder=5))

    clear_spacing = (available_width - n_bars*bar_diameter_cm)/(n_bars-1) if n_bars > 1 else available_width
    spacing_ok = clear_spacing >= max(2.5, bar_diameter_cm)
    status_color = 'green' if spacing_ok else 'red'
    status_text = 'OK' if spacing_ok else f'FAIL: {n_bars} bars do not fit in bw={bw_cm:.0f}cm single layer'

    ax.text(beff_cm+3, y_bot, f"{n_bars}-D{bar_diameter_cm*10:.0f}\n(tension)", fontsize=8, va='center')
    ax.text(beff_cm/2, -3, f"beff={beff_cm:.0f}cm", ha='center', fontsize=9)
    ax.text(web_x0+bw_cm/2, h_cm-hf_cm-3, f"bw={bw_cm:.0f}cm", ha='center', fontsize=8, color='gray')
    ax.text(-3, h_cm/2, f"h={h_cm:.0f}cm", va='center', rotation=90, fontsize=9)
    ax.text(beff_cm/2, h_cm+2, f"clear spacing={clear_spacing:.2f}cm [{status_text}]",
            ha='center', fontsize=7.5, color=status_color)

    ax.set_xlim(-8, beff_cm+22)
    ax.set_ylim(-6, h_cm+6)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=10)
    ax.axis('off')
    return ax, spacing_ok


if __name__ == "__main__":
    # 自我測試: 跑一次08.1的標準案例, 確認模組本身沒問題
    r = design_rebar(112.5, 30.0, 50.0, cover=4.0)
    assert abs(r['phiMn_provided'] - 119.17) < 0.1, "自我測試失敗, 數字跟已知案例對不上"
    print("rc_design.py 自我測試通過")

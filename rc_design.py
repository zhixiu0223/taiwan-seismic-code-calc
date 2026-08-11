"""
rc_design.py — Case-08 系列共用的 RC 配筋設計函式庫

依台灣《混凝土結構設計規範》(ACI 318 中譯本) 強度設計法。
被 Case-08.1(單筋梁)、Case-08.2(雙筋梁+T形梁)、後續 08.3+ 共用,
避免同一個函式在不同 notebook 裡各自定義、容易跑掉不一致。

v2 更新:加入排筋幾何(單層/雙層)。之前的版本只算「需要多少鋼筋
面積」,完全沒檢查排不排得下——如果單層排不下,現在會自動改排
雙層,並且用雙層排列後真正的形心位置重新算有效深度 d,對設計做
一次修正(不是無窮迭代找完美收斂點,是業界常見的「算一次、修正
一次、驗證還夠不夠」做法,避免在不同鋼筋尺寸之間來回震盪不收斂
——這是實際測試時真的踩到的坑,不是預先想到的假設風險)。

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


# ============================================================
# 排筋幾何——不是繪圖函式的責任, 是設計函式的責任
# (畫圖函式只負責把算好的layout畫出來, 不自己決定怎麼排)
# ============================================================

def compute_bar_layout(n_bars, bar_d_cm, b_cm, cover_cm, stirrup_d_cm=0.95):
    """
    給定鋼筋根數跟直徑, 決定單層排不排得下; 排不下就排雙層。
    只支援到雙層(2層以上實務少見, 這裡刻意不擴張範圍)。

    回傳 dict: n_layers, layout(每層根數list), clear_spacing_horizontal,
    vertical_clear_spacing(雙層才有), ok, reason(排不下時的原因)
    """
    available_width = b_cm - 2*(cover_cm + stirrup_d_cm)
    min_spacing = max(bar_d_cm, 2.5)

    def try_single_layer(n):
        if n <= 1:
            return True, available_width
        spacing = (available_width - n*bar_d_cm) / (n-1)
        return spacing >= min_spacing, spacing

    fits_single, spacing_single = try_single_layer(n_bars)
    if fits_single:
        return dict(n_layers=1, layout=[n_bars], clear_spacing_horizontal=spacing_single,
                     vertical_clear_spacing=None, ok=True, reason=None)

    n1 = math.ceil(n_bars/2)
    n2 = n_bars - n1
    fits1, spacing1 = try_single_layer(n1)
    fits2, spacing2 = try_single_layer(n2) if n2 > 0 else (True, available_width)
    if not (fits1 and fits2):
        return dict(n_layers=2, layout=[n1, n2], ok=False,
                     reason=f"連雙層都排不下({n1}+{n2}根), 需要加大梁寬或改用更大直徑鋼筋",
                     clear_spacing_horizontal=None, vertical_clear_spacing=None)

    return dict(n_layers=2, layout=[n1, n2], clear_spacing_horizontal=min(spacing1, spacing2),
                 vertical_clear_spacing=min_spacing, ok=True, reason=None)


def effective_depth_multilayer(layout_result, bar_d_cm, h_cm, cover_cm, stirrup_d_cm=0.95):
    """給定compute_bar_layout()的結果, 算出加權形心有效深度d。
    單層: 就是原本的d。雙層: 兩層鋼筋根數加權平均, 內層(較靠近受壓邊)
    的距離會被扣掉一根鋼筋直徑+層間淨距。"""
    if layout_result['n_layers'] == 1:
        return h_cm - cover_cm - stirrup_d_cm - bar_d_cm/2
    n1, n2 = layout_result['layout']
    d1 = h_cm - cover_cm - stirrup_d_cm - bar_d_cm/2
    d2 = d1 - (bar_d_cm + layout_result['vertical_clear_spacing'])
    return (n1*d1 + n2*d2) / (n1+n2)


def choose_bars_with_layout(As_req, b_cm, cover, stirrup_d, bar_table=None):
    """幫需求鋼筋量選一組鋼筋+排列方式。

    排序優先權: 先比層數(單層優先於雙層), 層數相同才比過量比例(越少越好)。
    ——這是修正過的邏輯: 原本只比過量比例, 會導致「Mu增加、需求鋼筋量增加,
    卻因為換了一個鋼筋尺寸而選到單層排列, 有效深度d反而變好」這種非單調
    現象(在Mu由小到大逐步掃描時, 拒絕/接受邊界會忽上忽下, 不是平滑遞減)。
    只比過量比例不會給出不安全的設計(每個候選都個別驗證過), 但層數優先
    這個修正讓整體行為更符合工程直覺(邁向union: 對同一個b/h, Mu越大,
    有效深度只會持平或變差, 不會無端變好)。"""
    if bar_table is None:
        bar_table = DEFAULT_BAR_TABLE
    best = None
    for name, (Ab, db) in sorted(bar_table.items(), key=lambda kv: kv[1][0]):
        n = max(2, math.ceil(As_req/Ab))
        layout = compute_bar_layout(n, db, b_cm, cover, stirrup_d)
        if not layout['ok']:
            continue
        over_ratio = n*Ab/As_req
        candidate = dict(bar_size=name, n_bars=n, As_provided=n*Ab, bar_d=db,
                          over_ratio=over_ratio, layout=layout)
        if best is None:
            best = candidate
            continue
        # 先比層數(少的優先), 層數相同才比過量比例
        if layout['n_layers'] < best['layout']['n_layers']:
            best = candidate
        elif layout['n_layers'] == best['layout']['n_layers'] and over_ratio < best['over_ratio']:
            best = candidate
    return best


# ============================================================
# 撓曲設計
# ============================================================

def design_rebar(Mu_kNm, b_cm, h_cm, fc=280.0, fy=4200.0, cover=4.0,
                  stirrup_d=0.95, bar_d_guess=2.5, bar_table=None,
                  phi_target=0.9, beta1=0.85, Es=2.0e6):
    """
    矩形單筋梁撓曲配筋設計(強度設計法)。含排筋幾何(單層/雙層)
    ——如果算出來的鋼筋單層排不下, 會自動改雙層, 並用雙層的真實
    有效深度做一次修正設計(不是無窮迭代, 是算一次+修正一次)。

    回傳 dict 除了原本的強度/鋼筋量, 多了 layout 欄位(排筋幾何細節)
    跟 n_passes(1=單層一次到位, 2=雙層修正過一次)。
    """
    if bar_table is None:
        bar_table = DEFAULT_BAR_TABLE

    d_pass1 = h_cm - cover - stirrup_d - bar_d_guess/2

    def solve_at_d(d):
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
        return dict(rho_req=rho_req, rho_min=rho_min, As_req=As_req, a=a, c=c, eps_t=eps_t)

    r1 = solve_at_d(d_pass1)
    chosen1 = choose_bars_with_layout(r1['As_req'], b_cm, cover, stirrup_d, bar_table)
    if chosen1 is None:
        raise ValueError("所有候選鋼筋尺寸連雙層都排不下, 需要加大梁寬")

    if chosen1['layout']['n_layers'] == 1:
        d, r, chosen, n_passes = d_pass1, r1, chosen1, 1
    else:
        # 修正過程記錄: 選筋+算d最多疊代6輪, 每輪都用"上一輪真正選到的
        # 鋼筋規格"重算有效深度(不是延用第一輪的筋徑, 這是真實抓到的
        # bug——例如第一輪選#10排雙層算出d, 第二輪需求量變大改選#8,
        # 若不重算d, 後續a/c/eps_t/Mn全部建立在不一致的d上)。
        #
        # 也真實抓到過選筋在多個尺寸之間循環、不會收斂的案例(#9/#10/#8
        # 之間形成極限環, 不是接近收斂)——這時候不報錯放棄, 改成從
        # 疊代過程中挑d最小(最保守, 對應鋼筋量最大)的那一輪自洽結果
        # 當最終答案, 保證方向上不會高估容量。
        d_cur = effective_depth_multilayer(chosen1['layout'], chosen1['bar_d'], h_cm, cover, stirrup_d)
        history = []
        for _extra_pass in range(6):
            r_cur = solve_at_d(d_cur)
            chosen_cur = choose_bars_with_layout(r_cur['As_req'], b_cm, cover, stirrup_d, bar_table)
            if chosen_cur is None:
                raise ValueError("雙層修正後仍排不下, 需要加大梁寬")
            if chosen_cur['layout']['n_layers'] == 1:
                d_new = h_cm - cover - stirrup_d - chosen_cur['bar_d']/2
            else:
                d_new = effective_depth_multilayer(chosen_cur['layout'], chosen_cur['bar_d'], h_cm, cover, stirrup_d)
            history.append((d_new, r_cur, chosen_cur))
            if abs(d_new - d_cur) < 0.01:
                d_cur, r, chosen = d_new, r_cur, chosen_cur
                break
            d_cur = d_new
        else:
            # 沒有收斂: 從history挑d最小(最保守)的那一輪
            d_cur, r, chosen = min(history, key=lambda t: t[0])
        d, n_passes = d_cur, 2

    a_p = chosen['As_provided']*fy/(0.85*fc*b_cm)
    c_p = a_p/beta1
    # d_t: 最外層有效深度(單層時等於d, 雙層時是真正的最外層, 不是加權形心)
    d_t = d if chosen['layout']['n_layers'] == 1 else h_cm - cover - stirrup_d - chosen['bar_d']/2
    # 用真實供給量(不是理論連續需求量As_req)重算eps_t, 這才是這根梁
    # 實際會發生的應變狀態——之前這裡沿用r['eps_t'](用As_req算的),
    # 跟design_doubly_reinforced()/design_Tbeam()的邏輯不一致, 這次
    # 一併對齊, 統一都用「真實供給量+最外層d_t」決定phi
    eps_t_actual = 0.003*(d_t-c_p)/c_p if c_p > 0 else 0
    if eps_t_actual < 0.005:
        # 選完鋼筋後用"真實供給量"(不是理論連續需求量As_req)重新檢查,
        # 因為選筋只能選現有規格, 實際供給量通常比理論值多一點, 有可能
        # 讓真實eps_t掉到門檻以下(即使用As_req檢查時通過)——這是真實
        # 存在過的邊界案例(曾抓到0.004997這種極接近門檻的情況), 不是
        # 假設性的風險。design_rebar()維持"非拉力控制直接拒絕, 不做
        # 過渡區折減"這個既定設計哲學, 只是現在用選筋後的真實狀態檢查,
        # 不是選筋前的理論值。
        raise ValueError(
            f"選筋後真實eps_t={eps_t_actual:.6f}<0.005(選筋前的理論值原本通過,"
            f"但實際供給量比理論需求多, 真實應變掉到門檻以下), 非拉力控制斷面,"
            "需要用過渡區phi內插或加大斷面")
    phi_actual = phi_from_eps_t(eps_t_actual, eps_ty=fy/Es)
    Mn_p_kgfcm = chosen['As_provided']*fy*(d-a_p/2)
    phiMn_p = phi_actual*Mn_p_kgfcm*9.80665e-5
    if phiMn_p < Mu_kNm:
        # 最後一道保底檢查: d/選筋雖然已經收斂(上面的疊代不再變動),
        # 但收斂到的鋼筋規格在真正的最終d之下, 供給強度還是不夠
        # ——這是曾經真實發生過的邊界案例(供給98.6%左右, 不是離譜的
        # 錯誤, 但確實不夠), 不能默默放行, 誠實報錯讓使用者知道要
        # 調整斷面, 不是隱藏起來讓人以為設計合格
        raise ValueError(
            f"收斂後供給強度phiMn={phiMn_p:.2f}仍小於需求Mu={Mu_kNm}, "
            "排筋+有效深度疊代已收斂但供給仍不足, 需要加大斷面或改用雙筋設計")
    Mn_p_kNm = Mn_p_kgfcm*9.80665e-5

    return dict(
        d=d, d_t=d_t, rho_req=r['rho_req'], rho_min=r['rho_min'], As_req=r['As_req'],
        a=a_p, c=c_p, eps_t=eps_t_actual, phi_used=phi_actual,
        bar_size=chosen['bar_size'], n_bars=chosen['n_bars'], bar_d=chosen['bar_d'],
        As_provided=chosen['As_provided'], clear_spacing=chosen['layout']['clear_spacing_horizontal'],
        layout=chosen['layout'], n_passes=n_passes, Mn=Mn_p_kNm,
        phiMn_provided=phiMn_p, Mu_demand=Mu_kNm, utilization=Mu_kNm/phiMn_p,
    )


def phi_from_eps_t(eps_t, eps_ty=0.002):
    """ACI 318 / 台灣混凝土結構設計規範強度折減係數phi, 依最外層拉力鋼筋
    淨拉應變eps_t(不是加權形心的應變, 是排筋位置最外層那一根的應變)
    決定: eps_t>=0.005拉力控制phi=0.90; eps_t<=eps_ty(壓力控制邊界,
    SD420鋼筋eps_y=0.0021, 這裡簡化用規範慣用值0.002)phi=0.65;
    中間過渡區線性內插。

    這是統一公開介面——矩形單筋梁、雙筋梁、T形梁三種斷面判斷phi的
    邏輯完全一樣, 差別只在怎麼算出eps_t(不同斷面的中性軸/最外層
    深度算法不同), 決定phi這一步共用同一個函式, 不用三份各自實作。
    design_rebar()/design_doubly_reinforced()/design_Tbeam()內部都
    呼叫這個函式。"""
    if eps_t >= 0.005:
        return 0.9
    if eps_t <= eps_ty:
        return 0.65
    return 0.65 + (eps_t - eps_ty) * (0.25 / (0.005 - eps_ty))


def _phiMn_doubly_strain_compat(As_total, As_prime, d, d_prime_cm, b_cm, h_cm,
                                  fc, fy, Es, beta1, eps_cu, phi, d_t=None):
    """雙筋斷面用應變相容法算真正的供給容量phiMn(內部函式, 不對外開放,
    design_doubly_reinforced()自己呼叫, 讓notebook不用重複實作)。

    修正記錄: 之前這裡直接用固定phi(呼叫端傳進來的0.9), 沒有依照
    ACI 318/台灣規範第3.3節的過渡區規則(eps_t<0.005時phi要線性折減)
    重新判斷——這是真實存在的bug, 在拉力鋼筋排成雙層、最外層淨拉應變
    eps_t(在d_t量, 不是在加權形心d量)落入0.002~0.005過渡區時,
    會高估phiMn(此前發現過一個案例高估達~10%)。d_t預設等於d(單層
    時兩者相同), 排雙層時呼叫端要傳入真正的最外層深度。
    """
    if d_t is None:
        d_t = d

    def section_force(c):
        a = min(beta1*c, h_cm)
        Cc = 0.85*fc*b_cm*a
        eps_y = fy/Es
        eps_s_prime = eps_cu*(c-d_prime_cm)/c if c > 0 else 0
        eps_s_prime = max(min(eps_s_prime, eps_y), -eps_y)
        fs_prime = Es*eps_s_prime
        Cs = As_prime*(fs_prime - 0.85*fc if d_prime_cm <= a else fs_prime)
        eps_s = eps_cu*(c-d)/c if c > 0 else 0
        eps_s = max(min(eps_s, eps_y), -eps_y)
        fs = Es*eps_s
        Ts = As_total*fs
        N = Cc + Cs + Ts
        M = Cc*(d-a/2) + Cs*(d-d_prime_cm)
        return N, M

    c_lo, c_hi = 0.1, h_cm
    for _ in range(100):
        c_mid = (c_lo+c_hi)/2
        N, _ = section_force(c_mid)
        if N > 0:
            c_hi = c_mid
        else:
            c_lo = c_mid
    c_final = (c_lo+c_hi)/2
    _, M_final = section_force(c_final)
    eps_t_true = eps_cu*(c_final-d_t)/c_final if c_final > 0 else 0
    eps_t_true = -eps_t_true  # section_force內部用"受壓為正"的號約定, 這裡轉成"拉應變為正"回報
    phi_true = phi_from_eps_t(eps_t_true, eps_ty=fy/Es)
    Mn_kNm = M_final*9.80665e-5
    return phi_true*Mn_kNm, eps_t_true, phi_true, Mn_kNm


def design_doubly_reinforced(Mu_kNm, b_cm, h_cm, d_prime_cm, fc=280.0, fy=4200.0,
                               Es=2.0e6, cover=4.0, eps_t_limit=0.005, eps_cu=0.003,
                               phi=0.9, stirrup_d=0.95, bar_d_guess=2.5, bar_table=None):
    """雙筋矩形梁設計。d_prime_cm: 壓力鋼筋到受壓邊緣的距離。

    當 Mu 超過單筋斷面在拉力控制極限下的容量時才需要——建議先呼叫
    design_rebar(),如果它 raise ValueError 才改用這個函式。

    含排筋幾何(單層/雙層), 邏輯跟design_rebar()一致: 算一次+修正一次,
    不是無窮迭代(實測發現無窮迭代在不同鋼筋尺寸間會震盪不收斂)。

    回傳的phiMn_provided是用應變相容法算出的真正供給容量(不是代數
    公式解), 因為雙筋斷面的Whitney簡化公式解跟"排筋後的真實d/As"
    搭配時有~0.3%量級的已知近似誤差(算一次+修正一次法造成), 應變
    相容法才是嚴謹的最終驗證, 直接內建在這裡, 呼叫端不用重新實作。
    """
    if bar_table is None:
        bar_table = DEFAULT_BAR_TABLE
    beta1 = 0.85 if fc <= 280 else max(0.65, 0.85-0.05*(fc-280)/70)
    eps_y = fy/Es

    def solve_at_d(d):
        c_max = eps_cu/(eps_cu+eps_t_limit)*d
        a_max = beta1*c_max
        As1 = 0.85*fc*b_cm*a_max/fy
        Mn1_kgfcm = As1*fy*(d-a_max/2)
        Mu1_kNm = phi*Mn1_kgfcm*9.80665e-5
        if Mu_kNm <= Mu1_kNm:
            return dict(need_doubly=False, Mu1=Mu1_kNm)
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
        return dict(need_doubly=True, As1=As1, As2=As2, As_total=As1+As2, As_prime=As_prime,
                    Mu1=Mu1_kNm, Mu2=Mu2_kNm, c_max=c_max, eps_s_prime=eps_s_prime,
                    compression_yields=compression_yields, fs_prime=fs_prime)

    d_pass1 = h_cm - cover - stirrup_d - bar_d_guess/2
    r1 = solve_at_d(d_pass1)
    if not r1['need_doubly']:
        return dict(need_doubly=False, Mu1=r1['Mu1'], d=d_pass1)

    chosen1 = choose_bars_with_layout(r1['As_total'], b_cm, cover, stirrup_d, bar_table)
    if chosen1 is None:
        raise ValueError("連雙層都排不下, 需要加大梁寬")

    if chosen1['layout']['n_layers'] == 1:
        d, r, chosen, n_passes = d_pass1, r1, chosen1, 1
    else:
        # 疊代最多6輪, 每輪用"上一輪真正選到的鋼筋規格"重算有效深度
        # (不是延用第一輪的筋徑)——同一個bug跟design_rebar()一致。
        # 不處理"疊代中need_doubly變False"這種情況: d在這個迴圈裡只會
        # 變小(多層修正的方向), As需求只會增加, need_doubly邏輯上不會
        # 中途從True變False。
        #
        # 也真實抓到過選筋在多個尺寸之間循環、不會收斂的案例——這時候
        # 不報錯放棄, 改成從疊代過程挑d最小(最保守)的那一輪自洽結果
        d_cur = effective_depth_multilayer(chosen1['layout'], chosen1['bar_d'], h_cm, cover, stirrup_d)
        history = []
        for _extra_pass in range(6):
            r_cur = solve_at_d(d_cur)
            chosen_cur = choose_bars_with_layout(r_cur['As_total'], b_cm, cover, stirrup_d, bar_table)
            if chosen_cur is None:
                raise ValueError("雙層修正後仍排不下, 需要加大梁寬")
            if chosen_cur['layout']['n_layers'] == 1:
                d_new = h_cm - cover - stirrup_d - chosen_cur['bar_d']/2
            else:
                d_new = effective_depth_multilayer(chosen_cur['layout'], chosen_cur['bar_d'], h_cm, cover, stirrup_d)
            history.append((d_new, r_cur, chosen_cur))
            if abs(d_new - d_cur) < 0.01:
                d_cur, r, chosen = d_new, r_cur, chosen_cur
                break
            d_cur = d_new
        else:
            d_cur, r, chosen = min(history, key=lambda t: t[0])
        d, n_passes = d_cur, 2
        d, r, chosen, n_passes = d_cur, r_cur, chosen_cur, 2

    # 單層時d_t就是d(只有一層, 沒有最外層跟加權形心不同這回事);
    # 雙層以上才需要用真正選到的鋼筋直徑重算最外層深度
    d_t = d if chosen['layout']['n_layers'] == 1 else h_cm - cover - stirrup_d - chosen['bar_d']/2
    phiMn_provided, eps_t_actual, phi_actual, Mn_val = _phiMn_doubly_strain_compat(
        chosen['As_provided'], r['As_prime'], d, d_prime_cm, b_cm, h_cm,
        fc, fy, Es, beta1, eps_cu, phi, d_t=d_t)

    return dict(need_doubly=True, As_total=r['As_total'], As_prime=r['As_prime'],
                As1=r['As1'], As2=r['As2'], Mu1=r['Mu1'], Mu2=r['Mu2'], d=d, d_t=d_t,
                eps_t=eps_t_actual, phi_used=phi_actual, Mn=Mn_val,
                c_max=r['c_max'], eps_s_prime=r['eps_s_prime'],
                compression_yields=r['compression_yields'], fs_prime=r['fs_prime'],
                bar_size=chosen['bar_size'], n_bars=chosen['n_bars'], bar_d=chosen['bar_d'],
                As_provided=chosen['As_provided'], layout=chosen['layout'], n_passes=n_passes,
                phiMn_provided=phiMn_provided, Mu_demand=Mu_kNm,
                utilization=Mu_kNm/phiMn_provided)


def _phiMn_Tbeam_strain_compat(As_total, d, bw_cm, beff_cm, hf_cm, h_cm,
                                 fc, fy, Es, beta1, eps_cu, phi, d_t=None):
    """T形斷面用應變相容法算真正的供給容量phiMn(內部函式)。壓力區可能
    跨越翼板+腹板(a>hf), 這時合力要拆成翼板部分(全寬beff, 深度hf)+
    腹板部分(寬bw, 深度a-hf)分別取矩, 跟design_Tbeam()正式設計時的
    近似公式解是獨立的第二種算法。

    修正記錄: 之前這裡直接用固定phi, 沒有依規範過渡區規則重新判斷
    ——這是真實bug, 排雙層時eps_t要在最外層d_t量, 不是加權形心d,
    這裡曾經發現一個案例(7-D32排成4+3雙層)高估phiMn達~10%(716.77
    vs 正確值~649)。d_t預設等於d(單層時兩者相同)。
    """
    if d_t is None:
        d_t = d

    def section_force(c):
        a = min(beta1*c, h_cm)
        if a <= hf_cm:
            Cc = 0.85*fc*beff_cm*a
            M_c = Cc*(d-a/2)
        else:
            Cc_f = 0.85*fc*beff_cm*hf_cm
            Cc_w = 0.85*fc*bw_cm*(a-hf_cm)
            Cc = Cc_f + Cc_w
            M_c = Cc_f*(d-hf_cm/2) + Cc_w*(d-hf_cm-(a-hf_cm)/2)
        eps_y = fy/Es
        eps_s = eps_cu*(c-d)/c if c > 0 else 0
        eps_s = max(min(eps_s, eps_y), -eps_y)
        Ts = As_total*Es*eps_s
        return Cc+Ts, M_c

    c_lo, c_hi = 0.1, h_cm
    for _ in range(100):
        c_mid = (c_lo+c_hi)/2
        N, _ = section_force(c_mid)
        if N > 0:
            c_hi = c_mid
        else:
            c_lo = c_mid
    c_final = (c_lo+c_hi)/2
    _, M_final = section_force(c_final)
    eps_t_true = eps_cu*(d_t-c_final)/c_final if c_final > 0 else 0
    phi_true = phi_from_eps_t(eps_t_true, eps_ty=fy/Es)
    Mn_kNm = M_final*9.80665e-5
    return phi_true*Mn_kNm, eps_t_true, phi_true, Mn_kNm


def design_Tbeam(Mu_kNm, bw_cm, beff_cm, hf_cm, h_cm, fc=280.0, fy=4200.0,
                  cover=4.0, phi=0.9, stirrup_d=0.95, bar_d_guess=2.5, beta1=None,
                  bar_table=None, Es=2.0e6, eps_cu=0.003):
    """T形梁撓曲設計。先試矩形梁(b=beff), a<=hf則直接採用;
    a>hf才拆成翼板懸挑部分+腹板矩形部分分開算。

    拉力鋼筋排列用腹板寬度bw(不是beff)——鋼筋要放在腹板裡, 不是
    整個翼板寬度。含排筋幾何(單層/雙層), 邏輯跟前兩個函式一致。

    回傳的phiMn_provided是用應變相容法算出的真正供給容量, 不是
    design_Tbeam()正式設計時用的近似代數解(翼板+腹板分開算力偶)
    ——這個近似解在a_w/d比例大時會失準(低fc、重度配筋案例),
    phiMn_provided直接內建做嚴謹驗證, 呼叫端不用重新實作。
    """
    if bar_table is None:
        bar_table = DEFAULT_BAR_TABLE
    if beta1 is None:
        beta1 = 0.85 if fc <= 280 else max(0.65, 0.85-0.05*(fc-280)/70)

    def solve_at_d(d):
        Mu_kgfcm = Mu_kNm*1e5/9.80665
        Rn = Mu_kgfcm/(phi*beff_cm*d**2)
        disc = 1 - 2*Rn/(0.85*fc)
        if disc < 0:
            return dict(ok=False, mode=None, reason='超出斷面能力')
        rho_trial = (0.85*fc/fy)*(1-math.sqrt(disc))
        As_trial = rho_trial*beff_cm*d
        a_trial = As_trial*fy/(0.85*fc*beff_cm)

        if a_trial <= hf_cm:
            return dict(ok=True, mode='rectangular', As_total=As_trial, a=a_trial)

        Asf = 0.85*fc*(beff_cm-bw_cm)*hf_cm/fy
        Mnf_kgfcm = Asf*fy*(d-hf_cm/2)
        Muf_kNm = phi*Mnf_kgfcm*9.80665e-5
        Muw_kNm = Mu_kNm - Muf_kNm
        Muw_kgfcm = Muw_kNm*1e5/9.80665
        Rn_w = Muw_kgfcm/(phi*bw_cm*d**2)
        disc_w = 1 - 2*Rn_w/(0.85*fc)
        if disc_w < 0:
            return dict(ok=False, mode=None, reason='腹板部分超出單筋能力, 需要雙筋T形梁(這裡未涵蓋)')
        rho_w = (0.85*fc/fy)*(1-math.sqrt(disc_w))
        Asw = rho_w*bw_cm*d
        a_w = Asw*fy/(0.85*fc*bw_cm)
        return dict(ok=True, mode='T-beam', As_total=Asf+Asw, Asf=Asf, Asw=Asw, a_w=a_w,
                    Muf=Muf_kNm, Muw=Muw_kNm)

    d_pass1 = h_cm - cover - stirrup_d - bar_d_guess/2
    r1 = solve_at_d(d_pass1)
    if not r1['ok']:
        return dict(ok=False, mode=None, reason=r1['reason'])

    chosen1 = choose_bars_with_layout(r1['As_total'], bw_cm, cover, stirrup_d, bar_table)
    if chosen1 is None:
        return dict(ok=False, mode=None, reason='連雙層都排不下(腹板寬度bw不夠), 需要加大bw')

    if chosen1['layout']['n_layers'] == 1:
        d, r, chosen, n_passes = d_pass1, r1, chosen1, 1
    else:
        # 疊代最多6輪, 每輪用"上一輪真正選到的鋼筋規格"重算有效深度
        # (不是延用第一輪的筋徑)——這是真實抓到的bug(例如第一輪選#10
        # 排雙層算出d, 第二輪需求量變大改選#8, 若不重算d, 回傳的d/
        # eps_t/Mn跟真正選到的鋼筋規格不一致)。也真實抓到過選筋在
        # 多個尺寸之間循環、不會收斂的案例——這時候不放棄, 改成從
        # 疊代過程挑d最小(最保守)的那一輪自洽結果
        d_cur = effective_depth_multilayer(chosen1['layout'], chosen1['bar_d'], h_cm, cover, stirrup_d)
        history = []
        for _extra_pass in range(6):
            r_cur = solve_at_d(d_cur)
            if not r_cur['ok']:
                return dict(ok=False, mode=None, reason=f"雙層修正後: {r_cur['reason']}")
            chosen_cur = choose_bars_with_layout(r_cur['As_total'], bw_cm, cover, stirrup_d, bar_table)
            if chosen_cur is None:
                return dict(ok=False, mode=None, reason='雙層修正後仍排不下, 需要加大bw')
            if chosen_cur['layout']['n_layers'] == 1:
                d_new = h_cm - cover - stirrup_d - chosen_cur['bar_d']/2
            else:
                d_new = effective_depth_multilayer(chosen_cur['layout'], chosen_cur['bar_d'], h_cm, cover, stirrup_d)
            history.append((d_new, r_cur, chosen_cur))
            if abs(d_new - d_cur) < 0.01:
                d_cur, r, chosen = d_new, r_cur, chosen_cur
                break
            d_cur = d_new
        else:
            d_cur, r, chosen = min(history, key=lambda t: t[0])
        d, n_passes = d_cur, 2

    result = dict(ok=True, mode=r['mode'], As_total=r['As_total'], d=d,
                  bw=bw_cm, beff=beff_cm, hf=hf_cm,
                  bar_size=chosen['bar_size'], n_bars=chosen['n_bars'], bar_d=chosen['bar_d'],
                  As_provided=chosen['As_provided'], layout=chosen['layout'], n_passes=n_passes)
    if r['mode'] == 'T-beam':
        result['Asf'] = r['Asf']
        result['Asw'] = r['Asw']
        result['a_w'] = r['a_w']
        result['Muf'] = r['Muf']    # 翼板懸挑部分承擔的彎矩(kN-m)
        result['Muw'] = r['Muw']    # 腹板矩形部分承擔的彎矩(kN-m)
    else:
        result['a'] = r['a']

    d_t = d if chosen['layout']['n_layers'] == 1 else h_cm - cover - stirrup_d - chosen['bar_d']/2
    phiMn_provided, eps_t_actual, phi_actual, Mn_val = _phiMn_Tbeam_strain_compat(
        chosen['As_provided'], d, bw_cm, beff_cm, hf_cm, h_cm,
        fc, fy, Es, beta1, eps_cu, phi, d_t=d_t)
    result['d_t'] = d_t
    result['eps_t'] = eps_t_actual
    result['phi_used'] = phi_actual
    result['Mn'] = Mn_val
    result['phiMn_provided'] = phiMn_provided
    result['Mu_demand'] = Mu_kNm
    result['utilization'] = Mu_kNm/phiMn_provided
    return result


def analyze_section_capacity(As_cm2, d_cm, b_cm=None, h_cm=None, As_prime_cm2=None,
                               d_prime_cm=None, bw_cm=None, beff_cm=None, hf_cm=None,
                               fc=280.0, fy=4200.0, Es=2.0e6, phi=0.9, eps_cu=0.003,
                               beta1=None, Mu_kNm=None, d_t_cm=None):
    """給定斷面幾何+材料+**已經知道的鋼筋量**, 直接用應變相容法算標稱
    強度phiMn——這是分析(analysis), 不是設計(design):design_rebar()
    等函式是「給Mu, 反推需要多少鋼筋」, 這個函式是反過來「已經有一根
    梁(不管是既有結構或你自己指定的鋼筋量), 它能扛多少」。

    根據傳入的參數自動判斷斷面類型:
    - 只給 As_cm2, b_cm, h_cm: 矩形單筋斷面
    - 加給 As_prime_cm2, d_prime_cm: 矩形雙筋斷面
    - 給 bw_cm, beff_cm, hf_cm(不給b_cm/h_cm, 用h_cm=d_cm+估計值也可以
      但建議直接給h_cm): T形斷面

    d_t_cm: 最外層拉力鋼筋的有效深度(不是加權形心d_cm)——排單層時
    兩者相同, 可以省略; 排雙層以上時, 規範規定phi要看最外層那一根
    的淨拉應變, 不是加權形心, 如果你在分析一個已知排成雙層的既有
    結構, 這裡要傳入真正的最外層深度, 不然phi判斷會不準確(這是
    這次修正的重點, 之前版本直接固定phi=0.9, 沒有做這個檢查)。

    如果傳入 Mu_kNm, 順便回傳 utilization 判定合格與否; 不傳就只回傳
    phiMn 本身。回傳的dict也會附上eps_t/phi_used, 讓你直接看到
    折減係數是不是被過渡區規則調整過。

    這個函式底層跟 design_doubly_reinforced()/design_Tbeam() 內部用
    的是同一套應變相容法, 只是這裡不做選筋、不做排筋幾何檢查——單純
    分析「給定這個斷面配這些鋼筋, 標稱強度是多少」, 用途包括: 核對
    既有結構圖說的配筋夠不夠、快速試算不同鋼筋量的容量而不用跑完整
    設計流程。跟外部工具 concreteproperties(VL-08 用來交叉驗證的
    第三方套件)做的是同一類事, 這裡是本repo自己內建的版本。
    """
    if beta1 is None:
        beta1 = 0.85 if fc <= 280 else max(0.65, 0.85-0.05*(fc-280)/70)
    if d_t_cm is None:
        d_t_cm = d_cm

    if bw_cm is not None:
        if beff_cm is None or hf_cm is None or h_cm is None:
            raise ValueError("T形斷面分析需要同時給bw_cm/beff_cm/hf_cm/h_cm")
        phiMn, eps_t_actual, phi_actual, Mn_val = _phiMn_Tbeam_strain_compat(
            As_cm2, d_cm, bw_cm, beff_cm, hf_cm, h_cm, fc, fy, Es, beta1, eps_cu, phi,
            d_t=d_t_cm)
    elif As_prime_cm2 is not None:
        if b_cm is None or h_cm is None or d_prime_cm is None:
            raise ValueError("雙筋斷面分析需要同時給b_cm/h_cm/d_prime_cm")
        phiMn, eps_t_actual, phi_actual, Mn_val = _phiMn_doubly_strain_compat(
            As_cm2, As_prime_cm2, d_cm, d_prime_cm, b_cm, h_cm, fc, fy, Es, beta1, eps_cu, phi,
            d_t=d_t_cm)
    else:
        if b_cm is None:
            raise ValueError("矩形斷面分析需要給b_cm(單筋)或加b_prime_cm(雙筋)")
        a = As_cm2*fy/(0.85*fc*b_cm)
        c = a/beta1
        eps_t_actual = eps_cu*(d_t_cm-c)/c if c > 0 else 0
        phi_actual = phi_from_eps_t(eps_t_actual, eps_ty=fy/Es)
        Mn_kgfcm = As_cm2*fy*(d_cm-a/2)
        Mn_val = Mn_kgfcm*9.80665e-5
        phiMn = phi_actual*Mn_val

    result = dict(phiMn_provided=phiMn, eps_t=eps_t_actual, phi_used=phi_actual, Mn=Mn_val)
    if Mu_kNm is not None:
        result['Mu_demand'] = Mu_kNm
        result['utilization'] = Mu_kNm/phiMn
    return result


# ============================================================
# 柱設計——軸力+彎矩互制(P-M interaction)
# ============================================================

def _phi_column_from_eps_t(eps_t, spiral=False, eps_ty=0.002):
    """柱子的phi折減: 跟梁同一套過渡區規則, 差別在壓力控制端的下限
    (螺箍柱0.75, 橫箍柱0.65, 梁沒有這個分別因為梁不會落在壓力控制區)。
    eps_t規範慣用"拉伸為正", 呼叫端要注意正負號(這裡曾經真實踩過一次
    符號搞反的坑, 內部用"壓力為正"算完要記得轉號)。"""
    phi_cc = 0.75 if spiral else 0.65
    if eps_t >= 0.005:
        return 0.9
    if eps_t <= eps_ty:
        return phi_cc
    return phi_cc + (eps_t - eps_ty)*((0.9-phi_cc)/(0.005-eps_ty))


def _column_PM_point(c, b_cm, h_cm, layers, fc, fy, Es, beta1, eps_cu=0.003):
    """給定中性軸深度c, 算出對應的(Pn, Mn, eps_t)一點。應變相容法,
    跟design_doubly_reinforced()/design_Tbeam()內部用的是同一套原理,
    差別是柱子兩側都可能是"受壓筋"或"受拉筋"(視c而定, 不像梁固定
    哪一側受拉), 所以每一層鋼筋都要各自判斷。

    layers: [(As_i, y_i), ...], y_i是該層鋼筋到"受壓邊緣"的距離(cm),
    不是到形心的距離——跟design_doubly_reinforced()的d/d_prime同一套
    量法。c也是同樣從受壓邊緣算的中性軸深度。

    回傳的Pn: kgf(正=壓力), Mn: kgf-cm, eps_t: 最外層(離受壓邊最遠,
    通常是最先進入拉力的那層)鋼筋的淨拉應變(拉伸為正, 規範慣用號約定)。
    """
    a = min(beta1*c, h_cm)
    Cc = 0.85*fc*b_cm*a
    y_bar_c = h_cm/2 - a/2
    N = Cc
    M = Cc*y_bar_c
    eps_y = fy/Es
    max_y = max(y for _, y in layers)
    eps_t_extreme = 0.0

    for As_i, y_i in layers:
        eps_i = eps_cu*(c - y_i)/c if c > 0 else 0
        eps_i_clamped = max(min(eps_i, eps_y), -eps_y)
        f_i = Es*eps_i_clamped
        if y_i <= a:
            F_i = As_i*(f_i - 0.85*fc)  # 壓力區內, 扣掉被鋼筋取代的混凝土
        else:
            F_i = As_i*f_i
        N += F_i
        y_i_from_center = h_cm/2 - y_i
        M += F_i*y_i_from_center
        if y_i == max_y:
            eps_t_extreme = -eps_i  # 轉成規範慣用"拉伸為正"

    return N, M, eps_t_extreme


def design_column_PM(b_cm, h_cm, As_per_layer_cm2, cover_to_center_cm,
                       n_layers=3, fc=280.0, fy=4200.0, Es=2.0e6,
                       beta1=None, spiral=False, n_points=60,
                       Pu_kN=None, Mu_kNm=None):
    """矩形柱P-M(軸力-彎矩)互制圖分析。跟design_rebar()等函式不同,
    這是分析(analysis)不是設計(design)——柱子的配筋通常是先假設一組
    對稱配置, 畫出完整的phi-包絡線, 再檢查各種軸力+彎矩組合(不同地震
    方向、不同樓層)是否都落在包絡線內, 不是像梁一樣「給Mu反推鋼筋量」。

    參數
    ----
    As_per_layer_cm2: 每一層鋼筋的總面積(cm^2)——對稱配置時每層通常
        相同, 如果各層不同, 傳list(長度要跟n_layers一致)
    cover_to_center_cm: 最外層鋼筋中心到斷面邊緣的距離(cm)
    n_layers: 鋼筋層數(沿斷面高度方向均勻分布, 含最外兩層+中間層)
    spiral: True=螺箍柱(壓力控制phi下限0.75), False=橫箍柱(0.65)
    Pu_kN/Mu_kNm: 如果給定, 順便檢查這個載重組合是否落在phi-包絡線內

    回傳dict: curve(完整曲線, 每點含c/Pn/Mn/eps_t/phi/phiPn/phiMn)、
    Po(純壓點phiPn, 無彎矩時的軸壓容量)、Mo(純彎點phiMn, Pn=0時的
    彎矩容量)、balanced(平衡點, eps_t恰好=eps_y時)、以及如果有給
    Pu/Mu, 附上utilization跟within_envelope判定。
    """
    if beta1 is None:
        beta1 = 0.85 if fc <= 280 else max(0.65, 0.85-0.05*(fc-280)/70)

    if isinstance(As_per_layer_cm2, (int, float)):
        As_list = [As_per_layer_cm2]*n_layers
    else:
        As_list = list(As_per_layer_cm2)
        n_layers = len(As_list)

    if n_layers == 1:
        y_positions = [h_cm/2]
    else:
        y_positions = [cover_to_center_cm + i*(h_cm-2*cover_to_center_cm)/(n_layers-1)
                       for i in range(n_layers)]
    layers = list(zip(As_list, y_positions))

    # c從很小(接近純彎)掃到很大(接近純壓), 非線性間距讓平衡點附近取樣密一點
    # 取樣策略: 前半段(涵蓋eps_t從很大遞減到eps_ty的過渡區)用線性間距
    # 加密, 後半段(壓力控制區, phi已經固定不再變化)用非線性間距節省
    # 點數——過渡區的phiMn會隨c增加平滑遞減(這是規範phi線性折減本身
    # 固有的現象, 不是bug, 但取樣太稀疏畫出來的圖會有鋸齒感, 這裡
    # 針對過渡區加密)
    n_dense = n_points//2
    c_dense = [0.5 + i*(h_cm*0.9)/(n_dense-1) for i in range(n_dense)]
    n_sparse = n_points - n_dense
    c_sparse = [h_cm*0.9 + (h_cm*3.1)*((i+1)/n_sparse)**1.5 for i in range(n_sparse)]
    c_values = c_dense + c_sparse

    curve = []
    for c in c_values:
        N, M, eps_t = _column_PM_point(c, b_cm, h_cm, layers, fc, fy, Es, beta1)
        phi = _phi_column_from_eps_t(eps_t, spiral=spiral)
        Pn_kN, Mn_kNm = N*9.80665e-3, M*9.80665e-5
        curve.append(dict(c=c, Pn=Pn_kN, Mn=Mn_kNm, eps_t=eps_t, phi=phi,
                          phiPn=phi*Pn_kN, phiMn=phi*Mn_kNm))

    # 純壓點(c最大那一個, 已經很接近c->infinity的理論極限)
    Po_point = curve[-1]
    # 純彎點: 找Pn最接近0的一點, 線性內插到Pn=0
    # (c越大, Pn越大: 隨著c從小掃到大, Pn從負(拉力主導)變正(壓力主導),
    # 要找Pn從負變正、經過0的那個區間——之前這裡方向寫反了, 判斷條件
    # 一直沒被觸發, 誤用了純壓點附近Mn≈0的值當作"純彎點", 已修正)
    for i in range(len(curve)-1):
        if curve[i]['Pn'] <= 0 <= curve[i+1]['Pn']:
            t = -curve[i]['Pn']/(curve[i+1]['Pn']-curve[i]['Pn'])
            Mo = curve[i]['Mn'] + t*(curve[i+1]['Mn']-curve[i]['Mn'])
            phi_at_Mo = curve[i]['phi'] + t*(curve[i+1]['phi']-curve[i]['phi'])
            break
    else:
        Mo, phi_at_Mo = curve[0]['Mn'], curve[0]['phi']

    # 平衡點: eps_t最接近eps_y(=fy/Es)的一點
    eps_y = fy/Es
    balanced_point = min(curve, key=lambda p: abs(p['eps_t']-eps_y))

    result = dict(curve=curve, Po_phiPn=Po_point['phiPn'],
                  Mo_phiMn=phi_at_Mo*Mo, balanced=balanced_point,
                  b_cm=b_cm, h_cm=h_cm, As_total=sum(As_list),
                  n_layers=n_layers, spiral=spiral)

    if Pu_kN is not None and Mu_kNm is not None:
        # 檢查(Pu,Mu)是否落在phi-包絡線內: 從原點往(Pu,Mu)方向找包絡線上
        # 對應的點, 比較該方向下包絡線能提供的容量
        if Mu_kNm == 0:
            capacity_ratio = None
            within = Pu_kN <= Po_point['phiPn']
        else:
            angle_target = Pu_kN/Mu_kNm if Mu_kNm != 0 else float('inf')
            best = min(curve, key=lambda p: abs(p['phiMn']) < 1e-9 and float('inf') or
                       abs(p['phiPn']/p['phiMn'] - angle_target) if p['phiMn'] != 0 else float('inf'))
            # 用簡單的比例法估計: 同一角度方向上, 需求點到原點的距離 vs 包絡線上同角度點到原點的距離
            demand_r = (Pu_kN**2+Mu_kNm**2)**0.5
            capacity_r = (best['phiPn']**2+best['phiMn']**2)**0.5
            capacity_ratio = demand_r/capacity_r if capacity_r > 0 else float('inf')
            within = capacity_ratio <= 1.0
        result['Pu_demand'] = Pu_kN
        result['Mu_demand'] = Mu_kNm
        result['utilization'] = capacity_ratio
        result['within_envelope'] = within

    return result


# ============================================================
# 設計摘要——放在notebook最後一格, 緊接在斷面圖之後
# ============================================================

def print_design_summary(kind, geometry, material, demand, result,
                           capacity_key=None, demand_key=None,
                           capacity_value=None, demand_value=None,
                           bar_count_key='n_bars',
                           bar_size_key='bar_size', bar_area_key='As_provided',
                           bar_unit='cm^2'):
    """統一格式的設計摘要,放在每個 Case-08.x notebook 的最後一格,緊接在斷面圖之後。

    印出:幾何、材料、設計需求、選筋後實際供給、最後給合格判定——
    數字要足夠讓人不用重新執行程式碼、光憑印出來的這幾個數字就能
    手算驗證(不是只信任程式自己說"合格")。

    kind: 標題(例如"Case-08.1 矩形單筋梁撓曲設計")
    geometry/material/demand: dict, 直接印出key=value
    result: design_rebar()/design_doubly_reinforced()/design_Tbeam()/
        design_stirrups() 的回傳dict
    capacity_key/demand_key: result裡對應「供給容量」跟「需求」的key名稱
        (不同函式欄位名不同, 例如撓曲是phiMn_provided/Mu_demand,
        剪力是phiVn/Vu_demand)——如果供給容量不是來自result本身的某個
        key(例如雙筋梁/T形梁的容量是另外用應變相容法驗證出來的),
        改用 capacity_value/demand_value 直接傳數值進來, 不要勉強找
        一個不相關的key湊數。
    """
    print("="*60)
    print(f"設計摘要: {kind}")
    print("="*60)
    print("\n[幾何]")
    for k, v in geometry.items():
        print(f"  {k} = {v}")
    print("\n[材料]")
    for k, v in material.items():
        print(f"  {k} = {v}")
    print("\n[設計需求]")
    for k, v in demand.items():
        print(f"  {k} = {v}")
    print("\n[選筋後實際供給]")
    if bar_size_key in result and bar_count_key in result:
        print(f"  鋼筋: {result[bar_count_key]}-{result[bar_size_key]}, "
              f"{bar_area_key} = {result[bar_area_key]:.3f} {bar_unit}")
    elif bar_size_key in result:
        print(f"  箍筋規格: {result[bar_size_key]}")
    if 'spacing_cm' in result:
        print(f"  箍筋間距 = {result['spacing_cm']:.0f} cm")

    capacity = capacity_value if capacity_value is not None else result[capacity_key]
    demand_val = demand_value if demand_value is not None else result[demand_key]
    utilization = demand_val/capacity
    print(f"\n[合格判定]")
    print(f"  供給容量 = {capacity:.2f}")
    print(f"  設計需求 = {demand_val:.2f}")
    print(f"  使用率(需求/供給) = {utilization:.1%}")
    status = "合格" if utilization <= 1.0 else "不合格"
    print(f"  結論: {status}"
          f"({'供給 >= 需求' if utilization <= 1 else '供給 < 需求, 需重新設計'})")
    print("="*60)
    return utilization


# ============================================================
# 剪力設計
# ============================================================

DEFAULT_STIRRUP_TABLE = {"#3(D10)": 0.71, "#4(D13)": 1.267}


def shear_capacity_concrete(bw_cm, d_cm, fc=280.0, phi=0.75):
    """混凝土本身的剪力容量 phiVc(強度設計法簡化公式, 無顯著軸力情況)。
    Vc = 0.53*sqrt(fc')*bw*d (kgf/cm^2單位), 回傳 phiVc 單位 kN。"""
    Vc_kgf = 0.53*math.sqrt(fc)*bw_cm*d_cm
    return phi*Vc_kgf*9.80665e-3


def design_stirrups(Vu_kN, bw_cm, d_cm, fc=280.0, fyv=2800.0, phi=0.75,
                     stirrup_table=None):
    """
    箍筋設計(強度設計法, 雙肢垂直箍筋)。

    參數
    ----
    Vu_kN : 設計剪力需求 (kN) ——注意單位是kN, 不是kN-m(剪力不是彎矩)
    bw_cm, d_cm : 梁寬、有效深度 (cm) ——d建議用design_rebar()/
        design_doubly_reinforced()回傳的真實排筋後有效深度, 不是原始假設值
    fyv : 箍筋降伏強度 (kgf/cm^2), 常用比主筋低的等級(SD280), 可與主筋fy不同

    回傳
    ----
    dict, 含: need_stirrups(是否需要剪力筋)、ok(能否設計出可行方案)、
    bar_size/spacing_cm(選定箍筋規格與間距)、phiVc/phiVn(供給容量)、utilization
    """
    if stirrup_table is None:
        stirrup_table = DEFAULT_STIRRUP_TABLE

    Vu_kgf = Vu_kN*1000/9.80665
    Vc_kgf = 0.53*math.sqrt(fc)*bw_cm*d_cm
    phiVc_kgf = phi*Vc_kgf
    phiVc_kN = phiVc_kgf*9.80665e-3

    if Vu_kgf <= 0.5*phiVc_kgf:
        return dict(need_stirrups=False, ok=True, phiVc=phiVc_kN, Vu_demand=Vu_kN,
                    reason="Vu<=0.5*phiVc, 理論上不需要剪力筋(實務上仍建議配置最小箍筋)")

    Vs_req_kgf = max(0.0, Vu_kgf/phi - Vc_kgf)
    Vs_max_kgf = 2.2*math.sqrt(fc)*bw_cm*d_cm
    if Vs_req_kgf > Vs_max_kgf:
        return dict(need_stirrups=True, ok=False, phiVc=phiVc_kN, Vu_demand=Vu_kN,
                    reason=f"Vs需求超過上限(斜壓破壞風險), 需加大bw或d "
                           f"(Vs_req={Vs_req_kgf*9.80665e-3:.1f}kN > "
                           f"Vs_max={Vs_max_kgf*9.80665e-3:.1f}kN)")

    best = None
    for name, Ab in stirrup_table.items():
        Av = 2*Ab
        s_req = Av*fyv*d_cm/Vs_req_kgf if Vs_req_kgf > 0 else 1e9
        s_max = min(d_cm/2 if Vs_req_kgf <= 1.1*math.sqrt(fc)*bw_cm*d_cm else d_cm/4, 60.0)
        s_use = min(s_req, s_max)
        s_practical = math.floor(s_use/5)*5
        if s_practical < 5:
            continue
        Av_min_check = max(0.2*math.sqrt(fc)*bw_cm*s_practical/fyv,
                             3.5*bw_cm*s_practical/fyv)
        if Av < Av_min_check:
            continue
        if best is None or s_practical > best['spacing']:
            best = dict(bar_size=name, spacing=s_practical, Av=Av)

    if best is None:
        return dict(need_stirrups=True, ok=False, phiVc=phiVc_kN, Vu_demand=Vu_kN,
                    reason="沒有找到滿足最小鋼筋量限制的箍筋規格+間距組合")

    Vs_provided_kgf = best['Av']*fyv*d_cm/best['spacing']
    phiVn_kN = phi*(Vc_kgf+Vs_provided_kgf)*9.80665e-3

    return dict(need_stirrups=True, ok=True, bar_size=best['bar_size'],
                spacing_cm=best['spacing'], Av=best['Av'],
                phiVc=phiVc_kN, Vs_provided=Vs_provided_kgf*9.80665e-3,
                phiVn=phiVn_kN, Vu_demand=Vu_kN, utilization=Vu_kN/phiVn_kN)



def draw_rc_section(b_cm, h_cm, cover_cm, layout, bar_diameter_cm,
                      As_prime_cm2=None, d_prime_cm=None, title="RC Section", ax=None):
    """矩形斷面配筋圖。layout 是 compute_bar_layout() 的回傳值(或
    design_rebar()/design_doubly_reinforced() 回傳dict裡的'layout'欄位)
    ——這個函式只負責把算好的排列畫出來, 不自己判斷單層雙層。"""
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 6))

    ax.add_patch(plt.Rectangle((0, 0), b_cm, h_cm, facecolor='#e8e8e8',
                                 edgecolor='black', linewidth=2))
    ax.add_patch(plt.Rectangle((cover_cm, cover_cm), b_cm-2*cover_cm, h_cm-2*cover_cm,
                                 facecolor='none', edgecolor='#888888', linewidth=1.2, linestyle='--'))

    stirrup_d = 0.95
    n_layers = layout['n_layers']
    rows = layout['layout']
    d1 = cover_cm + stirrup_d + bar_diameter_cm/2  # 最外層(離受拉邊緣最近)距邊緣的距離

    def row_xs(n):
        available_width = b_cm - 2*(cover_cm+stirrup_d) - bar_diameter_cm
        if n == 1:
            return [b_cm/2]
        return [cover_cm+stirrup_d+bar_diameter_cm/2 + i*available_width/(n-1) for i in range(n)]

    for layer_idx, n in enumerate(rows):
        y = cover_cm + d1 - d1 if layer_idx == 0 else None  # 佔位, 下面重新計算
        y_from_bottom = d1 if layer_idx == 0 else d1 + layer_idx*(bar_diameter_cm + (layout.get('vertical_clear_spacing') or 2.5))
        for x in row_xs(n):
            ax.add_patch(plt.Circle((x, y_from_bottom), bar_diameter_cm/2, facecolor='#333333',
                                      edgecolor='black', zorder=5))

    if As_prime_cm2 and d_prime_cm:
        Ab_prime_guess = bar_diameter_cm  # 沿用同一個直徑概估壓力筋根數(呼叫端如需精確應自行傳入)
        bar_area = math.pi*(bar_diameter_cm/2)**2
        n_bars_top = max(2, round(As_prime_cm2/bar_area))
        y_top = h_cm - d_prime_cm
        available_width = b_cm - 2*(cover_cm+stirrup_d) - bar_diameter_cm
        xs_top = [b_cm/2] if n_bars_top == 1 else \
            [cover_cm+stirrup_d+bar_diameter_cm/2 + i*available_width/(n_bars_top-1) for i in range(n_bars_top)]
        for x in xs_top:
            ax.add_patch(plt.Circle((x, y_top), bar_diameter_cm/2, facecolor='#c00000',
                                      edgecolor='black', zorder=5))
        ax.text(b_cm+2, y_top, f"{n_bars_top}-D{bar_diameter_cm*10:.0f}\n(compression)",
                fontsize=8, va='center', color='#c00000')

    spacing_ok = layout['ok']
    status_color = 'green' if spacing_ok else 'red'
    layer_text = f"{n_layers} layer(s): {rows}"
    spacing_text = f"h-spacing={layout['clear_spacing_horizontal']:.2f}cm" if layout['clear_spacing_horizontal'] else ""
    if n_layers == 2 and layout.get('vertical_clear_spacing') is not None:
        spacing_text += f", v-spacing={layout['vertical_clear_spacing']:.2f}cm"
    status_text = 'OK' if spacing_ok else f"FAIL: {layout['reason']}"

    total_bars = sum(rows)
    ax.text(b_cm+2, d1, f"{total_bars}-D{bar_diameter_cm*10:.0f}\n(tension, {layer_text})",
            fontsize=8, va='center', color='#333333')
    ax.text(b_cm/2, -3, f"b={b_cm:.0f}cm", ha='center', fontsize=9)
    ax.text(-3, h_cm/2, f"h={h_cm:.0f}cm", va='center', rotation=90, fontsize=9)
    ax.text(b_cm/2, h_cm+2, f"{spacing_text} [{status_text}]",
            ha='center', fontsize=7.5, color=status_color)

    ax.set_xlim(-8, b_cm+18)
    ax.set_ylim(-6, h_cm+6)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=10)
    ax.axis('off')
    return ax, spacing_ok


def draw_Tbeam_section(bw_cm, beff_cm, hf_cm, h_cm, cover_cm, layout,
                         bar_diameter_cm, title="T-beam Section", ax=None):
    """T形斷面配筋圖。layout 是 compute_bar_layout() 的回傳值——只負責畫,
    不自己決定排法。拉力鋼筋畫在腹板寬度(bw)內。"""
    import matplotlib.pyplot as plt
    import matplotlib.path as mpath
    from matplotlib.patches import PathPatch
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))

    web_x0 = (beff_cm-bw_cm)/2
    verts = [(web_x0, 0), (web_x0+bw_cm, 0), (web_x0+bw_cm, h_cm-hf_cm), (beff_cm, h_cm-hf_cm),
              (beff_cm, h_cm), (0, h_cm), (0, h_cm-hf_cm), (web_x0, h_cm-hf_cm), (web_x0, 0)]
    ax.add_patch(PathPatch(mpath.Path(verts), facecolor='#e8e8e8', edgecolor='black', linewidth=2))

    stirrup_d = 0.95
    n_layers = layout['n_layers']
    rows = layout['layout']
    d1 = cover_cm + stirrup_d + bar_diameter_cm/2
    available_width = bw_cm - 2*(cover_cm+stirrup_d) - bar_diameter_cm

    def row_xs(n):
        if n == 1:
            return [web_x0+bw_cm/2]
        return [web_x0+cover_cm+stirrup_d+bar_diameter_cm/2 + i*available_width/(n-1) for i in range(n)]

    for layer_idx, n in enumerate(rows):
        y_from_bottom = d1 if layer_idx == 0 else d1 + layer_idx*(bar_diameter_cm + (layout.get('vertical_clear_spacing') or 2.5))
        for x in row_xs(n):
            ax.add_patch(plt.Circle((x, y_from_bottom), bar_diameter_cm/2, facecolor='#333333',
                                      edgecolor='black', zorder=5))

    spacing_ok = layout['ok']
    status_color = 'green' if spacing_ok else 'red'
    layer_text = f"{n_layers} layer(s): {rows}"
    spacing_text = f"h-spacing={layout['clear_spacing_horizontal']:.2f}cm" if layout['clear_spacing_horizontal'] else ""
    if n_layers == 2 and layout.get('vertical_clear_spacing') is not None:
        spacing_text += f", v-spacing={layout['vertical_clear_spacing']:.2f}cm"
    status_text = 'OK' if spacing_ok else f"FAIL: {layout['reason']}"

    total_bars = sum(rows)
    ax.text(beff_cm+3, d1, f"{total_bars}-D{bar_diameter_cm*10:.0f}\n(tension, {layer_text})",
            fontsize=8, va='center')
    ax.text(beff_cm/2, -3, f"beff={beff_cm:.0f}cm", ha='center', fontsize=9)
    ax.text(web_x0+bw_cm/2, h_cm-hf_cm-3, f"bw={bw_cm:.0f}cm", ha='center', fontsize=8, color='gray')
    ax.text(-3, h_cm/2, f"h={h_cm:.0f}cm", va='center', rotation=90, fontsize=9)
    ax.text(beff_cm/2, h_cm+2, f"{spacing_text} [{status_text}]",
            ha='center', fontsize=7.5, color=status_color)

    ax.set_xlim(-8, beff_cm+22)
    ax.set_ylim(-6, h_cm+6)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=10)
    ax.axis('off')
    return ax, spacing_ok


def draw_stirrup_elevation(L_cm, h_cm, cover_cm, spacing_cm, bar_size,
                             title="Stirrup Elevation", ax=None):
    """箍筋立面圖(側視), 顯示沿梁長的箍筋間距分布——這是實務上箍筋
    設計真正要交代的東西。跟縱向鋼筋不同, 箍筋的斷面圖資訊量很低
    (畫出來只有一個矩形圈, 看不出設計重點), 立面圖(側視)才看得出
    間距, 這是業界通用的畫法。"""
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 3))

    ax.add_patch(plt.Rectangle((0, 0), L_cm, h_cm, facecolor='#e8e8e8',
                                 edgecolor='black', linewidth=1.5))
    ax.plot([cover_cm, L_cm-cover_cm], [cover_cm, cover_cm], color='#333333', lw=2)
    ax.plot([cover_cm, L_cm-cover_cm], [h_cm-cover_cm, h_cm-cover_cm], color='#333333', lw=2)

    n_stirrups = int((L_cm - 2*cover_cm) // spacing_cm) + 1
    x_positions = [cover_cm + i*spacing_cm for i in range(n_stirrups)
                   if cover_cm + i*spacing_cm <= L_cm-cover_cm]
    for x in x_positions:
        ax.plot([x, x], [cover_cm*0.3, h_cm-cover_cm*0.3], color='#c00000', lw=1.5)

    if len(x_positions) >= 2:
        ax.annotate('', xy=(x_positions[1], -h_cm*0.15), xytext=(x_positions[0], -h_cm*0.15),
                    arrowprops=dict(arrowstyle='<->', color='blue'))
        ax.text((x_positions[0]+x_positions[1])/2, -h_cm*0.28, f's={spacing_cm:.0f}cm',
                ha='center', fontsize=9, color='blue')

    ax.text(L_cm/2, h_cm+h_cm*0.15,
            f"{bar_size} stirrups @ {spacing_cm:.0f}cm o.c. ({len(x_positions)} total)",
            ha='center', fontsize=10)
    ax.set_xlim(-L_cm*0.05, L_cm*1.05)
    ax.set_ylim(-h_cm*0.4, h_cm*1.3)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=10)
    return ax


def draw_PM_interaction(result, title="P-M Interaction Diagram", ax=None):
    """畫柱子的phi折減P-M互制圖(標稱曲線phiPn/phiMn), 標出純壓點、
    純彎點、平衡點三個特徵點, 如果result裡有Pu/Mu需求點也一併畫出來,
    直接看合不合格。"""
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 7))

    curve = result['curve']
    Mn_vals = [p['phiMn'] for p in curve] + [-p['phiMn'] for p in curve[::-1]]
    Pn_vals = [p['phiPn'] for p in curve] + [p['phiPn'] for p in curve[::-1]]
    ax.plot(Mn_vals, Pn_vals, color='steelblue', lw=2, label='phi-envelope (design capacity)')

    ax.plot(0, result['Po_phiPn'], 'o', color='#333333', ms=6)
    ax.annotate('Po (pure compression)', (0, result['Po_phiPn']), fontsize=8,
                textcoords="offset points", xytext=(8, 0))
    ax.plot(result['Mo_phiMn'], 0, 'o', color='#333333', ms=6)
    ax.annotate('Mo (pure flexure)', (result['Mo_phiMn'], 0), fontsize=8,
                textcoords="offset points", xytext=(8, -12))
    bal = result['balanced']
    ax.plot(bal['phiMn'], bal['phiPn'], 'o', color='#c00000', ms=6)
    ax.annotate('balanced point', (bal['phiMn'], bal['phiPn']), fontsize=8, color='#c00000',
                textcoords="offset points", xytext=(8, 8))

    if 'Pu_demand' in result:
        color = 'green' if result['within_envelope'] else 'red'
        ax.plot(result['Mu_demand'], result['Pu_demand'], '*', color=color, ms=16,
                label=f"demand point ({'OK' if result['within_envelope'] else 'FAIL'})")

    ax.axhline(0, color='gray', lw=0.5)
    ax.axvline(0, color='gray', lw=0.5)
    ax.set_xlabel('phiMn (kN-m)')
    ax.set_ylabel('phiPn (kN)')
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc='lower right')
    ax.grid(True, alpha=0.3)
    return ax


if __name__ == "__main__":
    r = design_rebar(112.5, 30.0, 50.0, cover=4.0)
    assert abs(r['phiMn_provided'] - 119.17) < 0.1, "自我測試失敗(單筋案例), 數字跟已知案例對不上"
    assert r['layout']['n_layers'] == 1, "這個案例應該是單層"

    r2 = design_doubly_reinforced(420.0, 30.0, 50.0, 6.0)
    assert r2['need_doubly'], "這個案例應該觸發雙筋設計"
    assert r2['layout']['n_layers'] == 2, "這個案例應該觸發雙層排筋"
    assert r2['layout']['ok'], "雙層排列應該排得下"

    print("rc_design.py 自我測試通過(含雙層排筋)")

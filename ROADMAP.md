# ROADMAP

本 repo 的定位:**回答「依照台灣耐震設計流程,可以完整重現並驗證嗎?」**

姐妹專案 [reproducible-structural-benchmarks](https://github.com/zhixiu0223/reproducible-structural-benchmarks)
定位不同、互不重疊:它回答「分析引擎本身算得對不對」,用已知答案的
標竿案例,不涉及台灣法規。`taiwan-seismic-code-calc` 建立在這個基礎上,
重現「建築資料 → 法規計算 → 建模 → 驗算」的完整流程。

---

## 核心原則

> 越大的模型,越不知道錯在哪。

每個 Case 獨立驗證、獨立當教學節點。新 Case 只在前一個**完全通過**後開始。
**已 PASS 封存的 Case 不回頭改程式邏輯**——新發現、新限制的說明,寫在
ROADMAP 這個持續累積的地方,或另開新 Case,不回頭動舊 notebook 的程式碼。

## Analysis 與 Design 的區分

- **Analysis**:給定斷面驗證「模型算得對不對」(Case-01/02/03)
- **Design**:給定需求決定「斷面該多大」(Case-03.5/03.6/03.6b/03.7)
- Design 系列選出的斷面是**分析模型的初始斷面**,不是最終施工設計尺寸

---

## ⚠️ 重要限制說明:剪力構架假設的有效範圍(Case-04.5 的發現)

Case-03 到 Case-04 全程使用「剪力構架假設」(`ops.fix` 拘束柱頂柱底
轉角,等同假設梁無限剛)。這個假設**在數學上完全正確地做到它宣稱要
做的事**,但直到 Case-04.5 才第一次檢查它的**有效範圍**:

- 準確度取決於 $k_b/k_c$(梁勁度因子/柱勁度因子)比值
- $k_b/k_c$ 大(柱遠比梁軟)→ 簡化幾乎無誤差
- $k_b/k_c$ 小(柱梁勁度相當)→ 簡化會**抹平方向性差異**

這個 $k_b/k_c$ 判準後來在 Case-02.5(反曲點法)、Case-02.6(多層構架
U 形誤差曲線)獨立驗證過同一套規律,不是單一案例的巧合。

---

## Case 序列

### Case-01:單自由度(SDOF)—— **[已完成]**
`notebooks/case01_sdof.ipynb`

### Case-02:一跨一層 —— **[已完成]**
`notebooks/case02_one_bay_one_story.ipynb` — 位移法閉合解驗證側向勁度

### Case-02.5:反曲點法 + 虛功法 —— **[已完成]**
`notebooks/case02_5_portal_virtual_work.ipynb` — 另一個獨立的分析端
快速手算工具,對照 Case-02 精確解,誤差規律與 $k_b/k_c$ 直接相關,
跟 Case-04.5(不同案例、不同簡化手法)測出的規律方向一致

### Case-02.6:反曲點法 U 形誤差曲線 —— **[已完成]**
`notebooks/case02_6_portal_method_height_effect.ipynb` — 建立
`FrameModel`+可抽換 `Solver` 平台,掃描 1~50 層發現誤差呈 U 形
(先隨高度遞減、N≈12 反轉、之後單調遞增),高樓層段成因確鑿
(柱軸向伸縮驅動的整體彎曲被反曲點法完全忽略);斷面隨高度縮放
會拖慢誤差惡化速度,但沒有大幅推遲反轉點本身

### Case-03:一跨二層 —— **[已完成]**
`notebooks/case03_one_bay_two_story.ipynb` — 剪力構架假設引入

### Case-03.5:試設斷面 —— **[已完成]**
`notebooks/case03_5_trial_sizing.ipynb`

### Case-03.6:快速強度檢核 —— **[已完成]**
`notebooks/case03_6_quick_strength_check.ipynb` — 依《結構混凝土
設計規範》實作,發現本案例 governing 條件是位移角而非強度

### Case-03.6b:可抽換檢核模組示範 —— **[已完成]**
`notebooks/case03_6b_check_module_swap_demo.ipynb` — RC+鋼結構檢核
(依《鋼結構極限設計法規範》),驗證分析/檢核介面可跨材料抽換

### Case-03.7:Demand 物件與 Design Loop —— **[已完成]**
`notebooks/case03_7_demand_design_loop.ipynb`

### Case-04:桃園案例(X 向 3 跨 + Y 向 1 跨)—— **[已完成]**
`notebooks/case04_taoyuan_case.ipynb` — 兩個獨立 2D 模型,結果與
法規文件反曲點法估計值吻合,發現兩方向需求在剪力構架假設下完全
相同(留給 Case-04.5 驗證)

### Case-04.5:真梁模型驗證 —— **[已完成]**
`notebooks/case04_5_real_frame_validation.ipynb` — 放開轉角自由度,
量化剪力構架假設有效範圍;直接算出 $K_{eff}$(不只位移/drift):
X 向勁度恆大於 Y 向 2 倍以上,且差距隨 $k_b/k_c$ 變小而擴大——
剪力構架簡化不是「差異小才測不出來」,是整個方法對此效應視而不見

### Case-05:真正的 3D 模型 —— **[已完成]**
`notebooks/case05_3d_model.ipynb` — 8 柱+X 向梁+Y 向梁+
`ops.rigidDiaphragm` 樓板剛性,真正耦合在同一模型;X/Y 向誤差
(相對 Case-04.5 獨立 2D 模型)分別為 1.8%/0.2%,「N 榀構架平均
分攤」假設驗證大致成立;含 3D 整體圖+X/Y 向切片視覺化

### Case-06:RC Fiber Section + Pushover + FEMA 273
引入 Fiber Section(Concrete01、Steel02),跑側推分析,套 FEMA 273
等面積雙直線法

### Case-07:反應譜分析 + ATC-40 CSM
Pushover 曲線轉 ADRS 座標找性能點,實作 SRSS 與 CQC 多振態組合對比

### Case-08:時程分析
額外方法論驗證層,非規範強制要求

---

## FEMA 273 / ATC-40 的定位澄清

這兩份文件是美國既有建築耐震評估/補強指引,**不是台灣新建物法定合規
流程的一部分**。放進本 repo 是因為 Case-06/07 需要一套 Pushover→性能點
的既有方法論當骨架,必須用桃園案例自己跑出來的 Pushover 曲線重新代入。

---

## 明確不做的事

- 不在 Case 完全通過前平行展開下一個 Case
- 已 PASS 封存的 Case 不回頭改程式邏輯
- 不為了「更真實」而跳過中間 Case 直接做大模型
- 不在資料點不足時把觀察到的趨勢定案成正式工具——弱軸快速判定
  ($k_b/k_c$ 門檻值)雖然已有 Case-02.5/02.6/04.5 三個獨立來源
  互相佐證方向一致,但仍未定出可靠的數值門檻,留待未來視需要
  另開新 Case 正式處理

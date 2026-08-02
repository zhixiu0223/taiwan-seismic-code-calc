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
- $k_b/k_c$ 大(柱遠比梁軟)→ 簡化幾乎無誤差,不同跨數構架算出的
  結果幾乎相同
- $k_b/k_c$ 小(柱梁勁度相當)→ 簡化會**抹平方向性差異**(例如把
  X 向 3 跨、Y 向 1 跨算成完全一樣,但真梁模型顯示 X 向其實較硬)

**這代表 Case-03.5~04(以及依賴它們結論的所有後續判斷)的數值結果,
只在柱子相對梁足夠柔的情況下才準確**——這不是程式錯誤,是一個直到
現在才被量化的簡化假設邊界,詳見 Case-04.5。

---

## Case 序列

### Case-01:單自由度(SDOF)—— **[已完成]**
`notebooks/case01_sdof.ipynb` — 特徵值分析週期與靜力位移與手算閉合解
完全吻合(相對誤差 0.00e+00)

### Case-02:一跨一層 —— **[已完成]**
`notebooks/case02_one_bay_one_story.ipynb` — 位移法閉合解驗證側向勁度,
含結構視覺化

### Case-03:一跨二層 —— **[已完成]**
`notebooks/case03_one_bay_two_story.ipynb` — 剪力構架假設引入,2自由度
特徵值問題,含模態振型視覺化

### Case-03.5:試設斷面 —— **[已完成]**
`notebooks/case03_5_trial_sizing.ipynb` — 三輪迭代(18cm FAIL→20cm
PASS margin小→40cm PASS),僅檢核位移角

### Case-03.6:快速強度檢核 —— **[已完成]**
`notebooks/case03_6_quick_strength_check.ipynb` — 依《結構混凝土設計
規範》第21/22章實作軸力/彎矩/剪力檢核,發現本案例governing條件是
位移角而非強度

### Case-03.6b:可抽換檢核模組示範 —— **[已完成]**
`notebooks/case03_6b_check_module_swap_demo.ipynb` — RC檢核重構+新增
鋼結構檢核(依《鋼結構極限設計法規範》),驗證分析/檢核介面可跨材料抽換

### Case-03.7:Demand物件與Design Loop —— **[已完成]**
`notebooks/case03_7_demand_design_loop.ipynb` — Demand dataclass取代
散裝參數,`design_loop()`自動收斂,RC/鋼結構各自驗證與手動掃描結果一致

### Case-04:桃園案例(X向3跨+Y向1跨)—— **[已完成]**
`notebooks/case04_taoyuan_case.ipynb` — 延伸剪力構架法為通用多跨函式,
X向Y向真實構架分析結果與法規文件第15課反曲點法估計值吻合,含3D幾何
示意圖+2D變形對比視覺化。**發現兩方向需求完全相同**——當時判定為
剪力構架假設的侷限,留給 Case-04.5 驗證

### Case-04.5:真梁模型驗證 —— **[已完成]**
`notebooks/case04_5_real_frame_validation.ipynb` — 放開轉角自由度,
真的建梁元素(L/12經驗比試設,30x50cm),量化剪力構架假設的有效範圍:
- 20cm柱(kb/kc≈13.7):X/Y位移比≈99%,簡化模型幾乎無誤差
- 40cm柱(kb/kc≈0.85):X/Y位移比≈91%,簡化模型抹平約9~10%的
  方向性差異
- 驗證真梁模型位移大於簡化模型(簡化模型高估勁度)、X向確實比Y向硬
- **留下未完成的想法**:能否用 $k_b/k_c$ 做「弱軸快速判定」,只做
  governing方向的完整分析——目前只有3個資料點,門檻值不足以定案,
  留給未來視需要另開新 Case

### Case-05:三維 RC
加入 X 方向、Y 方向、樓板剛性假設、質量偏心(含規範規定的 5% 意外
偏心)——驗證 Case-04 用過的「N榀構架平均分攤」假設,以及扭轉效應

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
- Case-05 之前不加樓板剛性以外的三維複雜度
- 不為了「更真實」而跳過中間 Case 直接做大模型
- 不在資料點不足時把觀察到的趨勢定案成正式工具(見 Case-04.5 的
  弱軸判定想法)

---
title: "Stage 3 延伸講義與練習題"
subtitle: "荷載組合 · Demand Extraction · 斜率撓度 · RC 梁柱設計預覽"
author: "結構分析／RC 設計課後補充教材"
lang: zh-TW
---

# Stage 3 延伸講義與練習題

**適用對象**：已完成 2D 框架彈性分析（OpenSees／手算）之大學部或研究所結構課程  
**對應案例**：理想化桃園案例 Y 向單榀（1 跨 2 柱、2 層）  
**範圍說明**：本講義延伸 Stage 3（荷載組合與 demand extraction），並銜接 Stage 4 配筋預覽；**正式迭代配筋、強柱弱梁、capacity shear 不在 Stage 3 範圍內**。

---

# 第一部　講義

## 1. Stage 3 在做什麼？

Stage 2 已建立並驗證 **真梁真柱 + 規範勁度折減** 的 2D 彈性模型。Stage 3 完成三件事：

1. **重新推導重力載重**（有從屬寬度與材料單位重依據的 \(D\)、\(L\)）
2. **套完整荷載組合**（本模型 \(H=0\)、\(E_z=0\)）
3. **Demand extraction + 構件分組**：每個量留下 **governing load combination**（不可把不同工況的 max 硬湊）

分析模型是 **2D 平面構架**（`-ndm 2`），不是 3D。

---

## 2. 幾何、材料與勁度折減

| 項目 | 數值 |
|------|------|
| 跨度 \(L\) | 6.0 m |
| 層高 \(h_1=h_2\) | 3.5 m |
| 柱 trial | \(40\times40\) cm |
| 梁 trial | \(30\times50\) cm |
| \(E_{rc}\) | \(2.463\times10^7\) kN/m² |
| 柱有效勁度 | \(0.7I_g = 0.001493\) m⁴ |
| 梁有效勁度 | \(0.35I_g = 0.001094\) m⁴ |

\[
I_g=\frac{bh^3}{12}\quad\text{（柱取 }b=h\text{）},\qquad
I_{\mathrm{eff}}=R_F\cdot I_g
\]

---

## 3. 重力載重推導

- 從屬寬度：\(18\,\mathrm{m}/4\text{ 榀}=4.5\,\mathrm{m}\)
- 樓板 15 cm × 2400 kg/m³ + 粉刷 100 kg/m² → \(D_{\mathrm{area}}=460\) kg/m²
- 活載 300 kg/m²（住宅）
- 換算：\(\mathrm{kgf}\to\mathrm{kN}\) 乘 \(9.80665\times10^{-3}\)

**結果**

| 項目 | 數值 |
|------|------|
| \(D_{\mathrm{udl}}\) | 23.830 kN/m |
| \(L_{\mathrm{udl}}\) | 13.239 kN/m |
| \(D+L\) | 37.069 kN/m |
| 柱自重 | 3.766 kN/m（僅隨 \(D\) 係數） |

與 Stage 2 暫用值 49.2 kN/m 差約 24.7%（開放項目，如實記錄）。

---

## 4. 荷載組合

| 組合 | 式 |
|------|-----|
| C1 | \(1.4D+1.7L\) |
| C2 / C3 | \(1.05D\pm1.403E_x\) |
| C4 / C5 | \(0.9D\pm1.40E_x\) |
| C6 | \(0.9D\) |

- \(0.9D\)：自重估得準，但對傾覆／抗拔等「重力愈小愈不利」的檢查刻意打折。  
- 單榀地震力（Case-03.5）：\(F_1=9.938\) kN，\(F_2=15.900\) kN。

**Governing combination**：對某一構件某一內力，取絕對值最大者，並**記錄組合名稱**。

---

## 5. Demand 摘要（OpenSees，與重算一致）

### 1F 柱組（L+R envelope）

| 量 | 值 | combo |
|----|-----|-------|
| \(N_i\) | 372.1 kN | C1 |
| \(V_i\) | 27.8 kN | C3 |
| \(M_i\) | −56.4 kN·m | C3 |
| \(N_j\) | −353.7 kN | C1 |
| \(M_j\) | −50.0 kN·m | C1 |

### 2F 柱組

| 量 | 值 | combo |
|----|-----|-------|
| \(N_i\) | 186.1 kN | C1 |
| \(M_j\) | 142.1 kN·m | C1 |

### 梁（C1 控制端彎矩／剪力）

| 項目 | 1F 梁 | 屋頂梁 |
|------|-------|--------|
| 端 \(M\)（\| \|） | 157.1 kN·m | 142.1 kN·m |
| 跨中 \(M\) | 94.3 kN·m | 109.3 kN·m |
| 端 \(V\) | 167.6 kN | 167.6 kN |

---

## 6. 斜率撓度法（無側移）

### 6.1 基本式

\[
M_{ab}=M_{ab}^{F}+\frac{4EI}{L}\theta_a+\frac{2EI}{L}\theta_b-\frac{6EI}{L}\psi
\]

令 \(S=EI/L\)。均布載重：

\[
M^{F}=\frac{wL^{2}}{12}
\]

C1 對稱重力 → \(\psi=0\)，\(\theta_4=-\theta_3\)，\(\theta_6=-\theta_5\)。

### 6.2 平衡式

\[
\begin{aligned}
(8S_c+2S_b)\theta_3+2S_c\theta_5&=-M_F\\
2S_c\theta_3+(4S_c+2S_b)\theta_5&=-M_F
\end{aligned}
\]

### 6.3 封閉解（SymPy）

\[
\theta_3=\frac{M_F(-S_b-S_c)}{2(S_b^{2}+6S_b S_c+7S_c^{2})},\quad
\theta_5=\frac{M_F(-S_b-3S_c)}{2(S_b^{2}+6S_b S_c+7S_c^{2})}
\]

\[
M_{34}=\frac{M_F\,S_c(5S_b+7S_c)}{S_b^{2}+6S_b S_c+7S_c^{2}}
\]

### 6.4 數值（C1）

\(S_c=10508.8\)，$S_b=4489.8$，$M_F=167.61$ kN·m，$w=55.869$ kN/m

| 量 | 斜率撓度 | OpenSees |
|----|----------|----------|
| 1F 梁端 \(M\) | 157.12 | 157.09 |
| 跨中 \(M=wL^2/8-\|M_{\mathrm{end}}\|\) | 94.29 | 94.28 |

---

## 7. 斜率撓度法（有側移）

### 7.1 未知數（6 個）

\[
\theta_3,\theta_4,\theta_5,\theta_6,\quad
\psi_1=\frac{\Delta_1}{h},\quad
\psi_2=\frac{\Delta_2-\Delta_1}{h}
\]

梁不計軸變 → 梁 \(\psi=0\)；柱弦轉角 = 該層 \(\psi\)。

### 7.2 方程式組成

- **4** 條節點 \(\sum M=0\)（含 \(-6S\psi\)）
- **2** 條層剪力平衡：

\[
\frac{\sum(M_{\mathrm{底}}+M_{\mathrm{頂}})}{h}+F_{\mathrm{storey}}=0
\]

### 7.3 C3 數值驗證（側移）

\(F_1=-13.94\) kN，$F_2=-22.31$ kN，$w=25.02$ kN/m

| 項目 | 手算 SD | OpenSees |
|------|---------|----------|
| 1F 側移 | −3.97 mm | −4.00 mm |
| 屋頂側移 | −8.79 mm | −8.80 mm |

\(F_1=F_2=0\) 時 \(\psi\to0\)，退回無側移解（健全性檢查）。

**考試提示**：有側移一般列式 + 計算機解 6×6；封閉手算宜改考單層門架。

---

## 8. RC 梁：\(M_u\)、\(M_n\)、\(\phi\)

### 8.1 定義

\[
\phi M_n \ge M_u
\]

- \(M_u\)：組合後需求  
- \(M_n=A_s f_y(d-a/2)\)，$a=A_s f_y/(0.85f_c'b)$  
- \(\varepsilon_t=0.003(d_t-c)/c$，$c=a/\beta_1$  
- \(\varepsilon_t\ge0.005\Rightarrow\phi=0.90\)

### 8.2 1F 梁示例（\(M_u=157.1\) kN·m）

- 選 4-#6(D19)，$A_s=11.46$ cm²，$d=43.8$ cm  
- \(M_n=190.8$ kN·m，$\phi M_n=171.7$ kN·m  
- **Utilization = 91.5%（合格）**

---

## 9. RC 柱：P–M 互制

柱容量為曲線，不是單一 \(M_n\)。試排 \(\rho=0.02\)（3+2+3）：

| 柱組 | 檢查點 | Utilization | 包絡內 |
|------|--------|-------------|--------|
| 1F | (354 kN, 50 kN·m) | 25.5% | Yes |
| 2F | (186 kN, 142 kN·m) | 67.5% | Yes |

橫箍柱 \(\phi\)：$0.65\sim0.90$（依 \(\varepsilon_t\)）。

---

## 10. 梁剪力與箍筋

\[
\phi(V_c+V_s)\ge V_u,\quad \phi=0.75
\]

\[
V_c=0.53\sqrt{f_c'}\,b\,d\quad(\mathrm{kgf,cm})
\]

\[
s=\frac{A_v f_{yt} d}{V_s},\quad
s_{\max}=\min(d/2,\,60\,\mathrm{cm})
\]

1F 梁 $V_u=167.6$ kN、雙肢 #3 → **$s=20$ cm**（由 $d/2$ 控制）。

---

## 11. 構件分組與尚未完成項目

- **L+R envelope**：對稱構架同一樓層柱同筋。  
- Stage 3 **尚未做**：迭代最經濟配筋、強柱弱梁 \(\sum M_{nc}\ge1.2\sum M_{nb}\)、capacity design shear、完整 3D。

---

# 第二部　練習題（含詳解）

> 建議配分僅供組卷參考。答案緊接各題，便於自學；若作考試卷請自行撕開詳解。

---

## 練習題 1　荷載組合與 Governing（15 分）

**題目**  
已知 $D_{\mathrm{udl}}=23.83$ kN/m，$L_{\mathrm{udl}}=13.24$ kN/m。  
(1) 寫出 C1 並計算梁上 $w_u$。  
(2) 何謂 governing load combination？為何不能把「最大軸力」與「最大彎矩」取自不同組合拼成設計點？

### 詳解

**(1)**  
\[
w_u=1.4\times23.83+1.7\times13.24=33.362+22.508=\mathbf{55.87\,\mathrm{kN/m}}
\]

**(2)**  
Governing = 使該需求量絕對值最大、且**對應真實同時發生之載重狀態**的組合，並記錄名稱。  
硬湊 max $N$ 與 max $M$ 可能對應不到任一規範組合，導致不安全或無物理意義的需求點。

**評分**：C1 式與數值 8 分；governing 定義與禁止硬湊 7 分。

---

## 練習題 2　無側移斜率撓度求 $M_u$（25 分）

**題目**  
$L=6$ m，$h=3.5$ m，$S_c=10508.8$ kN·m，$S_b=4489.8$ kN·m，$w_u=55.869$ kN/m。  
僅重力、無側移、對稱。  
(1) 計算 $M_F$。  
(2) 寫出 $\theta_3,\theta_5$ 的平衡方程式。  
(3) 已知封閉式  
$M_{34}=M_F S_c(5S_b+7S_c)/(S_b^2+6S_b S_c+7S_c^2)$，  
求 1F 梁端 $M_u$ 與跨中 $M_u$。

### 詳解

**(1)**  
\[
M_F=\frac{55.869\times36}{12}=\mathbf{167.61\,\mathrm{kN\cdot m}}
\]

**(2)**  
\[
\begin{aligned}
(8S_c+2S_b)\theta_3+2S_c\theta_5&=-M_F\\
2S_c\theta_3+(4S_c+2S_b)\theta_5&=-M_F
\end{aligned}
\]

**(3)**  
代入 $S_c,S_b,M_F$：  
\[
M_{34}=\mathbf{157.12\,\mathrm{kN\cdot m}}
\]
\[
M_{\mathrm{mid}}=\frac{wL^2}{8}-157.12=251.41-157.12=\mathbf{94.29\,\mathrm{kN\cdot m}}
\]

**評分**：FEM 5；平衡式 8；端矩 7；跨中 5。

---

## 練習題 3　有側移觀念（15 分）

**題目**  
(1) 有側移時 2 層 1 跨框架斜率撓度有幾個未知數？各是什麼？  
(2) 除節點 $\sum M=0$ 外還需要哪類方程式？  
(3) 若令側向力 $F_1=F_2=0$，系統應退化成什麼結果？

### 詳解

**(1)** 六個：$\theta_3,\theta_4,\theta_5,\theta_6,\psi_1,\psi_2$。  

**(2)** **層剪力平衡**（各層 $\sum V=F_{\mathrm{storey}}$），共 2 條。  

**(3)** $\psi_1,\psi_2\to0$，且恢復對稱 $\theta_4=-\theta_3$ 等，退回無側移解（例如 $M_{34}=157.12$）。

**評分**：每小題 5 分。

---

## 練習題 4　單筋梁 $\phi M_n$（20 分）

**題目**  
梁 $b=30$ cm，$d=43.8$ cm，$f_c'=280$，$f_y=4200$（kgf/cm²）。  
$M_u=157.1$ kN·m。已選 4-#6，$A_s=11.46$ cm²。  
求 $a$、$M_n$、$\varepsilon_t$、$\phi$、$\phi M_n$，並判定是否合格。  
（$\beta_1=0.85$；1 kN·m $=10^5/9.80665$ kgf·cm）

### 詳解

\[
a=\frac{11.46\times4200}{0.85\times280\times30}=6.74\,\mathrm{cm}
\]

\[
M_n=11.46\times4200\times(43.8-6.74/2)\times9.80665\times10^{-5}=\mathbf{190.8\,\mathrm{kN\cdot m}}
\]

\[
c=a/0.85=7.93\,\mathrm{cm},\quad
\varepsilon_t=0.003\frac{43.8-7.93}{7.93}=0.0136>0.005
\]

\[
\phi=0.90,\quad
\phi M_n=171.7\,\mathrm{kN\cdot m}>157.1\quad\Rightarrow\quad
\text{utilization}=91.5\%\ \mathbf{合格}
\]

**評分**：各步驟約 4 分。

---

## 練習題 5　柱 P–M 檢核（15 分）

**題目**  
同一 40×40 cm 柱，$\rho=0.02$ 試排。  
(1) 為何柱不能只用單一 $M_n$ 與梁一樣設計？  
(2) 1F 點 $(P_u,M_u)=(354\,\mathrm{kN},\,50\,\mathrm{kN\cdot m})$ utilization 約 25.5%；  
2F 點 $(186,142)$ 約 67.5%。何者較臨界？為什麼？

### 詳解

**(1)** 軸力改變中性軸與破壞模式，容量是 **$P_n$–$M_n$ 曲線**（再乘 $\phi$），需求點須落在包絡內。  

**(2)** **2F 較臨界**（利用率較高）：軸力較低而彎矩較大，點較靠近彎矩側包絡。

**評分**：(1) 8 分；(2) 7 分。

---

## 練習題 6　箍筋間距（15 分）

**題目**  
$V_u=167.6$ kN，$b=30$ cm，$d=43.8$ cm，$f_c'=280$，$f_{yt}=4200$。  
雙肢箍 #3，$A_v=1.426$ cm²，$\phi=0.75$。  
$V_c=0.53\sqrt{f_c'}\,bd$（kgf）。求 $V_c$、$V_s$、計算 $s$ 與採用 $s$。

### 詳解

\[
V_c=0.53\times\sqrt{280}\times30\times43.8/101.97\approx\mathbf{114.3\,\mathrm{kN}}
\]

\[
V_s=\frac{167.6}{0.75}-114.3=\mathbf{109.2\,\mathrm{kN}}
\]

\[
s=\frac{1.426\times4200\times43.8}{109.2\times10^3/9.80665}\approx23.6\,\mathrm{cm}
\]

\[
s_{\max}=\min(d/2,60)=21.9\,\mathrm{cm}\Rightarrow\text{採用 }\mathbf{s=20\,\mathrm{cm}}
\]

**評分**：各 3～4 分；取構造上限 3 分。

---

## 練習題 7（進階）　綜合問答（10 分）

**題目**  
(1) 為何 1F 左右柱合成「柱組」取 envelope？  
(2) 列出至少三項 Stage 3 之後仍應完成的設計工作。

### 詳解

**(1)** 幾何對稱、施工統一配筋；地震使左右不對稱時用包絡覆蓋。  

**(2)** 任意三項即可：迭代經濟配筋；強柱弱梁 $1.2$；塑鉸區／capacity shear；錨定與構造；3D 模型等。

---

# 第三部　公式速查

\[
\begin{align*}
w_u&=1.4D+1.7L\\
M^{F}&=\frac{wL^{2}}{12},\quad S=\frac{EI}{L}\\
M_{ab}&=M^{F}+4S\theta_a+2S\theta_b-6S\psi\\
M_n&=A_sf_y\Bigl(d-\frac{a}{2}\Bigr),\quad a=\frac{A_sf_y}{0.85f_c'b}\\
\phi&=0.90\ (\varepsilon_t\ge0.005)\\
\phi(V_c+V_s)&\ge V_u,\quad V_c=0.53\sqrt{f_c'}\,bd
\end{align*}
\]

---

# 第四部　組卷建議（六題卷）

| 題號 | 內容 | 建議配分 |
|------|------|----------|
| 1 | 組合與 governing | 15% |
| 2 | 無側移斜率撓度 $M_u$ | 25% |
| 3 | 有側移觀念 | 10% |
| 4 | 梁 $\phi M_n$ | 20% |
| 5 | 柱 P–M | 15% |
| 6 | 箍筋 $s$ | 15% |

進階可加練習題 7 或改一題為「列出有側移 6 方程（不求解）」。

---

**文件結束**  
數字與 Stage 3 notebook / OpenSees 重算一致（梁端 157.1、utilization 柱 25.5%／67.5% 等）。若課堂使用 OpenSees，建議以本講義手算 C1 梁端矩作交叉驗證。

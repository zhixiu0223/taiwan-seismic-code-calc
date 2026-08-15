# 台灣耐震規範計算 (Taiwan Seismic Code Calc)

[![Execute notebook & verify results](https://github.com/zhixiu0223/taiwan-seismic-code-calc/actions/workflows/execute-notebook.yml/badge.svg)](https://github.com/zhixiu0223/taiwan-seismic-code-calc/actions/workflows/execute-notebook.yml)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/seismic_design_2story_8col.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 這是針對台灣耐震規範進行自動化計算與驗證的專案。

依 [ROADMAP.md](ROADMAP.md) 的漸進式驗證規劃,由簡單案例逐步累加複雜度。

---

## 📁 專案內容

### 法規計算(Case-04 的前置輸入,非編號序列本身)

* [2層樓8柱RC構架耐震設計(桃園案例法規計算)](notebooks/seismic_design_2story_8col.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/seismic_design_2story_8col.ipynb)

### Stage 序列(Taoyuan Design Pipeline)

跟 Case/VL 序列平行的第三個分類,定位是把桃園案例現有的斷面來源混亂
(40cm/20cm/25cm 三個互不銜接的答案)收斂成單一可追溯主線:規範地震力
→ 初步試設 → 真梁真柱彈性模型 → Pu/Mu/Vu 抽取 → 分組 → RC 設計 →
強柱弱梁檢核 → 獨立驗證 → **DESIGN FREEZE** → 塑鉸/纖維參數 → 非線性
側推 → 性能檢核。完整 Stage 0~9 定義、跟既有 Case 的映射表、歷史斷面
archaeology 見 [ROADMAP.md](ROADMAP.md#stage-序列taoyuan-design-pipeline跟-casevl-序列平行的第三個分類)。

Stage 0(規範地震力)、Stage 1(初步試設)沿用既有的
`seismic_design_2story_8col.ipynb`/`case03_5_trial_sizing.ipynb`,
不需要新檔案。

* [Stage 2:Canonical Elastic Model(第一版)——Y向1跨2柱構架,真梁真柱+規範勁度折減,OpenSeesPy/PyNite雙工具交叉驗證](notebooks/stage2_canonical_elastic_model.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/stage2_canonical_elastic_model.ipynb)
* [Stage 3:完整荷載組合+Demand Extraction+構件分組——重新推導D/L(真實從屬寬度+結構計算書真實單位重量),6組合跑完,governing combination可追溯,含Stage 4搶先預覽(配筋+P-M檢核+配筋圖)](notebooks/stage3_load_combinations_demand_extraction.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/stage3_load_combinations_demand_extraction.ipynb)
* [Stage 3.01:延伸講義+可重跑計算本(斜率撓度法交叉驗證](notebooks/stage3_01_lecture_vm_pm_slope_deflection.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/stage3_01_lecture_vm_pm_slope_deflection.ipynb)

### Case 序列

* [Case-01:單自由度 SDOF 驗證](notebooks/case01_sdof.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case01_sdof.ipynb)
* [Case-02:一跨一層構架驗證通過](notebooks/case02_one_bay_one_story.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case02_one_bay_one_story.ipynb)
* [Case-02.5:反曲點法+虛功法通過](notebooks/case02_5_portal_virtual_work.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case02_5_portal_virtual_work.ipynb)
* [Case-02.6:反曲點法U形誤差曲線,建立FrameModel+Solver可抽換平台](notebooks/case02_6_portal_method_height_effect.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case02_6_portal_method_height_effect.ipynb)
* [Case-03:一跨二層構架驗證通過](notebooks/case03_one_bay_two_story.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_one_bay_two_story.ipynb)
* [Case-03.5:試設斷面(Trial Sizing)](notebooks/case03_5_trial_sizing.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_5_trial_sizing.ipynb)
* [Case-03.6:快速強度檢核](notebooks/case03_6_quick_strength_check.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_6_quick_strength_check.ipynb)
* [Case-03.6b:快速強度檢核-抽換檢核界面-鋼結構示範](notebooks/case03_6b_check_module_swap_demo.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_6b_check_module_swap_demo.ipynb)
* [Case-03.7:Demand物件與Design Loop](notebooks/case03_7_demand_design_loop.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_7_demand_design_loop.ipynb)
* [Case-04:桃園案例(X向3跨+Y向1跨真實構架)](notebooks/case04_taoyuan_case.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case04_taoyuan_case.ipynb)
* [Case-04.5:真梁模型驗證,量化剪力構架假設的有效範圍](notebooks/case04_5_real_frame_validation.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case04_5_real_frame_validation.ipynb)
* [Case-04.6:第三方工具交叉驗證(PyNite)](notebooks/case04_6_third_party_verification.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case04_6_third_party_verification.ipynb)
* [Case-05:真正的3D模型,X向Y向真正耦合在同一模型](notebooks/case05_3d_model.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case05_3d_model.ipynb)
* [Case-06:RC Fiber Section彎矩-曲率與P-M交互作用圖驗證](notebooks/case06_fiber_pm_interaction.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case06_fiber_pm_interaction.ipynb)
* [Case-06.5:完整2層樓框架V-Delta側推+真正的FEMA356/ASCE41](notebooks/case06_5_frame_pushover_fema273.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case06_5_frame_pushover_fema273.ipynb)
* [Case-06.6:梁柱都用真實配筋的完整框架推覆分析](notebooks/case06_6_real_reinforced_frame.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case06_6_real_reinforced_frame.ipynb)
* [Case-07:反應譜分析+振態分析+ACI有效勁度](notebooks/case07_response_spectrum_atc40.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case07_response_spectrum_atc40.ipynb)
* [Case-07.5:轉換斷面與纖維積分理論對照(教學版)](notebooks/case07_5_transformed_vs_fiber_theory.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case07_5_transformed_vs_fiber_theory.ipynb)
* [Case-08.1:矩形單筋梁撓曲設計(鋼筋配置系列起手式)](notebooks/case08_1_rectangular_beam_design.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case08_1_rectangular_beam_design.ipynb)
* [Case-08.2:雙筋梁+T形梁設計(含雙層排筋幾何)](notebooks/case08_2_doubly_reinforced_Tbeam.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case08_2_doubly_reinforced_Tbeam.ipynb)
* [Case-08.3:梁剪力設計](notebooks/case08_3_shear_design.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case08_3_shear_design.ipynb)
* [Case-08.4:柱軸力彎矩設計(P-M 互制)](notebooks/case08_4_column_PM_design.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case08_4_column_PM_design.ipynb)

### 驗證紀錄(Validation Logs)

跟 Case 序列平行的獨立分類,不是 Case 序列的延伸——記錄「發現數字
對不上→往下挖→找到根因」的診斷過程。VL-01~07 目前寫在各自對應的
Case notebook 裡面(見 [ROADMAP.md](ROADMAP.md) 的 VL 對照表);
VL-08 是第一個獨立成檔的驗證紀錄,因為它同時驗證 Case-08.1 跟
Case-08.2 兩者,不適合塞進其中任何一個:

* [VL-08:concreteproperties 第三方交叉驗證 design_rebar()/design_Tbeam()](notebooks/VL-08_concreteproperties_crosscheck.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/VL-08_concreteproperties_crosscheck.ipynb)
* [VL-12:建立VL-12構件層級跨solver交叉驗證(OpenSeesPy vs PyNite)](notebooks/VL-12_openseespy_pynite_hinge_crosscheck.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/VL-12_openseespy_pynite_hinge_crosscheck.ipynb)
* [VL-13:無圍束纖維斷面vs Whitney等效矩形應力塊跨方法論驗證](notebooks/VL-13_unconfined_fiber_vs_whitney_block.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/VL-13_unconfined_fiber_vs_whitney_block.ipynb)
* [VL-14:梁真實配筋設計, 揭露1F樓板梁嚴重超載的重大警訊](notebooks/VL-14_beam_real_rebar_design.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/VL-14_beam_real_rebar_design.ipynb)
* VL-15:Stage 2 canonical elastic model 跨solver驗證(OpenSeesPy vs PyNite),11項全數0.0000%誤差一致——見上方 Stage 序列的
  [`stage2_canonical_elastic_model.ipynb`](notebooks/stage2_canonical_elastic_model.ipynb)(未獨立成檔,記錄併在同一個notebook裡)
* VL-16:Stage 3 重力載重重新推導(真實從屬寬度+結構計算書真實單位重量) vs Stage 2 反推值,發現24.7%落差並如實記錄;governing combination追溯+柱設計utilization取最差值(非分別取N/M最大值硬湊)——見
  [`stage3_load_combinations_demand_extraction.ipynb`](notebooks/stage3_load_combinations_demand_extraction.ipynb)(未獨立成檔)

完整規劃(Case 序列全貌、FEMA273/ATC-40 定位、與姐妹專案
[reproducible-structural-benchmarks](https://github.com/zhixiu0223/reproducible-structural-benchmarks)
的分工)見 [ROADMAP.md](ROADMAP.md)。

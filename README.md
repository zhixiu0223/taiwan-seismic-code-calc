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
* [Case-07:反應譜分析+振態分析+ACI有效勁度](notebooks/case07_response_spectrum_atc40.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case07_response_spectrum_atc40.ipynb)
* [Case-07.5:轉換斷面與纖維積分理論對照(教學版)](notebooks/case07_5_transformed_vs_fiber_theory.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case07_5_transformed_vs_fiber_theory.ipynb)
* [Case-08.1:矩形單筋梁撓曲設計(鋼筋配置系列起手式)](notebooks/case08_1_rectangular_beam_design.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case08_1_rectangular_beam_design.ipynb)

完整規劃(Case 序列全貌、FEMA273/ATC-40 定位、與姐妹專案
[reproducible-structural-benchmarks](https://github.com/zhixiu0223/reproducible-structural-benchmarks)
的分工)見 [ROADMAP.md](ROADMAP.md)。

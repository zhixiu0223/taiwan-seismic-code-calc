# 台灣耐震規範計算 (Taiwan Seismic Code Calc)

[![Execute notebook & verify results](https://github.com/zhixiu0223/taiwan-seismic-code-calc/actions/workflows/execute-notebook.yml/badge.svg)](https://github.com/zhixiu0223/taiwan-seismic-code-calc/actions/workflows/execute-notebook.yml)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/seismic_design_2story_8col.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 這是針對台灣耐震規範進行自動化計算與驗證的專案。

依 [ROADMAP.md](ROADMAP.md) 的漸進式驗證規劃,由簡單案例逐步累加複雜度。

---

## 📁 專案內容

* [Case-01:單自由度 SDOF 驗證](notebooks/case01_sdof.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case01_sdof.ipynb)
* [Case-02:一跨一層構架驗證通過](notebooks/case02_one_bay_one_story.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case02_one_bay_one_story.ipynb)
* [Case-03:一跨二層構架驗證通過](notebooks/case03_one_bay_two_story.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_one_bay_two_story.ipynb)
* [Case-03.5:試設斷面(Trial Sizing)](notebooks/case03_5_trial_sizing.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_5_trial_sizing.ipynb)
* [Case-03.6:快速強度檢核](notebooks/case03_6_quick_strength_check.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_6_quick_strength_check.ipynb)
* [Case-03.6b:快速強度檢核-抽換檢核界面-鋼結構示範](notebooks/case03_6b_check_module_swap_demo.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/case03_6b_check_module_swap_demo.ipynb)
* [Case-04:2層樓8柱RC構架耐震設計(桃園案例)](notebooks/seismic_design_2story_8col.ipynb)
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zhixiu0223/taiwan-seismic-code-calc/blob/main/notebooks/seismic_design_2story_8col.ipynb)

完整規劃(Case-01~08、FEMA273/ATC-40 定位、與姐妹專案
[reproducible-structural-benchmarks](https://github.com/zhixiu0223/reproducible-structural-benchmarks)
的分工)見 [ROADMAP.md](ROADMAP.md)。

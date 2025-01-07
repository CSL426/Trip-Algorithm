# 🗺️ 智能行程規劃系統

這是一個專門為台北旅遊設計的智能行程規劃系統。系統能根據使用者的時間限制、交通方式和個人喜好，自動生成最佳的一日遊行程。透過改良的貪婪演算法，在考量多項限制條件的情況下，為使用者規劃出最合適的旅遊路線。

## 系統特色

### 智能規劃
- 自動考慮景點間的最佳路線
- 依照時段動態調整規劃策略（早上→午餐→下午→晚餐→夜晚）
- 智能判斷並安排用餐時機
- 優化整體行程效率

### 時間管理
- 全天候動態規劃（支援 00:00-23:59）
- 自動考慮景點營業時間
- 智能分配景點停留時間
- 預留適當的交通時間緩衝

### 交通整合
- 支援多種交通方式（大眾運輸、開車、步行）
- 即時路線規劃與時間估算
- 整合 Google Maps 路線資訊
- 自動計算轉乘建議

### 個人化設定
- 自訂起點和終點位置
- 調整遊玩時間偏好
- 設定餐飲選項偏好
- 自訂景點停留時間

## 安裝說明

### 系統需求
- Python 3.9 或以上版本
- Poetry 套件管理工具
- 穩定的網路連線（需要存取 Google Maps API）

### 安裝步驟

1. 複製專案到本地：
```bash
git clone https://github.com/csl426/Trip-Algorithm.git
cd Trip-algorithm
```

2. 使用 Poetry 安裝相依套件：
```bash
poetry install
```

3. 在 config.py 或 .env 中設定你的 Google Maps API 金鑰

## 使用說明

### 基本使用方式
``` python
from src.core import TripPlanner

# 建立規劃器實例
planner = TripPlanner()

# 設定景點資訊
locations = [
    {
        'name': '台北101',
        'rating': 4.6,
        'lat': 25.0339808,
        'lon': 121.561964,
        'duration': 150,  # 參訪時間（分鐘）
        'label': '景點',
        'period': 'morning',
        'hours': {  # 營業時間
            1: [{'start': '09:00', 'end': '22:00'}],  # 週一
            # ... 其他日期的營業時間
        }
    }
]

# 執行規劃
itinerary = planner.plan(
    locations=locations,
    start_time='09:00',
    end_time='18:00',
    travel_mode='driving',
    custom_start={
        'name': '台北車站',
        'lat': 25.0478,
        'lon': 121.5170
    }
)
```

### 進階設定

本系統提供多項進階設定選項，讓您能更精確地控制行程規劃：

``` python
# 自訂規劃參數
itinerary = planner.plan(
    locations=locations,
    start_time='09:00',
    end_time='18:00',
    travel_mode='driving',     # 交通方式：driving, transit, walking
    distance_threshold=30,     # 最大可接受距離（公里）
    efficiency_threshold=0.1,  # 效率評分門檻
    custom_start=start_point,  # 自訂起點
    custom_end=end_point      # 自訂終點
)
```

## 系統架構

```
Trip_algorithm/
├── src/
│   ├── core/           # 核心功能模組
│   │   ├── models/    # 資料模型
│   │   ├── planner/   # 規劃邏輯
│   │   ├── services/  # 外部服務
│   │   └── utils/     # 工具函式
│   └── config/        # 設定檔
└── tests/             # 測試程式
```

## 演算法說明

系統使用改良的貪婪演算法進行行程規劃，主要考量以下因素：

1. 時段適合度：依據時間選擇合適的景點類型
2. 地理位置：計算交通成本與距離合理性
3. 景點評分：綜合考量景點的評價與熱門程度
4. 時間規劃：合理分配停留時間與交通時間
5. 用餐安排：在適當時間點安排用餐地點

## 常見問題

**Q: 如何調整景點停留時間？**  
A: 在景點資訊中設定 \`duration\` 參數，單位為分鐘。

**Q: 是否支援多日行程？**  
A: 目前版本專注於單日行程規劃，多日行程規劃功能正在開發中。

**Q: 如何處理特殊的營業時間？**  
A: 系統支援複雜的營業時間設定，包含午休時間和分段營業。

## 版本紀錄

- v0.1.0 (2024/01)
  - 首次發布
  - 基本行程規劃功能
  - 整合 Google Maps API

## 授權資訊

本專案採用 MIT 授權條款，詳細內容請參閱 LICENSE 檔案。

## 開發團隊 - 路遊憩

如有任何問題或建議，歡迎透過以下方式聯繫：
- Email: spark.cs.liao@gmail.com
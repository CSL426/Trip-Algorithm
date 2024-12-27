# 智能行程規劃系統

這是一個專門為台北旅遊設計的智能行程規劃系統。系統能根據使用者的時間限制、交通方式和個人喜好，自動生成最佳的一日遊行程。

## 系統特色

我們的系統提供了許多強大的功能：

### 智能規劃
- 自動考慮景點間的最佳路線
- 動態調整行程順序以優化時間利用
- 根據不同時段調整景點選擇策略
- 自動安排合適的用餐時間

### 時間管理
- 全天候動態規劃)支援 00:00-23:59)
- 自動考慮景點營業時間
- 智能分配景點停留時間
- 預留適當的交通時間緩衝

### 交通整合
- 支援多種交通方式)大眾運輸、開車、步行)
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
- 穩定的網路連線)需要存取 Google Maps API)

### 安裝步驟

1. 複製專案到本地：
```bash
git clone https://github.com/your-username/Trip-Algorithm.git
cd Trip-Algorithm
```

2. 使用 Poetry 安裝相依套件：
```bash
poetry install
```

3. 設定環境：
```bash
cp src/config/config_example.py src/config/config.py
```

4. 在 config.py 中設定你的 Google Maps API 金鑰

## 使用說明

### 基本使用方式
```python
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
        'duration': 150,  # 參訪時間)分鐘)
        'label': '景點',
        'hours': {  # 營業時間
            1: [{'start': '09:00', 'end': '22:00'}],
            # ... 其他日期的營業時間
        }
    },
    # ... 其他景點
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

```python
# 自訂規劃參數
itinerary = planner.plan(
    locations=locations,
    start_time='09:00',
    end_time='18:00',
    travel_mode='driving',     # 交通方式：driving, transit, walking
    distance_threshold=30,     # 最大可接受距離)公里)
    efficiency_threshold=0.1,  # 效率評分門檻
    custom_start=start_point,  # 自訂起點
    custom_end=end_point      # 自訂終點
)
```

## 專案結構

```
Trip_Algorithm/
├── src/
│   ├── api/            # API 端點
│   ├── config/         # 設定檔
│   ├── core/           # 核心演算法
│   │   ├── planners/   # 規劃器模組
│   │   └── utils/      # 工具函式
│   └── line/           # LINE 訊息格式化
└── tests/              # 測試程式
```

## 演算法說明

我們的系統使用了改良的貪婪演算法，結合了多項優化策略：

1. 多階段評分：考慮距離、時間和效率等多個面向
2. 動態權重調整：根據時段自動調整選擇策略
3. 智能時間分配：自動調整停留時間和交通時間
4. 即時路線最佳化：持續優化整體行程效率

## 常見問題

**Q: 如何調整景點停留時間？**
A: 在景點資訊中設定 `duration` 參數，單位為分鐘。

**Q: 是否支援多日行程？**
A: 目前版本專注於單日行程規劃，多日行程規劃功能正在開發中。

**Q: 如何處理特殊的營業時間？**
A: 系統支援複雜的營業時間設定，包含午休時間和分段營業。

## 版本歷程

- v1.0.0 (2024/12)
  - 首次發布
  - 基本行程規劃功能
  - LINE Bot 整合

## 授權資訊

本專案採用 MIT 授權條款，詳細內容請參閱 LICENSE 檔案。

## 貢獻指南

我們歡迎各種形式的貢獻，包括但不限於：
- 錯誤回報
- 功能建議
- 程式碼優化
- 文件改善

## 聯絡資訊

如有任何問題或建議，歡迎透過以下方式聯繫：
- GitHub Issues
- Email: spark.cs.liao@gmail.com
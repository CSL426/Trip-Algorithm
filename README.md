# Trip-Algorithm

Trip Planner Project Structure:

TripPlanner.py (核心規劃邏輯)
- 負責行程演算法和規劃
- 呼叫 utils.py 計算時間和距離
- 使用 TripNode.py 組織和顯示行程

TripNode.py (資料結構)
- 使用鏈結串列儲存行程
- 處理行程資料的組織和顯示格式

utils.py (工具函式)
- 提供距離計算、時間估算等功能
- 處理 Google Maps API 呼叫
- 提供共用的輔助函式

config.py (API存放)
- 存放我的API-KEY
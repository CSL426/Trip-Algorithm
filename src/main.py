trip_plan = {
    0: {                             # key是行程順序
        "name": "我家",              # 地點名稱
        "start_time": "09:00",       # 到達該地點的時間
        "end_time": "09:00",         # 離開該地點的時間
        "duration": 0,               # 停留時間（分鐘）
        "transport": {               # 到達該地點的交通資訊
            "mode": "起點",          # 交通方式
            "time": 0,              # 交通時間（分鐘）
            "period": None          # 交通發生的時間區間
        }
    },
    1: {
        "name": "台北101",
        "start_time": "09:20",
        "end_time": "10:50",
        "duration": 90,
        "hours": "09:00-22:00",
        "transport": {
            "mode": "開車",
            "time": 20,
            "period": "09:00-09:20"
        }
    },
    2: {
        "name": "西門町",
        "start_time": "11:05",
        "end_time": "12:35",
        "duration": 90,
        "hours": "10:00-22:00",
        "transport": {
            "mode": "開車",
            "time": 15,
            "period": "10:50-11:05"
        }
    }
}
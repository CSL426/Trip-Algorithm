# data.py

"""測試用的景點資料

此模組包含以下資料：
1. TEST_LOCATIONS: 測試用的景點列表
2. TEST_CUSTOM_START: 測試用的自訂起點
3. TEST_REQUIREMENT: 測試用的行程需求
"""

# 測試用的自訂起點
TEST_CUSTOM_START = {
    'name': '台北車站',
    'lat': 24.9881309,
    'lon': 121.4606196,
    'hours': {
        1: [{'start': '00:00', 'end': '23:59'}],  # 全天開放
        2: [{'start': '00:00', 'end': '23:59'}],
        3: [{'start': '00:00', 'end': '23:59'}],
        4: [{'start': '00:00', 'end': '23:59'}],
        5: [{'start': '00:00', 'end': '23:59'}],
        6: [{'start': '00:00', 'end': '23:59'}],
        7: [{'start': '00:00', 'end': '23:59'}]
    }
}


# 測試用的行程需求
TEST_REQUIREMENT = {
    "start_time": "08:00",        # 開始時間
    "end_time": "21:00",          # 結束時間
    "start_point": "台北車站",     # 起點
    "end_point": "台北車站",       # 終點
    "transport_mode": "driving",   # 交通方式：大眾運輸
    "distance_threshold": 30,      # 距離限制：30公里
    "breakfast_time": "none",      # 不需要早餐
    "lunch_time": "11:00",        # 午餐時間
    "dinner_time": "18:00",       # 晚餐時間
    "budget": "none",             # 無預算限制
    "date": "12-25"              # 日期：12月25日
}

TEST_LOCATIONS = []
TEST_LOCATIONS.extend([
    {
        'name': '象山步道',
        'rating': 4.7,
        'lat': 25.027843,
        'lon': 121.570492,
        'duration': 120,
        'label': '景點',
        'period': 'morning',
        'url': 'https://www.dintaifung.com.tw/store/xinyi.php',
        'hours': {
            1: [{'start': '05:00', 'end': '18:00'}],
            2: [{'start': '05:00', 'end': '18:00'}],
            3: [{'start': '05:00', 'end': '18:00'}],
            4: [{'start': '05:00', 'end': '18:00'}],
            5: [{'start': '05:00', 'end': '18:00'}],
            6: [{'start': '05:00', 'end': '18:00'}],
            7: [{'start': '05:00', 'end': '18:00'}]
        }
    },
    {
        'name': '龍山寺',
        'rating': 4.6,
        'lat': 25.037509,
        'lon': 121.499962,
        'duration': 90,
        'label': '景點',
        'period': 'morning',
        'url': 'https://www.dintaifung.com.tw/store/xinyi.php',
        'hours': {
            1: [{'start': '06:00', 'end': '22:00'}],
            2: [{'start': '06:00', 'end': '22:00'}],
            3: [{'start': '06:00', 'end': '22:00'}],
            4: [{'start': '06:00', 'end': '22:00'}],
            5: [{'start': '06:00', 'end': '22:00'}],
            6: [{'start': '06:00', 'end': '22:00'}],
            7: [{'start': '06:00', 'end': '22:00'}]
        }
    },
    {
        'name': '陽明山花鐘',
        'rating': 4.5,
        'lat': 25.164007,
        'lon': 121.543366,
        'duration': 150,
        'label': '景點',
        'period': 'morning',
        'url': 'https://www.dintaifung.com.tw/store/xinyi.php',
        'hours': {
            1: [{'start': '05:00', 'end': '20:00'}],
            2: [{'start': '05:00', 'end': '20:00'}],
            3: [{'start': '05:00', 'end': '20:00'}],
            4: [{'start': '05:00', 'end': '20:00'}],
            5: [{'start': '05:00', 'end': '20:00'}],
            6: [{'start': '05:00', 'end': '20:00'}],
            7: [{'start': '05:00', 'end': '20:00'}]
        }
    },
    {
        'name': '二子坪步道',
        'rating': 4.6,
        'lat': 25.177685,
        'lon': 121.553123,
        'duration': 180,
        'label': '景點',
        'period': 'morning',
        'url': 'https://www.dintaifung.com.tw/store/xinyi.php',
        'hours': {
            1: [{'start': '08:00', 'end': '18:00'}],
            2: [{'start': '08:00', 'end': '18:00'}],
            3: [{'start': '08:00', 'end': '18:00'}],
            4: [{'start': '08:00', 'end': '18:00'}],
            5: [{'start': '08:00', 'end': '18:00'}],
            6: [{'start': '08:00', 'end': '18:00'}],
            7: [{'start': '08:00', 'end': '18:00'}]
        }
    },
    {
        'name': '北投溫泉博物館',
        'rating': 4.4,
        'lat': 25.136138,
        'lon': 121.503985,
        'duration': 100,
        'label': '景點',
        'period': 'morning',
        'url': 'https://www.dintaifung.com.tw/store/xinyi.php',
        'hours': {
            1: [{'start': '09:00', 'end': '17:00'}],
            2: [{'start': '09:00', 'end': '17:00'}],
            3: [{'start': '09:00', 'end': '17:00'}],
            4: [{'start': '09:00', 'end': '17:00'}],
            5: [{'start': '09:00', 'end': '17:00'}],
            6: [{'start': '09:00', 'end': '17:00'}],
            7: [{'start': '09:00', 'end': '17:00'}]
        }
    }
])

TEST_LOCATIONS.extend([
    {
        'name': '鼎泰豐 (信義店)',
        'rating': 4.7,
        'lat': 25.033976,
        'lon': 121.563105,
        'duration': 90,
        'label': '餐廳',
        'period': 'lunch',
        'url': 'https://www.dintaifung.com.tw/store/xinyi.php',
        'hours': {
            1: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            2: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            3: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            4: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            5: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            6: [{'start': '11:20', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            7: [{'start': '11:20', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}]
        }
    },
    {
        'name': '永康牛肉麵',
        'rating': 4.5,
        'lat': 25.033542,
        'lon': 121.529307,
        'duration': 60,
        'label': '餐廳',
        'period': 'lunch',
        'url': 'https://www.facebook.com/yongkangbeef/',
        'hours': {
            1: [{'start': '11:00', 'end': '21:00'}],
            2: [{'start': '11:00', 'end': '21:00'}],
            3: [{'start': '11:00', 'end': '21:00'}],
            4: [{'start': '11:00', 'end': '21:00'}],
            5: [{'start': '11:00', 'end': '21:00'}],
            6: [{'start': '11:00', 'end': '21:00'}],
            7: [{'start': '11:00', 'end': '21:00'}]
        }
    },
    {
        'name': '金峰魯肉飯',
        'rating': 4.4,
        'lat': 25.043614,
        'lon': 121.533132,
        'duration': 45,
        'label': '小吃',
        'period': 'lunch',
        'url': 'https://www.facebook.com/pages/金峰魯肉飯/179726945452938',
        'hours': {
            1: [{'start': '08:00', 'end': '20:00'}],
            2: [{'start': '08:00', 'end': '20:00'}],
            3: [{'start': '08:00', 'end': '20:00'}],
            4: [{'start': '08:00', 'end': '20:00'}],
            5: [{'start': '08:00', 'end': '20:00'}],
            6: [{'start': '08:00', 'end': '20:00'}],
            7: [{'start': '08:00', 'end': '20:00'}]
        }
    },
    {
        'name': '阜杭豆漿',
        'rating': 4.6,
        'lat': 25.044279,
        'lon': 121.529664,
        'duration': 45,
        'label': '早午餐',
        'period': 'lunch',
        'url': 'https://www.facebook.com/pages/阜杭豆漿/273272716106529',
        'hours': {
            1: [None],  # 週一公休
            2: [{'start': '05:30', 'end': '12:30'}],
            3: [{'start': '05:30', 'end': '12:30'}],
            4: [{'start': '05:30', 'end': '12:30'}],
            5: [{'start': '05:30', 'end': '12:30'}],
            6: [{'start': '05:30', 'end': '12:30'}],
            7: [{'start': '05:30', 'end': '12:30'}]
        }
    },
    {
        'name': '杭州小籠湯包',
        'rating': 4.3,
        'lat': 25.042057,
        'lon': 121.532708,
        'duration': 60,
        'label': '餐廳',
        'period': 'lunch',
        'url': 'https://www.facebook.com/pages/杭州小籠湯包/234274696679149',
        'hours': {
            1: [{'start': '10:30', 'end': '21:00'}],
            2: [{'start': '10:30', 'end': '21:00'}],
            3: [{'start': '10:30', 'end': '21:00'}],
            4: [{'start': '10:30', 'end': '21:00'}],
            5: [{'start': '10:30', 'end': '21:00'}],
            6: [{'start': '10:30', 'end': '21:00'}],
            7: [{'start': '10:30', 'end': '21:00'}]
        }
    }
])

# 下午景點
TEST_LOCATIONS.extend([
    {
        'name': '松山文創園區',
        'rating': 4.5,
        'lat': 25.043808,
        'lon': 121.560520,
        'duration': 120,
        'label': '景點',
        'period': 'afternoon',
        'url': 'https://www.songshanculturalpark.org/',
        'hours': {
            1: [{'start': '09:00', 'end': '18:00'}],
            2: [{'start': '09:00', 'end': '18:00'}],
            3: [{'start': '09:00', 'end': '18:00'}],
            4: [{'start': '09:00', 'end': '18:00'}],
            5: [{'start': '09:00', 'end': '18:00'}],
            6: [{'start': '09:00', 'end': '18:00'}],
            7: [{'start': '09:00', 'end': '18:00'}]
        }
    },
    {
        'name': '華山1914文化創意產業園區',
        'rating': 4.6,
        'lat': 25.044103,
        'lon': 121.529540,
        'duration': 150,
        'label': '景點',
        'period': 'afternoon',
        'url': 'https://www.huashan1914.com/',
        'hours': {
            1: [{'start': '09:00', 'end': '21:00'}],
            2: [{'start': '09:00', 'end': '21:00'}],
            3: [{'start': '09:00', 'end': '21:00'}],
            4: [{'start': '09:00', 'end': '21:00'}],
            5: [{'start': '09:00', 'end': '21:00'}],
            6: [{'start': '09:00', 'end': '21:00'}],
            7: [{'start': '09:00', 'end': '21:00'}]
        }
    },
    {
        'name': '四四南村',
        'rating': 4.3,
        'lat': 25.033717,
        'lon': 121.565075,
        'duration': 90,
        'label': '景點',
        'period': 'afternoon',
        'url': 'https://www.travel.taipei/zh-tw/attraction/details/1917',
        'hours': {
            1: [{'start': '09:00', 'end': '17:00'}],
            2: [{'start': '09:00', 'end': '17:00'}],
            3: [{'start': '09:00', 'end': '17:00'}],
            4: [{'start': '09:00', 'end': '17:00'}],
            5: [{'start': '09:00', 'end': '17:00'}],
            6: [{'start': '09:00', 'end': '18:00'}],
            7: [{'start': '09:00', 'end': '18:00'}]
        }
    },
    {
        'name': '台北當代藝術館',
        'rating': 4.3,
        'lat': 25.053333,
        'lon': 121.515833,
        'duration': 120,
        'label': '景點',
        'period': 'afternoon',
        'url': 'https://www.mocataipei.org.tw/',
        'hours': {
            1: [None],  # 週一休館
            2: [{'start': '10:00', 'end': '18:00'}],
            3: [{'start': '10:00', 'end': '18:00'}],
            4: [{'start': '10:00', 'end': '18:00'}],
            5: [{'start': '10:00', 'end': '18:00'}],
            6: [{'start': '10:00', 'end': '18:00'}],
            7: [{'start': '10:00', 'end': '18:00'}]
        }
    },
    {
        'name': '迪化街',
        'rating': 4.4,
        'lat': 25.057337,
        'lon': 121.510712,
        'duration': 120,
        'label': '景點',
        'period': 'afternoon',
        'url': 'https://www.travel.taipei/zh-tw/attraction/details/62',
        'hours': {
            1: [{'start': '10:00', 'end': '19:00'}],
            2: [{'start': '10:00', 'end': '19:00'}],
            3: [{'start': '10:00', 'end': '19:00'}],
            4: [{'start': '10:00', 'end': '19:00'}],
            5: [{'start': '10:00', 'end': '19:00'}],
            6: [{'start': '10:00', 'end': '19:00'}],
            7: [{'start': '10:00', 'end': '19:00'}]
        }
    }
])

# 晚餐地點
TEST_LOCATIONS.extend([
    {
        'name': '寧夏夜市',
        'rating': 4.3,
        'lat': 25.057944,
        'lon': 121.515417,
        'duration': 120,
        'label': '夜市',
        'period': 'dinner',
        'url': 'https://www.travel.taipei/zh-tw/attraction/details/1485',
        'hours': {
            1: [{'start': '17:00', 'end': '23:59'}],
            2: [{'start': '17:00', 'end': '23:59'}],
            3: [{'start': '17:00', 'end': '23:59'}],
            4: [{'start': '17:00', 'end': '23:59'}],
            5: [{'start': '17:00', 'end': '23:59'}],
            6: [{'start': '17:00', 'end': '23:59'}],
            7: [{'start': '17:00', 'end': '23:59'}]
        }
    },
    {
        'name': '饒河街觀光夜市',
        'rating': 4.2,
        'lat': 25.049994,
        'lon': 121.577139,
        'duration': 120,
        'label': '夜市',
        'period': 'dinner',
        'url': 'https://www.travel.taipei/zh-tw/attraction/details/72',
        'hours': {
            1: [{'start': '16:00', 'end': '23:59'}],
            2: [{'start': '16:00', 'end': '23:59'}],
            3: [{'start': '16:00', 'end': '23:59'}],
            4: [{'start': '16:00', 'end': '23:59'}],
            5: [{'start': '16:00', 'end': '23:59'}],
            6: [{'start': '16:00', 'end': '23:59'}],
            7: [{'start': '16:00', 'end': '23:59'}]
        }
    },
    {
        'name': '欣葉台菜(創始店)',
        'rating': 4.5,
        'lat': 25.047411,
        'lon': 121.527017,
        'duration': 90,
        'label': '餐廳',
        'period': 'dinner',
        'url': 'https://www.shinway.com.tw/',
        'hours': {
            1: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            2: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            3: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            4: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            5: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            6: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
            7: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}]
        }
    },
    {
        'name': '鼎王麻辣鍋(台北光復店)',
        'rating': 4.4,
        'lat': 25.042637,
        'lon': 121.552423,
        'duration': 120,
        'label': '餐廳',
        'period': 'dinner',
        'url': 'https://www.dwhot.com.tw/',
                'hours': {
                    1: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
                    2: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
                    3: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
                    4: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
                    5: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
                    6: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}],
                    7: [{'start': '11:30', 'end': '14:30'}, {'start': '17:30', 'end': '21:30'}]
                }
    },
    {
        'name': '橘色涮涮屋(市民店)',
        'rating': 4.6,
        'lat': 25.041818,
        'lon': 121.543623,
        'duration': 120,
        'label': '餐廳',
        'period': 'dinner',
        'url': 'https://www.facebook.com/OrangeTimeShabu/',
        'hours': {
            1: [{'start': '11:30', 'end': '23:00'}],
            2: [{'start': '11:30', 'end': '23:00'}],
            3: [{'start': '11:30', 'end': '23:00'}],
            4: [{'start': '11:30', 'end': '23:00'}],
            5: [{'start': '11:30', 'end': '23:00'}],
            6: [{'start': '11:30', 'end': '23:00'}],
            7: [{'start': '11:30', 'end': '23:00'}]
        }
    }
])

# 晚上景點
TEST_LOCATIONS.extend([
    {
        'name': '台北101觀景台',
        'rating': 4.7,
        'lat': 25.033194,
        'lon': 121.564837,
        'duration': 120,
        'label': '景點',
        'period': 'night',
        'url': 'https://www.taipei-101.com.tw/observatory-deck/',
        'hours': {
            1: [{'start': '13:00', 'end': '22:00'}],
            2: [{'start': '13:00', 'end': '22:00'}],
            3: [{'start': '13:00', 'end': '22:00'}],
            4: [{'start': '13:00', 'end': '22:00'}],
            5: [{'start': '13:00', 'end': '22:00'}],
            6: [{'start': '12:00', 'end': '22:00'}],
            7: [{'start': '12:00', 'end': '22:00'}]
        }
    },
    {
        'name': '信義商圈',
        'rating': 4.5,
        'lat': 25.033611,
        'lon': 121.563889,
        'duration': 150,
        'label': '商圈',
        'period': 'night',
        'url': 'https://www.travel.taipei/zh-tw/attraction/details/1572',
        'hours': {
            1: [{'start': '11:00', 'end': '22:00'}],
            2: [{'start': '11:00', 'end': '22:00'}],
            3: [{'start': '11:00', 'end': '22:00'}],
            4: [{'start': '11:00', 'end': '22:00'}],
            5: [{'start': '11:00', 'end': '22:00'}],
            6: [{'start': '11:00', 'end': '22:30'}],
            7: [{'start': '11:00', 'end': '22:00'}]
        }
    },
    {
        'name': '西門町',
        'rating': 4.3,
        'lat': 25.042057,
        'lon': 121.507470,
        'duration': 150,
        'label': '商圈',
        'period': 'night',
        'url': 'https://www.travel.taipei/zh-tw/attraction/details/1572',
        'hours': {
            1: [{'start': '11:00', 'end': '22:00'}],
            2: [{'start': '11:00', 'end': '22:00'}],
            3: [{'start': '11:00', 'end': '22:00'}],
            4: [{'start': '11:00', 'end': '22:00'}],
            5: [{'start': '11:00', 'end': '22:00'}],
            6: [{'start': '11:00', 'end': '23:00'}],
            7: [{'start': '11:00', 'end': '22:00'}]
        }
    },
    {
        'name': '美麗華摩天輪',
        'rating': 4.4,
        'lat': 25.083311,
        'lon': 121.556837,
        'duration': 60,
        'label': '景點',
        'period': 'night',
        'url': 'https://www.miramar.com.tw/brand/detail/71',
        'hours': {
            1: [{'start': '13:00', 'end': '22:00'}],
            2: [{'start': '13:00', 'end': '22:00'}],
            3: [{'start': '13:00', 'end': '22:00'}],
            4: [{'start': '13:00', 'end': '22:00'}],
            5: [{'start': '13:00', 'end': '22:30'}],
            6: [{'start': '12:00', 'end': '23:00'}],
            7: [{'start': '12:00', 'end': '22:00'}]
        }
    },
    {
        'name': '大稻埕碼頭',
        'rating': 4.3,
        'lat': 25.056389,
        'lon': 121.508333,
        'duration': 90,
        'label': '景點',
        'period': 'night',
        'url': 'https://www.travel.taipei/zh-tw/attraction/details/1537',
        'hours': {
            1: [{'start': '00:00', 'end': '23:59'}],  # 24小時開放
            2: [{'start': '00:00', 'end': '23:59'}],
            3: [{'start': '00:00', 'end': '23:59'}],
            4: [{'start': '00:00', 'end': '23:59'}],
            5: [{'start': '00:00', 'end': '23:59'}],
            6: [{'start': '00:00', 'end': '23:59'}],
            7: [{'start': '00:00', 'end': '23:59'}]
        }
    }
])




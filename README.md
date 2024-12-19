```markdown
# Trip Algorithm

智能行程規劃系統，根據輸入的景點資訊自動生成最佳行程。

## Features

- 自動規劃最佳行程路線
- 考慮景點營業時間
- 智能安排用餐時間
- 整合大眾運輸資訊
- LINE Bot 訊息輸出

## Requirements 

- Python 3.9+
- Poetry

## Installation

```bash
git clone <https://github.com/CSL426/Trip-Algorithm>
cd Trip_algorithm
poetry install
```
```

## Configuration

1. 複製 config 範本：
```bash
cp src/config/config_example.py src/config/config.py
```

2. 在 `config.py` 中設定你的 Google Maps API Key

## Usage

```python
from src.core import plan_trip

locations = [
    {
        'name': '台北101',
        'rating': 4.6,
        'lat': 25.0339808,
        'lon': 121.561964,
        'duration': 150,
        'label': '景點',
        'hours': '09:00 - 22:00'
    }
]

itinerary = plan_trip(
    locations=locations,
    start_time='09:00',
    end_time='21:00'
)
```

## Project Structure

```
Trip_algorithm/
├── src/
│   ├── api/          # API endpoints
│   ├── config/       # Configuration
│   ├── core/         # Core algorithm
│   └── line/         # LINE message formatter
└── tests/            # Tests
```

## License

MIT License
```

# src\core\utils\navigation_translator.py

"""導航文字轉換模組

此模組負責:
1. 英文導航指令轉中文
2. 路線資訊格式化
3. 導航文字清理
"""

from typing import Dict
import re


class NavigationTranslator:
    """導航文字轉換類別"""

    # 英文轉中文對照表
    DIRECTION_MAP = {
        ' on ': '沿著',
        ' onto ': '進入',
        'Head': '往',
        'Turn left': '左轉',
        'Turn right': '右轉',
        'Keep right': '靠右行駛',
        'Keep left': '靠左行駛',
        'Take the': '走上',
        'Merge': '匯入',
        'Continue': '繼續前進',
        'ramp': '匝道',
        'at the 1st cross street': '在第一個路口',
        'on the left': '(在左側)',
        'on the right': '(在右側)',
        'after': '經過',
        'before': '在...之前',
        'toward': '朝向',
        'Destination will be': '目的地位於',
        'south': '南',
        'north': '北',
        'east': '東',
        'west': '西',
        ' to ': '往',
        'stay on': '繼續走',
        'Huanhe N. Rd.': '環河北路',
        'Sanchong': '三重'
    }

    @classmethod
    def clean_html(cls, text: str) -> str:
        """清理HTML標記

        輸入參數:
            text: str - 包含HTML標記的文字

        回傳:
            str: 清理後的純文字
        """
        # 移除所有HTML標籤
        text = re.sub(r'<[^>]+>', '', text)
        # 移除多餘的空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @classmethod
    def translate_instruction(cls, text: str) -> str:
        """轉換單一導航指令

        輸入參數:
            text: str - 英文導航指令

        回傳:
            str: 中文導航指令
        """
        result = text

        # 進行翻譯轉換
        for eng, chi in cls.DIRECTION_MAP.items():
            result = result.replace(eng, chi)

        # 處理特殊格式
        result = result.replace('(在左側))', '(在左側)')
        result = result.replace('位於 (在左側)', '位於左側')

        # 調整語序
        result = result.replace('沿著 南', '往南沿著')

        return result.strip()

    @classmethod
    def format_distance(cls, distance: str) -> str:
        """格式化距離顯示

        輸入參數:
            distance: str - 原始距離文字

        回傳:
            str: 格式化後的距離文字
        """
        return distance.replace('km', '公里').replace('m', '公尺')

    @classmethod
    def format_duration(cls, duration: str) -> str:
        """格式化時間顯示

        輸入參數:
            duration: str - 原始時間文字

        回傳:
            str: 格式化後的時間文字
        """
        return duration.replace('mins', '分鐘').replace('min', '分鐘')

    @classmethod
    def format_navigation(cls, route_info: Dict) -> str:
        """格式化完整導航資訊

        輸入參數:
            route_info: Dict - Google Maps API回傳的路線資訊

        回傳:
            str: 格式化後的中文導航說明
        """
        if not route_info or 'steps' not in route_info:
            return "無法取得導航資訊"

        navigation_text = []
        for i, step in enumerate(route_info['steps'], 1):
            # 取得並轉換指令
            instruction = cls.clean_html(step.get('html_instructions', ''))
            instruction = cls.translate_instruction(instruction)

            # 處理距離和時間
            distance = cls.format_distance(
                step.get('distance', {}).get('text', ''))
            duration = cls.format_duration(
                step.get('duration', {}).get('text', ''))

            # 組合文字
            step_text = f"{i}. {instruction}"
            if distance:
                step_text += f"({distance}"
                if duration:
                    step_text += f"，約{duration})"
                else:
                    step_text += ")"

            navigation_text.append(step_text)

        # 加入總結資訊
        if 'legs' in route_info and route_info['legs']:
            leg = route_info['legs'][0]
            total_distance = cls.format_distance(
                leg.get('distance', {}).get('text', ''))
            total_duration = cls.format_duration(
                leg.get('duration', {}).get('text', ''))

            if total_distance or total_duration:
                summary = f"\n總計: "
                if total_distance:
                    summary += f"距離{total_distance}"
                if total_duration:
                    summary += f"，預估時間{total_duration}"
                navigation_text.append(summary)

        return "\n".join(navigation_text)

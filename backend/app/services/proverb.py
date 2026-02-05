# backend/app/services/proverb.py
"""氣象諺語服務

提供諺語驗證功能：
- 臺灣在地氣象諺語資料庫
- 用歷史數據驗證諺語準確率
- 諺語科學解釋
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional, Callable
from enum import Enum
import statistics

from sqlalchemy.orm import Session

from app.models import RawObservation


class ProverbCategory(str, Enum):
    """諺語分類"""
    SOLAR_TERM = "節氣"      # 節氣相關
    SEASONAL = "季節"        # 季節變化
    RAIN = "降雨"            # 降雨預測
    TEMPERATURE = "溫度"     # 溫度變化
    AGRICULTURE = "農業"     # 農業活動
    TYPHOON = "颱風"         # 颱風預測
    GENERAL = "通用"         # 一般氣象


class ProverbRegion(str, Enum):
    """諺語來源地區"""
    TAIWAN = "臺灣"          # 臺灣本土諺語
    CHINA = "華夏"           # 中原傳統諺語
    HAKKA = "客家"           # 客家諺語
    HOKKIEN = "閩南"         # 閩南語諺語


@dataclass
class ProverbVerification:
    """諺語驗證結果"""
    total_cases: int          # 總驗證樣本數
    positive_cases: int       # 符合諺語的樣本數
    accuracy_rate: float      # 準確率 (0-1)
    interpretation: str       # 結果解讀
    sample_years: list[int]   # 使用的年份樣本
    methodology: str          # 驗證方法說明


@dataclass
class Proverb:
    """諺語資料"""
    id: str                              # 諺語 ID
    text: str                            # 諺語原文
    reading: Optional[str] = None        # 臺語/客語讀音
    meaning: str = ""                    # 白話解釋
    category: ProverbCategory = ProverbCategory.GENERAL
    region: ProverbRegion = ProverbRegion.TAIWAN
    related_solar_term: Optional[str] = None  # 相關節氣
    scientific_explanation: str = ""     # 科學解釋
    applicable_months: list[int] = field(default_factory=list)  # 適用月份
    keywords: list[str] = field(default_factory=list)  # 關鍵字
    verifiable: bool = True              # 是否可用數據驗證
    verification_method: str = ""        # 驗證方法描述


# ============================================
# 臺灣在地氣象諺語資料庫
# ============================================

PROVERBS_DATABASE: dict[str, Proverb] = {
    # ========== 節氣相關諺語 ==========
    "lichun_rain": Proverb(
        id="lichun_rain",
        text="立春落雨透清明",
        meaning="立春這天如果下雨，會一直下到清明",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.TAIWAN,
        related_solar_term="立春",
        scientific_explanation="立春前後臺灣處於東北季風尾聲與春雨過渡期，若形成持續性鋒面，確實可能延續多日降雨。",
        applicable_months=[2, 3, 4],
        keywords=["立春", "清明", "降雨"],
        verification_method="檢查立春日有雨的年份中，立春至清明期間的降雨天數是否高於平均",
    ),
    "qingming_rain": Proverb(
        id="qingming_rain",
        text="清明時節雨紛紛",
        meaning="清明節前後經常下雨",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.CHINA,
        related_solar_term="清明",
        scientific_explanation="清明前後臺灣進入梅雨季前期，華南雲雨帶北移，降雨機率確實較高。",
        applicable_months=[4],
        keywords=["清明", "降雨"],
        verification_method="計算清明節前後一週的歷史降雨機率",
    ),
    "xiazhi_heat": Proverb(
        id="xiazhi_heat",
        text="夏至不過不熱",
        meaning="夏至之後才會真正炎熱",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.CHINA,
        related_solar_term="夏至",
        scientific_explanation="夏至是北半球白晝最長的一天，但地表熱量累積需要時間，最熱時期通常在夏至後一個月左右。",
        applicable_months=[6, 7],
        keywords=["夏至", "溫度", "炎熱"],
        verification_method="比較夏至前後各 30 天的平均最高溫",
    ),
    "dongzhi_cold": Proverb(
        id="dongzhi_cold",
        text="冬至不過不寒",
        meaning="冬至之後才會真正寒冷",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.CHINA,
        related_solar_term="冬至",
        scientific_explanation="冬至是北半球白晝最短的一天，但地表冷卻需要時間，最冷時期通常在冬至後的小寒、大寒。",
        applicable_months=[12, 1],
        keywords=["冬至", "溫度", "寒冷"],
        verification_method="比較冬至前後各 30 天的平均最低溫",
    ),
    "bailu_dew": Proverb(
        id="bailu_dew",
        text="白露身不露",
        meaning="白露後天氣轉涼，不宜再穿短袖",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.CHINA,
        related_solar_term="白露",
        scientific_explanation="白露時節臺灣受東北季風影響，氣溫明顯下降，日夜溫差加大。",
        applicable_months=[9],
        keywords=["白露", "溫度", "轉涼"],
        verification_method="計算白露前後平均溫度變化幅度",
    ),

    # ========== 臺灣在地諺語 ==========
    "spring_mother_face": Proverb(
        id="spring_mother_face",
        text="春天後母面",
        reading="tshun-thinn āu-bó-bīn",
        meaning="春天天氣變化無常，像後母的臉色一樣難以捉摸",
        category=ProverbCategory.SEASONAL,
        region=ProverbRegion.HOKKIEN,
        scientific_explanation="春季為季風交替期，冷暖氣團交替頻繁，加上鋒面通過，天氣確實多變。",
        applicable_months=[3, 4, 5],
        keywords=["春天", "天氣變化"],
        verification_method="計算春季每日溫差變化的標準差",
    ),
    "june_fire_burning": Proverb(
        id="june_fire_burning",
        text="六月火燒埔",
        reading="la̍k-gue̍h hué sio-poo",
        meaning="農曆六月天氣極熱，像火燒一樣",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.HOKKIEN,
        scientific_explanation="農曆六月（約國曆七月）正值臺灣盛夏，太平洋高壓籠罩，常出現高溫。",
        applicable_months=[7],
        keywords=["六月", "高溫", "炎熱"],
        verification_method="計算七月超過 35°C 的天數比例",
    ),
    "september_wind": Proverb(
        id="september_wind",
        text="九月風，十月颱",
        reading="káu-gue̍h hong, tsa̍p-gue̍h thai",
        meaning="農曆九月多風，十月可能有颱風",
        category=ProverbCategory.TYPHOON,
        region=ProverbRegion.HOKKIEN,
        scientific_explanation="農曆九、十月（約國曆十、十一月）為秋颱季節，東北季風增強。",
        applicable_months=[10, 11],
        keywords=["九月", "十月", "颱風", "風"],
        verification_method="計算十、十一月的平均風速和颱風頻率",
    ),
    "frost_rice_barn": Proverb(
        id="frost_rice_barn",
        text="霜降見霜，米穀滿倉",
        meaning="霜降時節如果見到霜，預示豐收年",
        category=ProverbCategory.AGRICULTURE,
        region=ProverbRegion.TAIWAN,
        related_solar_term="霜降",
        scientific_explanation="霜降見霜表示氣候正常，冷暖交替有序，有利於農作物成熟。",
        applicable_months=[10],
        keywords=["霜降", "霜", "豐收"],
        verification_method="檢查霜降時期低溫與該年農產量的相關性",
        verifiable=False,  # 需要農產量數據
    ),
    "bamboo_shoot_rain": Proverb(
        id="bamboo_shoot_rain",
        text="竹筍雨，落甲飽",
        reading="tik-sún-hōo, lo̍h kah pá",
        meaning="春天竹筍生長期的雨會下得很足",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.HOKKIEN,
        scientific_explanation="春季為竹筍生長期，此時也是春雨季節，降雨機率和雨量確實較高。",
        applicable_months=[3, 4, 5],
        keywords=["竹筍", "春雨", "降雨"],
        verification_method="計算三至五月的平均降雨量",
    ),

    # ========== 梅雨相關 ==========
    "plum_rain": Proverb(
        id="plum_rain",
        text="小滿大滿江河滿",
        meaning="小滿到大滿（芒種前）期間，雨水充沛，江河水位高漲",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.CHINA,
        related_solar_term="小滿",
        scientific_explanation="此時正值臺灣梅雨季高峰期，滯留鋒面帶來連續性降雨，雨量豐沛。",
        applicable_months=[5, 6],
        keywords=["小滿", "梅雨", "降雨"],
        verification_method="計算五月下旬至六月中旬的累積降雨量",
    ),
    "mangzhong_rain": Proverb(
        id="mangzhong_rain",
        text="芒種夏至天，走路要人牽",
        meaning="芒種到夏至期間，天氣炎熱潮濕，容易中暑",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.CHINA,
        related_solar_term="芒種",
        scientific_explanation="此時為梅雨季尾聲，高溫高濕，體感溫度高，容易不適。",
        applicable_months=[6],
        keywords=["芒種", "夏至", "高溫", "濕度"],
        verification_method="計算六月平均溫度和濕度，以及體感溫度",
    ),

    # ========== 颱風相關 ==========
    "qixi_typhoon": Proverb(
        id="qixi_typhoon",
        text="七夕水，無人知",
        reading="tshit-si̍k-tsuí, bô-lâng-tsai",
        meaning="農曆七月七日前後常有突然的降雨（颱風）",
        category=ProverbCategory.TYPHOON,
        region=ProverbRegion.HOKKIEN,
        scientific_explanation="農曆七月七日約在國曆八月中旬，正值颱風旺季。",
        applicable_months=[8],
        keywords=["七夕", "颱風", "降雨"],
        verification_method="計算八月中旬的降雨機率和颱風侵台頻率",
    ),
    "mid_autumn_typhoon": Proverb(
        id="mid_autumn_typhoon",
        text="中秋無月光，無颱風也有雨",
        reading="tiong-tshiu bô gue̍h-kng, bô thai-hong iā ū hōo",
        meaning="中秋節看不到月亮，即使沒有颱風也會下雨",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.HOKKIEN,
        scientific_explanation="中秋前後為秋颱季節，即使沒有颱風，東北季風也可能帶來降雨。",
        applicable_months=[9, 10],
        keywords=["中秋", "颱風", "降雨"],
        verification_method="計算中秋節當日的歷史降雨機率",
    ),

    # ========== 冬季相關 ==========
    "winter_thunder": Proverb(
        id="winter_thunder",
        text="冬雷震震，米穀不稔",
        meaning="冬天打雷，預示來年收成不好",
        category=ProverbCategory.AGRICULTURE,
        region=ProverbRegion.CHINA,
        scientific_explanation="冬季打雷表示氣候異常，可能影響作物生長週期。",
        applicable_months=[12, 1, 2],
        keywords=["冬天", "雷", "農業"],
        verification_method="統計冬季打雷頻率",
        verifiable=False,  # 需要雷擊數據
    ),
    "cold_wave_from_north": Proverb(
        id="cold_wave_from_north",
        text="大陸冷氣團來時，嘉南平原溫度最低",
        meaning="寒流來襲時，嘉南平原因地形關係溫度降得最低",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.TAIWAN,
        scientific_explanation="嘉南平原地勢平坦開闊，缺乏屏障，冷空氣容易堆積，造成輻射冷卻效應明顯。",
        applicable_months=[12, 1, 2],
        keywords=["寒流", "嘉南平原", "低溫"],
        verification_method="比較寒流期間各站點的最低溫差異",
    ),
    "spring_cold": Proverb(
        id="spring_cold",
        text="大雪不凍倒春寒",
        meaning="大雪時節如果不夠冷，春天反而會有寒流",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.CHINA,
        related_solar_term="大雪",
        scientific_explanation="冬季暖冬可能導致大氣環流異常，造成春季出現異常低溫。",
        applicable_months=[12, 3],
        keywords=["大雪", "春寒", "溫度"],
        verification_method="檢查大雪時期溫度與隔年春季低溫的相關性",
    ),

    # ========== 降雨預測 ==========
    "morning_glow": Proverb(
        id="morning_glow",
        text="朝霞不出門，晚霞行千里",
        meaning="早上有紅霞不宜出門（會下雨），傍晚有紅霞則天氣好",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.CHINA,
        scientific_explanation="臺灣天氣系統由西向東移動，早上西邊有雲（朝霞）表示天氣系統將至；傍晚西邊晴朗（晚霞）表示天氣將好轉。",
        applicable_months=list(range(1, 13)),
        keywords=["朝霞", "晚霞", "天氣"],
        verification_method="需要雲況觀測數據",
        verifiable=False,
    ),
    "ant_moving": Proverb(
        id="ant_moving",
        text="螞蟻搬家，天將雨",
        meaning="螞蟻大規模搬家，表示即將下雨",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.CHINA,
        scientific_explanation="螞蟻對氣壓和濕度變化敏感，下雨前氣壓降低、濕度升高，螞蟻會將巢穴移至高處。",
        applicable_months=list(range(1, 13)),
        keywords=["螞蟻", "降雨"],
        verifiable=False,
    ),
    "swallow_low_fly": Proverb(
        id="swallow_low_fly",
        text="燕子低飛要落雨",
        reading="ìnn-á kē-pue beh lo̍h-hōo",
        meaning="燕子飛得低，表示快要下雨",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.HOKKIEN,
        scientific_explanation="下雨前空氣濕度高，昆蟲飛行高度降低，燕子追逐昆蟲也跟著低飛。",
        applicable_months=list(range(1, 13)),
        keywords=["燕子", "降雨"],
        verifiable=False,
    ),

    # ========== 溫度相關 ==========
    "hot_before_rain": Proverb(
        id="hot_before_rain",
        text="雨前燠熱，雨後寒涼",
        meaning="下雨前悶熱，下雨後涼爽",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.TAIWAN,
        scientific_explanation="降雨前暖濕空氣聚集，氣壓低而悶熱；雨後冷空氣隨鋒面南下，氣溫下降。",
        applicable_months=list(range(1, 13)),
        keywords=["悶熱", "降雨", "降溫"],
        verification_method="計算降雨日前後的溫度變化",
    ),
    "early_hot_late_cold": Proverb(
        id="early_hot_late_cold",
        text="早穿棉襖午穿紗，圍著火爐吃西瓜",
        meaning="形容日夜溫差極大",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.CHINA,
        scientific_explanation="臺灣春秋季節日夜溫差可達 10 度以上，尤其是盆地和平原地區。",
        applicable_months=[3, 4, 10, 11],
        keywords=["溫差", "日夜"],
        verification_method="計算春秋季節的日均溫差",
    ),

    # ========== 客家諺語 ==========
    "hakka_spring_rain": Proverb(
        id="hakka_spring_rain",
        text="春雨貴如油",
        meaning="春天的雨水對農作物非常珍貴",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.HAKKA,
        scientific_explanation="春季為農作物生長關鍵期，適量降雨有利於作物發芽成長。",
        applicable_months=[2, 3, 4],
        keywords=["春雨", "農業"],
        verification_method="計算二至四月的降雨量分布",
    ),
    "hakka_frost": Proverb(
        id="hakka_frost",
        text="霜降落霜，立冬落雨",
        meaning="霜降有霜，立冬就會有雨",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.HAKKA,
        related_solar_term="霜降",
        scientific_explanation="霜降有霜表示天氣轉涼，東北季風建立，立冬前後常帶來降雨。",
        applicable_months=[10, 11],
        keywords=["霜降", "立冬", "霜", "降雨"],
        verification_method="檢查霜降低溫與立冬降雨的相關性",
    ),

    # ========== 農業相關 ==========
    "grain_in_ear": Proverb(
        id="grain_in_ear",
        text="芒種逢雷美亦然，端陽有雨是豐年",
        meaning="芒種打雷、端午有雨，都是豐收的好兆頭",
        category=ProverbCategory.AGRICULTURE,
        region=ProverbRegion.CHINA,
        related_solar_term="芒種",
        scientific_explanation="芒種前後為水稻插秧期，適量降雨有利於秧苗存活。",
        applicable_months=[6],
        keywords=["芒種", "端午", "降雨", "豐收"],
        verification_method="計算六月初（端午前後）的降雨機率",
    ),
    "double_ninth": Proverb(
        id="double_ninth",
        text="重陽無雨望冬乾",
        meaning="重陽節（農曆九月九日）不下雨，冬天就會乾旱",
        category=ProverbCategory.RAIN,
        region=ProverbRegion.CHINA,
        scientific_explanation="重陽節約在國曆十月，若此時缺乏降雨，可能意味著整個冬季降雨偏少。",
        applicable_months=[10],
        keywords=["重陽", "冬季", "乾旱"],
        verification_method="檢查重陽降雨與該年冬季降雨量的相關性",
    ),

    # ========== 其他季節性諺語 ==========
    "summer_solstice_long": Proverb(
        id="summer_solstice_long",
        text="吃過夏至麵，一天短一線",
        meaning="夏至後白天開始變短",
        category=ProverbCategory.SOLAR_TERM,
        region=ProverbRegion.CHINA,
        related_solar_term="夏至",
        scientific_explanation="夏至是北半球白晝最長的一天，之後日照時數逐日減少。",
        applicable_months=[6, 7],
        keywords=["夏至", "日照", "白天"],
        verification_method="計算夏至前後日照時數變化",
    ),
    "autumn_tiger": Proverb(
        id="autumn_tiger",
        text="處暑天還暑，好似秋老虎",
        meaning="處暑後天氣仍然炎熱，像秋天的老虎一樣",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.CHINA,
        related_solar_term="處暑",
        scientific_explanation="處暑雖名為「暑氣結束」，但臺灣此時仍受太平洋高壓影響，常有高溫。",
        applicable_months=[8, 9],
        keywords=["處暑", "秋老虎", "高溫"],
        verification_method="計算八月下旬至九月上旬的高溫天數",
    ),
    "three_fu_days": Proverb(
        id="three_fu_days",
        text="小暑大暑，上蒸下煮",
        meaning="小暑到大暑期間，天氣極為炎熱",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.CHINA,
        related_solar_term="小暑",
        scientific_explanation="小暑、大暑期間是一年中最熱的時候，高溫高濕，體感如同蒸煮。",
        applicable_months=[7],
        keywords=["小暑", "大暑", "高溫"],
        verification_method="計算七月的平均最高溫和超過 35°C 的天數",
    ),
    "cold_in_nine": Proverb(
        id="cold_in_nine",
        text="小寒大寒，凍成冰團",
        meaning="小寒到大寒是一年中最冷的時期",
        category=ProverbCategory.TEMPERATURE,
        region=ProverbRegion.CHINA,
        related_solar_term="小寒",
        scientific_explanation="小寒、大寒期間太陽直射南半球，北半球獲得熱量最少，加上冷氣團頻繁，氣溫最低。",
        applicable_months=[1],
        keywords=["小寒", "大寒", "低溫"],
        verification_method="計算一月的平均最低溫和低於 10°C 的天數",
    ),
}


def get_all_proverbs() -> list[Proverb]:
    """取得所有諺語"""
    return list(PROVERBS_DATABASE.values())


def get_proverb_by_id(proverb_id: str) -> Optional[Proverb]:
    """依 ID 取得諺語"""
    return PROVERBS_DATABASE.get(proverb_id)


def get_proverbs_by_category(category: ProverbCategory) -> list[Proverb]:
    """依分類取得諺語"""
    return [p for p in PROVERBS_DATABASE.values() if p.category == category]


def get_proverbs_by_region(region: ProverbRegion) -> list[Proverb]:
    """依地區取得諺語"""
    return [p for p in PROVERBS_DATABASE.values() if p.region == region]


def get_proverbs_by_solar_term(solar_term: str) -> list[Proverb]:
    """依相關節氣取得諺語"""
    return [p for p in PROVERBS_DATABASE.values() if p.related_solar_term == solar_term]


def get_proverbs_by_month(month: int) -> list[Proverb]:
    """依月份取得適用的諺語"""
    return [p for p in PROVERBS_DATABASE.values() if month in p.applicable_months]


def get_verifiable_proverbs() -> list[Proverb]:
    """取得可驗證的諺語列表"""
    return [p for p in PROVERBS_DATABASE.values() if p.verifiable]


def search_proverbs(keyword: str) -> list[Proverb]:
    """搜尋諺語（在原文、解釋、關鍵字中搜尋）"""
    keyword = keyword.lower()
    results = []
    for p in PROVERBS_DATABASE.values():
        if (keyword in p.text.lower() or
            keyword in p.meaning.lower() or
            any(keyword in kw.lower() for kw in p.keywords)):
            results.append(p)
    return results

# backend/app/services/solar_term.py
"""二十四節氣服務

提供節氣深度資訊：
- 節氣名稱與日期
- 天文意義
- 農業意義
- 氣象特徵
- 相關諺語
- 物候特徵
"""

from datetime import datetime, date, timedelta
from typing import Optional
from dataclasses import dataclass
import cnlunar


@dataclass
class SolarTermInfo:
    """節氣完整資訊"""
    name: str                    # 節氣名稱
    name_en: str                 # 英文名稱
    order: int                   # 序號 (1-24)
    solar_longitude: int         # 太陽黃經度數
    typical_date: str            # 典型日期 (MM-DD)
    season: str                  # 所屬季節
    is_major: bool               # 是否為「中氣」（節氣分「節」和「中」）
    astronomy: str               # 天文意義
    agriculture: str             # 農業意義
    weather: str                 # 氣象特徵（臺灣）
    phenology: list[str]         # 物候（三候）
    proverbs: list[str]          # 相關諺語
    health_tips: str             # 養生建議


# 二十四節氣完整資料庫
SOLAR_TERMS_DATA: dict[str, SolarTermInfo] = {
    "立春": SolarTermInfo(
        name="立春",
        name_en="Start of Spring",
        order=1,
        solar_longitude=315,
        typical_date="02-04",
        season="春",
        is_major=False,
        astronomy="太陽到達黃經315度，春季開始",
        agriculture="春耕準備開始，農諺「立春一日，百草回芽」",
        weather="臺灣仍處冬末，北部仍有寒流可能，南部開始回暖。日照漸長，氣溫開始緩慢上升。",
        phenology=["東風解凍", "蟄蟲始振", "魚陟負冰"],
        proverbs=[
            "立春落雨透清明",
            "立春晴一日，耕田不費力",
            "立春打雷，十處豬欄九處空",
        ],
        health_tips="宜養肝護陽，飲食清淡，適量運動以助陽氣生發。"
    ),
    "雨水": SolarTermInfo(
        name="雨水",
        name_en="Rain Water",
        order=2,
        solar_longitude=330,
        typical_date="02-19",
        season="春",
        is_major=True,
        astronomy="太陽到達黃經330度，降雨增多",
        agriculture="春雨貴如油，農作物開始需要水分灌溉",
        weather="臺灣進入春雨季節，東北季風減弱，天氣變化多端，忽冷忽熱。",
        phenology=["獺祭魚", "鴻雁來", "草木萌動"],
        proverbs=[
            "雨水連綿是豐年，農民不用力耕田",
            "雨水有雨，一年多水",
            "雨水落雨三大碗，大河小河都要滿",
        ],
        health_tips="注意防寒保暖，預防感冒。宜食溫補食物，少食生冷。"
    ),
    "驚蟄": SolarTermInfo(
        name="驚蟄",
        name_en="Awakening of Insects",
        order=3,
        solar_longitude=345,
        typical_date="03-06",
        season="春",
        is_major=False,
        astronomy="太陽到達黃經345度，春雷驚醒冬眠生物",
        agriculture="農諺「驚蟄到，農夫忙」，開始春耕播種",
        weather="臺灣春雷初響，溫度回升明顯，但仍有冷氣團南下，「春天後母面」變化大。",
        phenology=["桃始華", "倉庚鳴", "鷹化為鳩"],
        proverbs=[
            "驚蟄聞雷米似泥",
            "驚蟄不耕田，好比蒸饅頭不發酵",
            "驚蟄過，暖和和，蛤蟆老角唱山歌",
        ],
        health_tips="春季養肝，宜早睡早起，保持心情舒暢，飲食清淡。"
    ),
    "春分": SolarTermInfo(
        name="春分",
        name_en="Spring Equinox",
        order=4,
        solar_longitude=0,
        typical_date="03-21",
        season="春",
        is_major=True,
        astronomy="太陽直射赤道，晝夜等長，春季過半",
        agriculture="春分種麥，秋分種稻。農事繁忙期",
        weather="臺灣氣候宜人，日夜溫差仍大。梅雨季前的好天氣。",
        phenology=["玄鳥至", "雷乃發聲", "始電"],
        proverbs=[
            "春分有雨病人稀",
            "春分前後怕春霜",
            "春分雨不歇，清明前後有好天",
        ],
        health_tips="陰陽平衡之時，宜調和身心，不宜過勞。"
    ),
    "清明": SolarTermInfo(
        name="清明",
        name_en="Pure Brightness",
        order=5,
        solar_longitude=15,
        typical_date="04-05",
        season="春",
        is_major=False,
        astronomy="太陽到達黃經15度，萬物清潔明淨",
        agriculture="清明穀雨兩相連，浸種耕田莫遲延",
        weather="臺灣進入梅雨季前期，天氣回暖但多雨。清明時節雨紛紛。",
        phenology=["桐始華", "田鼠化為鴽", "虹始見"],
        proverbs=[
            "清明時節雨紛紛",
            "清明穀雨，凍死老鼠",
            "清明斷雪，穀雨斷霜",
        ],
        health_tips="宜踏青舒展身心，飲食宜清淡，多食當季蔬果。"
    ),
    "穀雨": SolarTermInfo(
        name="穀雨",
        name_en="Grain Rain",
        order=6,
        solar_longitude=30,
        typical_date="04-20",
        season="春",
        is_major=True,
        astronomy="太陽到達黃經30度，雨生百穀",
        agriculture="穀雨前後，種瓜點豆。播種好時機",
        weather="臺灣梅雨季開始，雨量增加，濕度高。",
        phenology=["萍始生", "鳴鳩拂其羽", "戴勝降于桑"],
        proverbs=[
            "穀雨前後一場雨，勝似秀才中了舉",
            "穀雨無雨，後來哭雨",
            "穀雨栽上紅薯秧，一棵能收一大筐",
        ],
        health_tips="濕氣重，宜健脾祛濕，少食寒涼。"
    ),
    "立夏": SolarTermInfo(
        name="立夏",
        name_en="Start of Summer",
        order=7,
        solar_longitude=45,
        typical_date="05-06",
        season="夏",
        is_major=False,
        astronomy="太陽到達黃經45度，夏季開始",
        agriculture="立夏東風到，麥子水裡撈",
        weather="臺灣正值梅雨季，天氣悶熱潮濕，雷陣雨頻繁。",
        phenology=["螻蟈鳴", "蚯蚓出", "王瓜生"],
        proverbs=[
            "立夏補老父",
            "立夏吃蛋，石頭踩爛",
            "立夏小滿雨水相趕",
        ],
        health_tips="宜養心，清淡飲食，午睡養神，避免過度出汗。"
    ),
    "小滿": SolarTermInfo(
        name="小滿",
        name_en="Grain Buds",
        order=8,
        solar_longitude=60,
        typical_date="05-21",
        season="夏",
        is_major=True,
        astronomy="太陽到達黃經60度，穀物漸飽滿",
        agriculture="小滿不滿，麥有一險（乾熱風）",
        weather="臺灣梅雨季高峰，暴雨頻繁，需防水災。天氣悶熱。",
        phenology=["苦菜秀", "靡草死", "麥秋至"],
        proverbs=[
            "小滿大滿江河滿",
            "小滿不下，乾斷塘壩",
            "小滿動三車（水車、油車、繅車）",
        ],
        health_tips="防暑濕，清熱利濕，多食苦瓜、綠豆等。"
    ),
    "芒種": SolarTermInfo(
        name="芒種",
        name_en="Grain in Ear",
        order=9,
        solar_longitude=75,
        typical_date="06-06",
        season="夏",
        is_major=False,
        astronomy="太陽到達黃經75度，有芒作物成熟",
        agriculture="芒種忙忙栽，夏至谷懷胎",
        weather="臺灣梅雨季尾聲，氣溫持續升高，午後常有雷陣雨。",
        phenology=["螳螂生", "鵙始鳴", "反舌無聲"],
        proverbs=[
            "芒種夏至天，走路要人牽",
            "芒種逢雷美亦然，端陽有雨是豐年",
            "芒種火燒天，夏至雨綿綿",
        ],
        health_tips="注意防暑，保持室內通風，飲食清淡易消化。"
    ),
    "夏至": SolarTermInfo(
        name="夏至",
        name_en="Summer Solstice",
        order=10,
        solar_longitude=90,
        typical_date="06-21",
        season="夏",
        is_major=True,
        astronomy="太陽直射北回歸線，北半球白晝最長",
        agriculture="夏至不過不熱，冬至不過不寒",
        weather="臺灣進入炎夏，太平洋高壓影響，晴熱為主，午後雷陣雨。",
        phenology=["鹿角解", "蜩始鳴", "半夏生"],
        proverbs=[
            "夏至一陰生",
            "吃過夏至麵，一天短一線",
            "夏至有雷三伏熱",
        ],
        health_tips="陽氣最盛，宜靜養，避免正午外出，多食清涼消暑食物。"
    ),
    "小暑": SolarTermInfo(
        name="小暑",
        name_en="Minor Heat",
        order=11,
        solar_longitude=105,
        typical_date="07-07",
        season="夏",
        is_major=False,
        astronomy="太陽到達黃經105度，天氣開始炎熱",
        agriculture="小暑過，一日熱三分",
        weather="臺灣盛夏酷暑，高溫炎熱，需防熱傷害。颱風季節開始。",
        phenology=["溫風至", "蟋蟀居壁", "鷹始擊"],
        proverbs=[
            "小暑大暑，上蒸下煮",
            "小暑不算熱，大暑三伏天",
            "小暑一聲雷，倒轉做黃梅",
        ],
        health_tips="防暑降溫，多補充水分和電解質，避免中暑。"
    ),
    "大暑": SolarTermInfo(
        name="大暑",
        name_en="Major Heat",
        order=12,
        solar_longitude=120,
        typical_date="07-23",
        season="夏",
        is_major=True,
        astronomy="太陽到達黃經120度，一年中最熱時期",
        agriculture="大暑不暑，五穀不鼓",
        weather="臺灣一年最熱時期，高溫頻繁突破35度。颱風活躍季節。",
        phenology=["腐草為螢", "土潤溽暑", "大雨時行"],
        proverbs=[
            "大暑熱不透，大熱在秋後",
            "大暑無酷熱，五穀多不結",
            "大暑展秋風，秋後熱到狂",
        ],
        health_tips="三伏天重養生，清熱解暑，注意防曬，保持充足睡眠。"
    ),
    "立秋": SolarTermInfo(
        name="立秋",
        name_en="Start of Autumn",
        order=13,
        solar_longitude=135,
        typical_date="08-08",
        season="秋",
        is_major=False,
        astronomy="太陽到達黃經135度，秋季開始",
        agriculture="立秋三場雨，麻布扇子高擱起",
        weather="臺灣仍處盛夏，俗稱「秋老虎」，高溫依舊。颱風仍活躍。",
        phenology=["涼風至", "白露降", "寒蟬鳴"],
        proverbs=[
            "立秋之日涼風至",
            "雷打秋，冬半收",
            "立秋處暑有陣頭，三秋天氣多雨水",
        ],
        health_tips="秋季養肺，宜滋陰潤燥，多食梨、蜂蜜等。"
    ),
    "處暑": SolarTermInfo(
        name="處暑",
        name_en="End of Heat",
        order=14,
        solar_longitude=150,
        typical_date="08-23",
        season="秋",
        is_major=True,
        astronomy="太陽到達黃經150度，暑氣漸消",
        agriculture="處暑不出頭，割穀喂老牛",
        weather="臺灣暑氣漸退，早晚稍涼，但白天仍炎熱。颱風持續。",
        phenology=["鷹乃祭鳥", "天地始肅", "禾乃登"],
        proverbs=[
            "處暑天還暑，好似秋老虎",
            "處暑不下雨，乾到白露底",
            "處暑滿地黃，家家修廩倉",
        ],
        health_tips="暑濕未盡，宜清補，多食蓮藕、百合等。"
    ),
    "白露": SolarTermInfo(
        name="白露",
        name_en="White Dew",
        order=15,
        solar_longitude=165,
        typical_date="09-08",
        season="秋",
        is_major=False,
        astronomy="太陽到達黃經165度，露水凝白",
        agriculture="白露秋分夜，一夜涼一夜",
        weather="臺灣秋意漸濃，日夜溫差加大，東北季風開始增強。",
        phenology=["鴻雁來", "玄鳥歸", "群鳥養羞"],
        proverbs=[
            "白露身不露",
            "白露秋風夜，一夜涼一夜",
            "白露勿露身，早晚要叮嚀",
        ],
        health_tips="注意保暖，預防感冒。宜食溫補，少食生冷。"
    ),
    "秋分": SolarTermInfo(
        name="秋分",
        name_en="Autumn Equinox",
        order=16,
        solar_longitude=180,
        typical_date="09-23",
        season="秋",
        is_major=True,
        astronomy="太陽直射赤道，晝夜等長，秋季過半",
        agriculture="秋分種小麥，冬至送草鞋",
        weather="臺灣秋高氣爽，天氣穩定，日夜溫差大。",
        phenology=["雷始收聲", "蟄蟲坏戶", "水始涸"],
        proverbs=[
            "秋分天氣白雲來，處處新歌好稻栽",
            "秋分有雨來年豐",
            "秋分西風響，蟹腳癢",
        ],
        health_tips="陰陽平衡，宜收斂神氣，早睡早起，滋陰潤肺。"
    ),
    "寒露": SolarTermInfo(
        name="寒露",
        name_en="Cold Dew",
        order=17,
        solar_longitude=195,
        typical_date="10-08",
        season="秋",
        is_major=False,
        astronomy="太陽到達黃經195度，露水寒涼",
        agriculture="寒露過後，防寒保暖",
        weather="臺灣東北季風增強，天氣轉涼，北部開始有涼意。",
        phenology=["鴻雁來賓", "雀入大水為蛤", "菊有黃華"],
        proverbs=[
            "寒露腳不露",
            "吃了寒露飯，單衣漢少見",
            "寒露十月已秋深，田裡種麥要當心",
        ],
        health_tips="注意添衣保暖，防秋燥，多食潤燥食物。"
    ),
    "霜降": SolarTermInfo(
        name="霜降",
        name_en="Frost Descent",
        order=18,
        solar_longitude=210,
        typical_date="10-24",
        season="秋",
        is_major=True,
        astronomy="太陽到達黃經210度，天氣漸冷，開始有霜",
        agriculture="霜降殺百草",
        weather="臺灣高山地區可能出現霜凍，平地秋意濃厚，早晚涼。",
        phenology=["豺乃祭獸", "草木黃落", "蜇蟲咸俯"],
        proverbs=[
            "霜降見霜，米穀滿倉",
            "霜降無霜，主來歲饑荒",
            "一年補通通，不如補霜降",
        ],
        health_tips="秋冬進補開始，宜食溫補，如羊肉、核桃等。"
    ),
    "立冬": SolarTermInfo(
        name="立冬",
        name_en="Start of Winter",
        order=19,
        solar_longitude=225,
        typical_date="11-08",
        season="冬",
        is_major=False,
        astronomy="太陽到達黃經225度，冬季開始",
        agriculture="立冬補冬，補嘴空",
        weather="臺灣北部轉涼，南部仍暖。東北季風明顯，偶有冷氣團。",
        phenology=["水始冰", "地始凍", "雉入大水為蜃"],
        proverbs=[
            "立冬收成期，雞鳥卡會啼",
            "立冬晴，一冬晴；立冬雨，一冬雨",
            "立冬補冬，補嘴空",
        ],
        health_tips="進補時節，宜食羊肉、薑母鴨等溫補食物。"
    ),
    "小雪": SolarTermInfo(
        name="小雪",
        name_en="Minor Snow",
        order=20,
        solar_longitude=240,
        typical_date="11-22",
        season="冬",
        is_major=True,
        astronomy="太陽到達黃經240度，開始降小雪",
        agriculture="小雪醃菜，大雪醃肉",
        weather="臺灣北部濕冷，高山可能降雪。東北季風持續影響。",
        phenology=["虹藏不見", "天氣上升地氣下降", "閉塞而成冬"],
        proverbs=[
            "小雪地封嚴",
            "小雪封地，大雪封河",
            "小雪雪滿天，來年必豐年",
        ],
        health_tips="防寒保暖，多食熱食，適當運動以防冬日懶散。"
    ),
    "大雪": SolarTermInfo(
        name="大雪",
        name_en="Major Snow",
        order=21,
        solar_longitude=255,
        typical_date="12-07",
        season="冬",
        is_major=False,
        astronomy="太陽到達黃經255度，降雪增多",
        agriculture="大雪紛紛落，明年吃饃饃",
        weather="臺灣冬季氣候，北部濕冷，高山積雪增加。",
        phenology=["鶡鴠不鳴", "虎始交", "荔挺出"],
        proverbs=[
            "大雪不凍倒春寒",
            "大雪晴天，立春雪多",
            "大雪兆豐年，無雪要遭殃",
        ],
        health_tips="陽氣內斂，宜早睡晚起，溫補養腎。"
    ),
    "冬至": SolarTermInfo(
        name="冬至",
        name_en="Winter Solstice",
        order=22,
        solar_longitude=270,
        typical_date="12-22",
        season="冬",
        is_major=True,
        astronomy="太陽直射南回歸線，北半球白晝最短",
        agriculture="冬至大如年",
        weather="臺灣一年最冷時期開始，寒流頻繁，需防低溫。",
        phenology=["蚯蚓結", "麋角解", "水泉動"],
        proverbs=[
            "冬至一陽生",
            "冬至大過年",
            "冬至紅，年邊濃；冬至黑，年邊疏",
        ],
        health_tips="陰極陽生，宜大補，如湯圓、薑母鴨、羊肉爐。"
    ),
    "小寒": SolarTermInfo(
        name="小寒",
        name_en="Minor Cold",
        order=23,
        solar_longitude=285,
        typical_date="01-06",
        season="冬",
        is_major=False,
        astronomy="太陽到達黃經285度，天氣漸寒",
        agriculture="小寒大寒，凍成冰團",
        weather="臺灣最冷時期之一，寒流影響頻繁，北部低溫。",
        phenology=["雁北鄉", "鵲始巢", "雉始雊"],
        proverbs=[
            "小寒勝大寒，常見不稀罕",
            "小寒大寒不下雪，小暑大暑田開裂",
            "小寒節，十五天，七八天處三九天",
        ],
        health_tips="注意保暖，防寒防凍，宜食溫熱食物。"
    ),
    "大寒": SolarTermInfo(
        name="大寒",
        name_en="Major Cold",
        order=24,
        solar_longitude=300,
        typical_date="01-20",
        season="冬",
        is_major=True,
        astronomy="太陽到達黃經300度，一年最冷時期",
        agriculture="大寒見三白，農人衣食足",
        weather="臺灣仍處嚴冬，但即將迎來立春，天氣開始準備回暖。",
        phenology=["雞始乳", "征鳥厲疾", "水澤腹堅"],
        proverbs=[
            "大寒不寒，人馬不安",
            "大寒不寒，春分不暖",
            "大寒日怕南風起，當天最忌下雨時",
        ],
        health_tips="冬令進補尾聲，宜收斂進補，為春季養肝做準備。"
    ),
}


def get_solar_term_info(name: str) -> Optional[SolarTermInfo]:
    """取得指定節氣的完整資訊

    Args:
        name: 節氣名稱

    Returns:
        節氣資訊，找不到則返回 None
    """
    return SOLAR_TERMS_DATA.get(name)


def get_all_solar_terms() -> list[SolarTermInfo]:
    """取得所有節氣資訊

    Returns:
        按序號排序的所有節氣列表
    """
    terms = list(SOLAR_TERMS_DATA.values())
    return sorted(terms, key=lambda x: x.order)


def get_current_solar_term(dt: date) -> Optional[str]:
    """取得指定日期的節氣（如果當天是節氣）

    Args:
        dt: 日期

    Returns:
        節氣名稱，如果當天不是節氣則返回 None
    """
    from datetime import datetime
    dt_full = datetime(dt.year, dt.month, dt.day, 12, 0)
    lunar = cnlunar.Lunar(dt_full)
    jieqi = lunar.todaySolarTerms
    return jieqi if jieqi and jieqi != "無" else None


def get_nearest_solar_term(dt: date) -> dict:
    """取得最近的節氣（包含當前所處節氣和下一個節氣）

    Args:
        dt: 日期

    Returns:
        {
            "current": 當前所處的節氣資訊,
            "next": 下一個節氣資訊,
            "days_to_next": 距離下一個節氣的天數
        }
    """
    from datetime import datetime

    # 向前搜尋最近的節氣（當前所處的節氣）
    current_term = None
    for i in range(30):  # 最多往前找30天
        check_date = dt - timedelta(days=i)
        dt_full = datetime(check_date.year, check_date.month, check_date.day, 12, 0)
        lunar = cnlunar.Lunar(dt_full)
        jieqi = lunar.todaySolarTerms
        if jieqi and jieqi != "無":
            current_term = jieqi
            break

    # 向後搜尋下一個節氣
    next_term = None
    days_to_next = None
    for i in range(1, 20):  # 最多往後找20天（節氣間隔約15天）
        check_date = dt + timedelta(days=i)
        dt_full = datetime(check_date.year, check_date.month, check_date.day, 12, 0)
        lunar = cnlunar.Lunar(dt_full)
        jieqi = lunar.todaySolarTerms
        if jieqi and jieqi != "無":
            next_term = jieqi
            days_to_next = i
            break

    return {
        "current": get_solar_term_info(current_term) if current_term else None,
        "next": get_solar_term_info(next_term) if next_term else None,
        "days_to_next": days_to_next,
    }


def get_solar_terms_by_season(season: str) -> list[SolarTermInfo]:
    """取得指定季節的所有節氣

    Args:
        season: 季節 (春/夏/秋/冬)

    Returns:
        該季節的節氣列表
    """
    return [
        term for term in SOLAR_TERMS_DATA.values()
        if term.season == season
    ]

# backend/app/services/divination/hexagrams.py
"""64-hexagram metadata (name + judgement + image + weather_persona).

卦辭 (judgement) 出自《周易》卦辭，大象傳 (image) 出自《周易·大象傳》。
《周易》為先秦典籍，屬公共領域。朱熹《周易本義》亦為公共領域。

weather_persona 為自製內容，採「天氣意象 — 行動建議」格式，
每則 ≤30 繁體中文字符，作為 Layer 1 deterministic fallback。
"""

HEXAGRAMS: list[dict] = [
    {"num": 1,  "name": "乾為天",   "judgement": "元亨利貞",                       "image": "天行健，君子以自強不息",                "weather_persona": "陽光最強的一天 — 全力推進，但別曬到中暑。"},
    {"num": 2,  "name": "坤為地",   "judgement": "元亨，利牝馬之貞",               "image": "地勢坤，君子以厚德載物",                "weather_persona": "陰天靜臥的一天 — 收尾整理比新開戰更划算。"},
    {"num": 3,  "name": "水雷屯",   "judgement": "元亨利貞，勿用有攸往，利建侯",   "image": "雲雷屯，君子以經綸",                    "weather_persona": "雷雨交加的開局 — 卡住正常，沉住氣等天晴。"},
    {"num": 4,  "name": "山水蒙",   "judgement": "亨。匪我求童蒙，童蒙求我",       "image": "山下出泉，君子以果行育德",              "weather_persona": "山間起霧看不清 — 別急著決定，先看清路再走。"},
    {"num": 5,  "name": "水天需",   "judgement": "有孚，光亨，貞吉，利涉大川",     "image": "雲上於天，君子以飲食宴樂",              "weather_persona": "雲在天上未落雨 — 該等就等，雨來了再撐傘。"},
    {"num": 6,  "name": "天水訟",   "judgement": "有孚窒，惕中吉，終凶",           "image": "天與水違行，君子以作事謀始",            "weather_persona": "冷鋒對撞的一天 — 別爭那口氣，先退一步避雷。"},
    {"num": 7,  "name": "地水師",   "judgement": "貞，丈人吉，無咎",               "image": "地中有水，君子以容民畜眾",              "weather_persona": "地下伏流的一天 — 行動要有紀律，別單兵冒進。"},
    {"num": 8,  "name": "水地比",   "judgement": "吉。原筮元永貞，無咎",           "image": "地上有水，先王以建萬國親諸侯",          "weather_persona": "水匯地面成湖泊 — 找對人靠在一起，事就成了。"},
    {"num": 9,  "name": "風天小畜", "judgement": "亨。密雲不雨，自我西郊",         "image": "風行天上，君子以懿文德",                "weather_persona": "雲堆得厚卻沒下 — 火候未到，再蓄一點力再說。"},
    {"num": 10, "name": "天澤履",   "judgement": "履虎尾，不咥人，亨",             "image": "上天下澤，君子以辨上下定民志",          "weather_persona": "走在薄冰上的天氣 — 步伐放輕，老虎尾巴別亂踩。"},
    {"num": 11, "name": "地天泰",   "judgement": "小往大來，吉亨",                 "image": "天地交泰，後以財成天地之道",            "weather_persona": "陰陽調和的好天 — 順勢而為，事半功倍。"},
    {"num": 12, "name": "天地否",   "judgement": "否之匪人，不利君子貞",           "image": "天地不交，君子以儉德辟難",              "weather_persona": "悶熱不通風的一天 — 別硬推，先散熱再說。"},
    {"num": 13, "name": "天火同人", "judgement": "同人于野，亨，利涉大川，利君子貞", "image": "天與火，君子以類族辨物",                "weather_persona": "晴空映火的明朗日 — 找夥伴一起，比單幹更亮。"},
    {"num": 14, "name": "火天大有", "judgement": "元亨",                           "image": "火在天上，君子以遏惡揚善",              "weather_persona": "烈日當空照大地 — 收成在望，記得分享給身邊人。"},
    {"num": 15, "name": "地山謙",   "judgement": "亨，君子有終",                   "image": "地中有山，君子以裒多益寡",              "weather_persona": "山藏地下不顯眼 — 越低調越穩，別急著出頭。"},
    {"num": 16, "name": "雷地豫",   "judgement": "利建侯行師",                     "image": "雷出地奮，先王以作樂崇德",              "weather_persona": "春雷震開大地 — 有節奏地動起來，會被推著走。"},
    {"num": 17, "name": "澤雷隨",   "judgement": "元亨利貞，無咎",                 "image": "澤中有雷，君子以嚮晦入宴息",            "weather_persona": "雷在水下震盪 — 跟著節氣走，硬扭只會兩敗俱傷。"},
    {"num": 18, "name": "山風蠱",   "judgement": "元亨，利涉大川，先甲三日後甲三日", "image": "山下有風，君子以振民育德",              "weather_persona": "山下吹腐風 — 該清理的舊事就動手，別再拖。"},
    {"num": 19, "name": "地澤臨",   "judgement": "元亨利貞，至于八月有凶",         "image": "澤上有地，君子以教思無窮",              "weather_persona": "澤潤大地的春日 — 機會正到位，伸手抓得住。"},
    {"num": 20, "name": "風地觀",   "judgement": "盥而不薦，有孚顒若",             "image": "風行地上，先王以省方觀民設教",          "weather_persona": "風吹過大地的一天 — 多看少動，看清才下決定。"},
    {"num": 21, "name": "火雷噬嗑", "judgement": "亨，利用獄",                     "image": "雷電噬嗑，先王以明罰敕法",              "weather_persona": "雷電交擊的一天 — 卡住的事就強硬咬開，別含糊。"},
    {"num": 22, "name": "山火賁",   "judgement": "亨，小利有攸往",                 "image": "山下有火，君子以明庶政",                "weather_persona": "山下夕陽染晚霞 — 把場面妝點一下，效果加倍。"},
    {"num": 23, "name": "山地剝",   "judgement": "不利有攸往",                     "image": "山附於地，上以厚下安宅",                "weather_persona": "風吹葉落的尾聲 — 該收的就收，別逞強。"},
    {"num": 24, "name": "地雷復",   "judgement": "亨，出入無疾，朋來無咎",         "image": "雷在地中，先王以至日閉關",              "weather_persona": "寒冬中的初春雷 — 一切重新開始，慢慢來就好。"},
    {"num": 25, "name": "天雷無妄", "judgement": "元亨利貞，其匪正有眚",           "image": "天下雷行，先王以茂對時育萬物",          "weather_persona": "晴天霹靂的一天 — 守本分，別亂動才不會中招。"},
    {"num": 26, "name": "山天大畜", "judgement": "利貞，不家食吉，利涉大川",       "image": "天在山中，君子以多識前言往行",          "weather_persona": "高山藏住雲氣 — 蓄夠能量再出手，不急著放。"},
    {"num": 27, "name": "山雷頤",   "judgement": "貞吉，觀頤，自求口實",           "image": "山下有雷，君子以慎言語節飲食",          "weather_persona": "山中迴響的悶雷 — 顧好嘴和心，吃喝言行都別過。"},
    {"num": 28, "name": "澤風大過", "judgement": "棟橈，利有攸往，亨",             "image": "澤滅木，君子以獨立不懼",                "weather_persona": "颱風過境的一天 — 樑都要彎了，先挺住別硬撐。"},
    {"num": 29, "name": "坎為水",   "judgement": "有孚，維心亨，行有尚",           "image": "水洊至，君子以常德行習教事",            "weather_persona": "連日豪雨的一天 — 險中再險，唯有信念能渡。"},
    {"num": 30, "name": "離為火",   "judgement": "利貞，亨，畜牝牛吉",             "image": "明兩作，君子以繼明照于四方",            "weather_persona": "正午豔陽的一天 — 光鮮亮眼，但小心過熱。"},
    {"num": 31, "name": "澤山咸",   "judgement": "亨利貞，取女吉",                 "image": "山上有澤，君子以虛受人",                "weather_persona": "山頂湖面起漣漪 — 心動就是時候，順著感覺走。"},
    {"num": 32, "name": "雷風恆",   "judgement": "亨，無咎，利貞，利有攸往",       "image": "雷風恆，君子以立不易方",                "weather_persona": "風雷成習的日常 — 持續做小事，時間會給你答案。"},
    {"num": 33, "name": "天山遯",   "judgement": "亨，小利貞",                     "image": "天下有山，君子以遠小人",                "weather_persona": "山頂雲層退散時 — 該走就走，別戀棧不放。"},
    {"num": 34, "name": "雷天大壯", "judgement": "利貞",                           "image": "雷在天上，君子以非禮弗履",              "weather_persona": "雷響徹天的一天 — 力氣很夠，但別硬碰玻璃牆。"},
    {"num": 35, "name": "火地晉",   "judgement": "康侯用錫馬蕃庶，晝日三接",       "image": "明出地上，君子以自昭明德",              "weather_persona": "太陽從地平線升 — 順勢往上走，光自然照來。"},
    {"num": 36, "name": "地火明夷", "judgement": "利艱貞",                         "image": "明入地中，君子以蒞眾用晦而明",          "weather_persona": "太陽落入地下 — 暫時收光韜晦，別當顯眼包。"},
    {"num": 37, "name": "風火家人", "judgement": "利女貞",                         "image": "風自火出，君子以言有物而行有恆",        "weather_persona": "風助爐火的暖日 — 顧好家裡，外頭風大不重要。"},
    {"num": 38, "name": "火澤睽",   "judgement": "小事吉",                         "image": "上火下澤，君子以同而異",                "weather_persona": "火往上澤往下 — 想法不同很正常，求同存異。"},
    {"num": 39, "name": "水山蹇",   "judgement": "利西南，不利東北，利見大人，貞吉", "image": "山上有水，君子以反身修德",              "weather_persona": "高山積水難通行 — 此路不通就繞，別硬闖。"},
    {"num": 40, "name": "雷水解",   "judgement": "利西南，無所往，其來復吉",       "image": "雷雨作，君子以赦過宥罪",                "weather_persona": "雷雨後的放晴 — 結卡開了，動作要快不留尾。"},
    {"num": 41, "name": "山澤損",   "judgement": "有孚，元吉，無咎，可貞",         "image": "山下有澤，君子以懲忿窒欲",              "weather_persona": "山下水位下降 — 該捨就捨，留必要的就好。"},
    {"num": 42, "name": "風雷益",   "judgement": "利有攸往，利涉大川",             "image": "風雷益，君子以見善則遷有過則改",        "weather_persona": "風助雷威的一天 — 看到好的就學，看到錯的就改。"},
    {"num": 43, "name": "澤天夬",   "judgement": "揚于王庭，孚號，有厲",           "image": "澤上于天，君子以施祿及下",              "weather_persona": "高雲積水欲傾 — 該決斷就決斷，別讓它懸著。"},
    {"num": 44, "name": "天風姤",   "judgement": "女壯，勿用取女",                 "image": "天下有風，后以施命誥四方",              "weather_persona": "高空忽起的微風 — 偶遇別當定數，看清再說。"},
    {"num": 45, "name": "澤地萃",   "judgement": "亨，王假有廟，利見大人，亨利貞", "image": "澤上於地，君子以除戎器戒不虞",          "weather_persona": "澤水匯入低地 — 把人聚起來，也要備好應變。"},
    {"num": 46, "name": "地風升",   "judgement": "元亨，用見大人，勿恤，南征吉",   "image": "地中生木，君子以順德積小以高大",        "weather_persona": "地中草木向上長 — 一步一步往上走，不必急。"},
    {"num": 47, "name": "澤水困",   "judgement": "亨，貞大人吉，無咎",             "image": "澤無水，君子以致命遂志",                "weather_persona": "池子滲乾的一天 — 暫時沒水也別慌，守住嘴別亂講。"},
    {"num": 48, "name": "水風井",   "judgement": "改邑不改井，無喪無得，往來井井", "image": "木上有水，君子以勞民勸相",              "weather_persona": "井水恆湧的日子 — 該分享就分享，越用越清。"},
    {"num": 49, "name": "澤火革",   "judgement": "己日乃孚，元亨利貞，悔亡",       "image": "澤中有火，君子以治曆明時",              "weather_persona": "池中起火的奇日 — 該變就變，舊規矩別捨不得。"},
    {"num": 50, "name": "火風鼎",   "judgement": "元吉，亨",                       "image": "木上有火，君子以正位凝命",              "weather_persona": "爐火慢燉的時刻 — 把材料配好，火候到自然成。"},
    {"num": 51, "name": "震為雷",   "judgement": "亨，震來虩虩，笑言啞啞",         "image": "洊雷震，君子以恐懼修省",                "weather_persona": "連環炸雷的一天 — 嚇到正常，定下心來照常做。"},
    {"num": 52, "name": "艮為山",   "judgement": "艮其背，不獲其身，行其庭，不見其人", "image": "兼山艮，君子以思不出其位",              "weather_persona": "兩山相疊不動 — 該停就停，硬走只會撞牆。"},
    {"num": 53, "name": "風山漸",   "judgement": "女歸吉，利貞",                   "image": "山上有木，君子以居賢德善俗",            "weather_persona": "山頂樹苗緩緩長 — 慢慢來比較快，別求速成。"},
    {"num": 54, "name": "雷澤歸妹", "judgement": "征凶，無攸利",                   "image": "澤上有雷，君子以永終知敝",              "weather_persona": "雷在水面震盪 — 走偏了就承認，硬撐只會更亂。"},
    {"num": 55, "name": "雷火豐",   "judgement": "亨，王假之，勿憂，宜日中",       "image": "雷電皆至，君子以折獄致刑",              "weather_persona": "雷電交加的盛夏 — 趁正午太陽行事，別等夕陽。"},
    {"num": 56, "name": "火山旅",   "judgement": "小亨，旅貞吉",                   "image": "山上有火，君子以明慎用刑",              "weather_persona": "山上篝火的夜晚 — 在外漂泊要謙和，別惹是非。"},
    {"num": 57, "name": "巽為風",   "judgement": "小亨，利有攸往，利見大人",       "image": "隨風巽，君子以申命行事",                "weather_persona": "微風不停的一天 — 滲透比強攻有效，慢慢來。"},
    {"num": 58, "name": "兌為澤",   "judgement": "亨，利貞",                       "image": "麗澤兌，君子以朋友講習",                "weather_persona": "兩湖相連的明媚 — 多和朋友聊聊，心會更開闊。"},
    {"num": 59, "name": "風水渙",   "judgement": "亨，王假有廟，利涉大川，利貞",   "image": "風行水上，先王以享于帝立廟",            "weather_persona": "風吹散水面波紋 — 鬱結要散開，找個出口透氣。"},
    {"num": 60, "name": "水澤節",   "judgement": "亨，苦節不可貞",                 "image": "澤上有水，君子以制數度議德行",          "weather_persona": "水流入澤有節奏 — 該停就停，過度反而傷自己。"},
    {"num": 61, "name": "風澤中孚", "judgement": "豚魚吉，利涉大川，利貞",         "image": "澤上有風，君子以議獄緩死",              "weather_persona": "風吹湖面起漣漪 — 真心換真心，騙不過自己。"},
    {"num": 62, "name": "雷山小過", "judgement": "亨，利貞，可小事，不可大事",     "image": "山上有雷，君子以行過乎恭",              "weather_persona": "山頂打雷的一天 — 小事可放，大事別冒進。"},
    {"num": 63, "name": "水火既濟", "judgement": "亨小，利貞，初吉終亂",           "image": "水在火上，君子以思患而豫防之",          "weather_persona": "水滅火的平衡點 — 看似圓滿，更要小心走完。"},
    {"num": 64, "name": "火水未濟", "judgement": "亨。小狐汔濟，濡其尾",           "image": "火在水上，君子以慎辨物居方",            "weather_persona": "雨後仍未天晴 — 結尾比開頭難，再多走一哩。"},
]


def get(num: int) -> dict:
    if not (1 <= num <= 64):
        raise ValueError(f"hexagram num must be 1..64, got {num}")
    return HEXAGRAMS[num - 1]

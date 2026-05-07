# backend/app/services/divination/yao_ci.py
"""384-row 爻辭 lookup table (64 卦 × 6 爻).

原文 (original) 出自《周易》爻辭 — 先秦典籍，公共領域。
白話 (vernacular) 為 AI 輔助生成 + 人工校對結果（CC-BY-SA 4.0 標註）。
"""

from app.schemas.day_insight import YaoCiEntry


# Key: (hex_num, line_pos), where line_pos 1=初爻, 6=上爻
YAO_CI: dict[tuple[int, int], YaoCiEntry] = {
    # ---------- 卦 1 乾為天 ----------
    (1, 1): YaoCiEntry(
        original="初九：潛龍勿用。",
        vernacular="深水裡的龍，先別動 — 時機未到，沉潛蓄力比逞強更聰明。",
    ),
    (1, 2): YaoCiEntry(
        original="九二：見龍在田，利見大人。",
        vernacular="龍開始浮現，宜尋覓貴人或合作夥伴 — 不是孤軍時候。",
    ),
    (1, 3): YaoCiEntry(
        original="九三：君子終日乾乾，夕惕若厲，無咎。",
        vernacular="白天卯足全力、晚上仍警戒檢視 — 這樣的勤勉才能化險為夷。",
    ),
    (1, 4): YaoCiEntry(
        original="九四：或躍在淵，無咎。",
        vernacular="該躍出還是退守？兩可之間，憑直覺抉擇皆無咎。",
    ),
    (1, 5): YaoCiEntry(
        original="九五：飛龍在天，利見大人。",
        vernacular="勢頭最盛之時，正是擴大格局、結交同等量級的人的時刻。",
    ),
    (1, 6): YaoCiEntry(
        original="上九：亢龍有悔。",
        vernacular="飛得太高的龍，會懊悔 — 物極必反，懂得收斂才是真本事。",
    ),
    # ---------- 卦 2 坤為地 ----------
    (2, 1): YaoCiEntry(
        original="初六：履霜，堅冰至。",
        vernacular="踩到第一片霜，就知道嚴冬將至 — 從微小徵兆讀出大趨勢。",
    ),
    (2, 2): YaoCiEntry(
        original="六二：直方大，不習無不利。",
        vernacular="正直、方正、寬大這三個本性夠了 — 不必刻意修飾，自然順遂。",
    ),
    (2, 3): YaoCiEntry(
        original="六三：含章可貞，或從王事，無成有終。",
        vernacular="懷藏才華靜守正道，即便代人辦事不居功，也會有好結局。",
    ),
    (2, 4): YaoCiEntry(
        original="六四：括囊，無咎無譽。",
        vernacular="把袋口紮緊 — 該沉默的時候沉默，沒讚也沒罵就是上策。",
    ),
    (2, 5): YaoCiEntry(
        original="六五：黃裳，元吉。",
        vernacular="居中的黃色內裳象徵謙退守中 — 大吉。",
    ),
    (2, 6): YaoCiEntry(
        original="上六：龍戰于野，其血玄黃。",
        vernacular="陰盛至極與陽相搏 — 兩敗俱傷的場面，宜避其鋒。",
    ),
    # ---------- 卦 3 水雷屯 ----------
    (3, 1): YaoCiEntry(
        original="初九：磐桓，利居貞，利建侯。",
        vernacular="開局徘徊不定，留在原地守正反而有利，也適合奠基立業。",
    ),
    (3, 2): YaoCiEntry(
        original="六二：屯如邅如，乘馬班如。匪寇婚媾，女子貞不字，十年乃字。",
        vernacular="進退維谷，車馬徘徊。對方不是敵人是求婚者 — 但十年後才會回應。",
    ),
    (3, 3): YaoCiEntry(
        original="六三：即鹿無虞，惟入于林中。君子幾不如舍，往吝。",
        vernacular="無嚮導獵鹿只會迷失叢林。君子當知見機放手，硬闖會有遺憾。",
    ),
    (3, 4): YaoCiEntry(
        original="六四：乘馬班如，求婚媾，往吉，無不利。",
        vernacular="徘徊之時若主動求結盟，前往大吉、無往不利。",
    ),
    (3, 5): YaoCiEntry(
        original="九五：屯其膏，小貞吉，大貞凶。",
        vernacular="囤積資源該散卻不散 — 小事守正吉，大事守舊凶。",
    ),
    (3, 6): YaoCiEntry(
        original="上六：乘馬班如，泣血漣如。",
        vernacular="徘徊到最後，血淚漣漣 — 此時當斷不斷反受其亂。",
    ),
    # ---------- 卦 4 山水蒙 ----------
    (4, 1): YaoCiEntry(
        original="初六：發蒙，利用刑人，用說桎梏，以往吝。",
        vernacular="啟蒙之初要立規矩，先嚴後鬆才有效；一味放任只會留下遺憾。",
    ),
    (4, 2): YaoCiEntry(
        original="九二：包蒙吉，納婦吉，子克家。",
        vernacular="以寬厚包容無知者吉，迎娶賢內助吉 — 後輩也能撐起家業。",
    ),
    (4, 3): YaoCiEntry(
        original="六三：勿用取女，見金夫，不有躬，無攸利。",
        vernacular="別娶這樣的對象 — 見錢就忘本的人，跟誰都沒好結果。",
    ),
    (4, 4): YaoCiEntry(
        original="六四：困蒙，吝。",
        vernacular="陷在自己的無知裡又拒絕學習 — 困窘可惜。",
    ),
    (4, 5): YaoCiEntry(
        original="六五：童蒙，吉。",
        vernacular="保有像孩童一樣謙虛求教的心，最吉。",
    ),
    (4, 6): YaoCiEntry(
        original="上九：擊蒙，不利為寇，利禦寇。",
        vernacular="嚴厲糾正無知者，不要當侵略者，而是當防守者 — 才是正道。",
    ),
    # ---------- 卦 5 水天需 ----------
    (5, 1): YaoCiEntry(
        original="初九：需于郊，利用恆，無咎。",
        vernacular="在城郊外耐心等待，保持恆心 — 沒什麼錯。",
    ),
    (5, 2): YaoCiEntry(
        original="九二：需于沙，小有言，終吉。",
        vernacular="等在沙地有點接近危險，雖有小小口舌是非，最後仍吉。",
    ),
    (5, 3): YaoCiEntry(
        original="九三：需于泥，致寇至。",
        vernacular="陷在泥地裡硬等，等於招來盜匪 — 該動就動。",
    ),
    (5, 4): YaoCiEntry(
        original="六四：需于血，出自穴。",
        vernacular="已經受傷流血，仍能脫離險穴 — 識時務為俊傑。",
    ),
    (5, 5): YaoCiEntry(
        original="九五：需于酒食，貞吉。",
        vernacular="從容地等，邊吃邊喝邊耐心觀察 — 守正則吉。",
    ),
    (5, 6): YaoCiEntry(
        original="上六：入于穴，有不速之客三人來，敬之終吉。",
        vernacular="退守洞穴卻來了三位不速之客 — 以禮相待，終究吉祥。",
    ),
    # ---------- 卦 6 天水訟 ----------
    (6, 1): YaoCiEntry(
        original="初六：不永所事，小有言，終吉。",
        vernacular="爭執別拖太久，雖有口角，及早收手反而吉。",
    ),
    (6, 2): YaoCiEntry(
        original="九二：不克訟，歸而逋，其邑人三百戶，無眚。",
        vernacular="打不贏這官司就趕快撤退回家 — 小規模避禍，沒有大災。",
    ),
    (6, 3): YaoCiEntry(
        original="六三：食舊德，貞厲，終吉。或從王事，無成。",
        vernacular="守住舊有的本份吃飯，雖危守正最終吉；幫人辦事別爭功。",
    ),
    (6, 4): YaoCiEntry(
        original="九四：不克訟，復即命，渝安貞，吉。",
        vernacular="打不贏官司，回來面對命運、改變態度安守正道 — 吉。",
    ),
    (6, 5): YaoCiEntry(
        original="九五：訟，元吉。",
        vernacular="有公正大人主持訴訟 — 大吉。",
    ),
    (6, 6): YaoCiEntry(
        original="上九：或錫之鞶帶，終朝三褫之。",
        vernacular="爭來的榮譽腰帶，一天之內被剝三次 — 靠爭奪得來的不長久。",
    ),
    # ---------- 卦 7 地水師 ----------
    (7, 1): YaoCiEntry(
        original="初六：師出以律，否臧凶。",
        vernacular="出兵要紀律嚴明 — 散漫無章必凶。",
    ),
    (7, 2): YaoCiEntry(
        original="九二：在師中，吉，無咎，王三錫命。",
        vernacular="率師居中得宜 — 吉而無咎，獲長官三度嘉獎。",
    ),
    (7, 3): YaoCiEntry(
        original="六三：師或輿尸，凶。",
        vernacular="軍中載著屍體回來 — 大凶之兆，宜檢討領導。",
    ),
    (7, 4): YaoCiEntry(
        original="六四：師左次，無咎。",
        vernacular="部隊往後撤紮營 — 識時務的退守，沒過錯。",
    ),
    (7, 5): YaoCiEntry(
        original="六五：田有禽，利執言，無咎。長子帥師，弟子輿尸，貞凶。",
        vernacular="田裡有獸宜出兵討伐；老將帶兵吉，新手亂指揮就慘了。",
    ),
    (7, 6): YaoCiEntry(
        original="上六：大君有命，開國承家，小人勿用。",
        vernacular="主君論功封賞，建邦繼業 — 但小人別重用。",
    ),
    # ---------- 卦 8 水地比 ----------
    (8, 1): YaoCiEntry(
        original="初六：有孚比之，無咎。有孚盈缶，終來有他吉。",
        vernacular="以誠信親近他人無咎；誠意滿盈如盛器，終有意外好運。",
    ),
    (8, 2): YaoCiEntry(
        original="六二：比之自內，貞吉。",
        vernacular="從內心發出的親近，守正則吉。",
    ),
    (8, 3): YaoCiEntry(
        original="六三：比之匪人。",
        vernacular="親近錯了人 — 慎選你的圈子。",
    ),
    (8, 4): YaoCiEntry(
        original="六四：外比之，貞吉。",
        vernacular="向外尋求好的依附，守正則吉。",
    ),
    (8, 5): YaoCiEntry(
        original="九五：顯比，王用三驅，失前禽，邑人不誡，吉。",
        vernacular="光明正大的親附，像王者三面圍獵留一條生路 — 寬厚則吉。",
    ),
    (8, 6): YaoCiEntry(
        original="上六：比之無首，凶。",
        vernacular="親近卻沒有首腦凝聚 — 一盤散沙，凶。",
    ),
    # ---------- 卦 9 風天小畜 ----------
    (9, 1): YaoCiEntry(
        original="初九：復自道，何其咎，吉。",
        vernacular="回到自己原本的道路上，能有什麼錯？吉。",
    ),
    (9, 2): YaoCiEntry(
        original="九二：牽復，吉。",
        vernacular="被同伴拉著一起回正道 — 吉。",
    ),
    (9, 3): YaoCiEntry(
        original="九三：輿說輻，夫妻反目。",
        vernacular="馬車輪輻脫落、夫妻反目相向 — 內部失和難前進。",
    ),
    (9, 4): YaoCiEntry(
        original="六四：有孚，血去惕出，無咎。",
        vernacular="心存誠信，血光散去、警惕解除 — 無咎。",
    ),
    (9, 5): YaoCiEntry(
        original="九五：有孚攣如，富以其鄰。",
        vernacular="誠信使人緊密相連 — 富裕也樂於分享給鄰人。",
    ),
    (9, 6): YaoCiEntry(
        original="上九：既雨既處，尚德載，婦貞厲。月幾望，君子征凶。",
        vernacular="雨落了該停了、累積過盛當警戒；陰盛之時君子妄動則凶。",
    ),
    # ---------- 卦 10 天澤履 ----------
    (10, 1): YaoCiEntry(
        original="初九：素履往，無咎。",
        vernacular="保持本色平實前行 — 沒事。",
    ),
    (10, 2): YaoCiEntry(
        original="九二：履道坦坦，幽人貞吉。",
        vernacular="走在平坦大道上 — 隱士守正自得其樂。",
    ),
    (10, 3): YaoCiEntry(
        original="六三：眇能視，跛能履，履虎尾，咥人，凶。武人為于大君。",
        vernacular="自不量力踩老虎尾巴必被咬 — 武夫想當王者，註定凶。",
    ),
    (10, 4): YaoCiEntry(
        original="九四：履虎尾，愬愬，終吉。",
        vernacular="踩到老虎尾巴卻戰戰兢兢 — 警覺謹慎反而能脫險，終吉。",
    ),
    (10, 5): YaoCiEntry(
        original="九五：夬履，貞厲。",
        vernacular="果決前行，守正仍要警覺潛在風險。",
    ),
    (10, 6): YaoCiEntry(
        original="上九：視履考祥，其旋元吉。",
        vernacular="回頭檢視走過的路、衡量吉凶 — 圓滿循環，大吉。",
    ),
    # ---------- 卦 11 地天泰 ----------
    (11, 1): YaoCiEntry(
        original="初九：拔茅茹，以其彙，征吉。",
        vernacular="連根拔起的茅草帶著同類 — 揪團一起前進，吉。",
    ),
    (11, 2): YaoCiEntry(
        original="九二：包荒，用馮河，不遐遺，朋亡，得尚于中行。",
        vernacular="氣度包容、敢渡大河、不忘遠人、不結黨 — 中道而行受推崇。",
    ),
    (11, 3): YaoCiEntry(
        original="九三：無平不陂，無往不復。艱貞無咎，勿恤其孚，于食有福。",
        vernacular="沒有不轉彎的平地、沒有去而不回的路 — 艱守正道有福。",
    ),
    (11, 4): YaoCiEntry(
        original="六四：翩翩，不富以其鄰，不戒以孚。",
        vernacular="輕盈下降不靠財富招來鄰人 — 全憑真誠相待。",
    ),
    (11, 5): YaoCiEntry(
        original="六五：帝乙歸妹，以祉元吉。",
        vernacular="帝乙嫁妹下嫁臣下 — 不擺架子帶來大福，元吉。",
    ),
    (11, 6): YaoCiEntry(
        original="上六：城復于隍，勿用師，自邑告命，貞吝。",
        vernacular="城牆崩塌回填溝壑 — 此時別動兵，自我反省，守正以避憾。",
    ),
    # ---------- 卦 12 天地否 ----------
    (12, 1): YaoCiEntry(
        original="初六：拔茅茹，以其彙，貞吉，亨。",
        vernacular="拔茅草連根帶同類 — 守正則吉，亨通。",
    ),
    (12, 2): YaoCiEntry(
        original="六二：包承，小人吉，大人否，亨。",
        vernacular="包容承奉 — 小人吉、大人卻被閉塞，但仍能亨通。",
    ),
    (12, 3): YaoCiEntry(
        original="六三：包羞。",
        vernacular="包藏羞恥 — 此時宜內省。",
    ),
    (12, 4): YaoCiEntry(
        original="九四：有命無咎，疇離祉。",
        vernacular="奉天命行事無咎 — 同類也一起得福。",
    ),
    (12, 5): YaoCiEntry(
        original="九五：休否，大人吉。其亡其亡，繫于苞桑。",
        vernacular="閉塞將解，大人吉 — 隨時居安思危，繫如苞桑般穩固。",
    ),
    (12, 6): YaoCiEntry(
        original="上九：傾否，先否後喜。",
        vernacular="閉塞徹底傾覆 — 先苦後甜。",
    ),
    # ---------- 卦 13 天火同人 ----------
    (13, 1): YaoCiEntry(
        original="初九：同人于門，無咎。",
        vernacular="在門口就與人結交 — 開放公平，無咎。",
    ),
    (13, 2): YaoCiEntry(
        original="六二：同人于宗，吝。",
        vernacular="只跟自家宗親結交 — 圈子太窄，可惜。",
    ),
    (13, 3): YaoCiEntry(
        original="九三：伏戎于莽，升其高陵，三歲不興。",
        vernacular="埋兵草叢、登高觀望 — 三年都動不起來，不宜輕舉妄動。",
    ),
    (13, 4): YaoCiEntry(
        original="九四：乘其墉，弗克攻，吉。",
        vernacular="登上城牆又克制不攻 — 有所節制反而吉。",
    ),
    (13, 5): YaoCiEntry(
        original="九五：同人，先號咷而後笑，大師克相遇。",
        vernacular="與心意相通的人，先哭後笑 — 大軍會師，相見終得償。",
    ),
    (13, 6): YaoCiEntry(
        original="上九：同人于郊，無悔。",
        vernacular="在郊外與人結交，雖偏遠卻無悔。",
    ),
    # ---------- 卦 14 火天大有 ----------
    (14, 1): YaoCiEntry(
        original="初九：無交害，匪咎，艱則無咎。",
        vernacular="不與害事沾邊就沒過錯 — 處境艱難就更要守正。",
    ),
    (14, 2): YaoCiEntry(
        original="九二：大車以載，有攸往，無咎。",
        vernacular="大車裝載重物前行 — 有去處、能勝任，無咎。",
    ),
    (14, 3): YaoCiEntry(
        original="九三：公用亨于天子，小人弗克。",
        vernacular="諸侯朝見天子奉獻 — 小人沒這份氣度。",
    ),
    (14, 4): YaoCiEntry(
        original="九四：匪其彭，無咎。",
        vernacular="不過度張揚自己的盛勢 — 收斂則無咎。",
    ),
    (14, 5): YaoCiEntry(
        original="六五：厥孚交如，威如，吉。",
        vernacular="以誠信相交、保持威嚴 — 吉。",
    ),
    (14, 6): YaoCiEntry(
        original="上九：自天祐之，吉無不利。",
        vernacular="得天保佑 — 吉，無往不利。",
    ),
    # ---------- 卦 15 地山謙 ----------
    (15, 1): YaoCiEntry(
        original="初六：謙謙君子，用涉大川，吉。",
        vernacular="謙虛再謙虛的君子，能涉險渡大川 — 吉。",
    ),
    (15, 2): YaoCiEntry(
        original="六二：鳴謙，貞吉。",
        vernacular="謙虛之名外揚 — 守正則吉。",
    ),
    (15, 3): YaoCiEntry(
        original="九三：勞謙君子，有終吉。",
        vernacular="既勤勞又謙遜的君子 — 善始善終，吉。",
    ),
    (15, 4): YaoCiEntry(
        original="六四：無不利，撝謙。",
        vernacular="發揮謙遜的態度 — 無往不利。",
    ),
    (15, 5): YaoCiEntry(
        original="六五：不富以其鄰，利用侵伐，無不利。",
        vernacular="不靠富有就能凝聚鄰人 — 此時出兵討伐也無往不利。",
    ),
    (15, 6): YaoCiEntry(
        original="上六：鳴謙，利用行師，征邑國。",
        vernacular="謙德彰顯天下 — 此時動員整頓內部，仍合宜。",
    ),
    # ---------- 卦 16 雷地豫 ----------
    (16, 1): YaoCiEntry(
        original="初六：鳴豫，凶。",
        vernacular="得意忘形大聲炫耀 — 凶。",
    ),
    (16, 2): YaoCiEntry(
        original="六二：介于石，不終日，貞吉。",
        vernacular="像石頭一樣堅定，不待一日就見機行事 — 守正則吉。",
    ),
    (16, 3): YaoCiEntry(
        original="六三：盱豫，悔。遲有悔。",
        vernacular="諂媚奉承求逸樂 — 悔；拖延不改更後悔。",
    ),
    (16, 4): YaoCiEntry(
        original="九四：由豫，大有得。勿疑，朋盍簪。",
        vernacular="眾人因你而樂 — 大有所得；別猶豫，朋友自然集結。",
    ),
    (16, 5): YaoCiEntry(
        original="六五：貞疾，恆不死。",
        vernacular="長期病痛纏身但不致死 — 守正能挺過來。",
    ),
    (16, 6): YaoCiEntry(
        original="上六：冥豫，成有渝，無咎。",
        vernacular="沉迷享樂到極點 — 若能改變仍可無咎。",
    ),
    # ---------- 卦 17 澤雷隨 ----------
    (17, 1): YaoCiEntry(
        original="初九：官有渝，貞吉。出門交有功。",
        vernacular="當權者有變動，守正則吉 — 出門廣結善緣會有成果。",
    ),
    (17, 2): YaoCiEntry(
        original="六二：係小子，失丈夫。",
        vernacular="跟錯了輕浮的小子，反而錯失成熟可靠的人。",
    ),
    (17, 3): YaoCiEntry(
        original="六三：係丈夫，失小子。隨有求得，利居貞。",
        vernacular="跟對了成熟的人 — 跟隨求取則有所得，宜守正。",
    ),
    (17, 4): YaoCiEntry(
        original="九四：隨有獲，貞凶。有孚在道，以明，何咎。",
        vernacular="跟隨而有大收穫 — 過盛則凶；保持誠信走正道又何咎？",
    ),
    (17, 5): YaoCiEntry(
        original="九五：孚于嘉，吉。",
        vernacular="誠信於善美之人事 — 吉。",
    ),
    (17, 6): YaoCiEntry(
        original="上六：拘係之，乃從維之。王用亨于西山。",
        vernacular="緊緊拘繫追隨者 — 如王者祭於西山般虔誠團結。",
    ),
    # ---------- 卦 18 山風蠱 ----------
    (18, 1): YaoCiEntry(
        original="初六：幹父之蠱，有子，考無咎，厲終吉。",
        vernacular="承擔修正父輩的弊病 — 雖危險，最終吉。",
    ),
    (18, 2): YaoCiEntry(
        original="九二：幹母之蠱，不可貞。",
        vernacular="處理母親留下的問題 — 不宜過剛硬，要圓融。",
    ),
    (18, 3): YaoCiEntry(
        original="九三：幹父之蠱，小有悔，無大咎。",
        vernacular="處理父輩遺留問題 — 雖有小悔，無大過錯。",
    ),
    (18, 4): YaoCiEntry(
        original="六四：裕父之蠱，往見吝。",
        vernacular="姑息對待父輩弊病 — 遲早會見遺憾。",
    ),
    (18, 5): YaoCiEntry(
        original="六五：幹父之蠱，用譽。",
        vernacular="以美譽的方式繼承並修正父輩之事 — 兩全其美。",
    ),
    (18, 6): YaoCiEntry(
        original="上九：不事王侯，高尚其事。",
        vernacular="不依附權貴，自做高尚之事 — 隱士風骨。",
    ),
    # ---------- 卦 19 地澤臨 ----------
    (19, 1): YaoCiEntry(
        original="初九：咸臨，貞吉。",
        vernacular="以感應之心親近他人 — 守正則吉。",
    ),
    (19, 2): YaoCiEntry(
        original="九二：咸臨，吉，無不利。",
        vernacular="以真誠感應親近 — 吉，無不利。",
    ),
    (19, 3): YaoCiEntry(
        original="六三：甘臨，無攸利。既憂之，無咎。",
        vernacular="用甜言蜜語靠近 — 沒好處；能警覺反省則無咎。",
    ),
    (19, 4): YaoCiEntry(
        original="六四：至臨，無咎。",
        vernacular="用最誠摯的態度親近 — 無咎。",
    ),
    (19, 5): YaoCiEntry(
        original="六五：知臨，大君之宜，吉。",
        vernacular="以智慧駕馭親臨 — 大領導者的氣度，吉。",
    ),
    (19, 6): YaoCiEntry(
        original="上六：敦臨，吉，無咎。",
        vernacular="以敦厚的態度親近 — 吉、無咎。",
    ),
    # ---------- 卦 20 風地觀 ----------
    (20, 1): YaoCiEntry(
        original="初六：童觀，小人無咎，君子吝。",
        vernacular="像小孩看世界 — 平凡人沒事，但要做大事的人就太淺薄了。",
    ),
    (20, 2): YaoCiEntry(
        original="六二：闚觀，利女貞。",
        vernacular="從門縫窺看 — 視野受限，宜守內斂之道。",
    ),
    (20, 3): YaoCiEntry(
        original="六三：觀我生，進退。",
        vernacular="觀察自己作為，決定該進該退。",
    ),
    (20, 4): YaoCiEntry(
        original="六四：觀國之光，利用賓于王。",
        vernacular="觀察國家的氣象 — 適合作為賓客輔佐君王。",
    ),
    (20, 5): YaoCiEntry(
        original="九五：觀我生，君子無咎。",
        vernacular="反觀自己的作為 — 君子無咎。",
    ),
    (20, 6): YaoCiEntry(
        original="上九：觀其生，君子無咎。",
        vernacular="觀照他人或自身的整體生命 — 君子無咎。",
    ),
    # ---------- 卦 21 火雷噬嗑 ----------
    (21, 1): YaoCiEntry(
        original="初九：屨校滅趾，無咎。",
        vernacular="腳上戴著木枷蓋住腳趾 — 小懲大誡，無咎。",
    ),
    (21, 2): YaoCiEntry(
        original="六二：噬膚滅鼻，無咎。",
        vernacular="咬肉太深沒了鼻子 — 用力過猛但仍可挽回，無咎。",
    ),
    (21, 3): YaoCiEntry(
        original="六三：噬腊肉，遇毒，小吝，無咎。",
        vernacular="咬到陳年肉乾遇到毒 — 小有遺憾，仍無大過。",
    ),
    (21, 4): YaoCiEntry(
        original="九四：噬乾胏，得金矢，利艱貞，吉。",
        vernacular="咬硬肉骨頭得到金箭 — 艱難中守正則吉。",
    ),
    (21, 5): YaoCiEntry(
        original="六五：噬乾肉，得黃金，貞厲，無咎。",
        vernacular="咬乾肉得黃金 — 守正雖危，能避過錯。",
    ),
    (21, 6): YaoCiEntry(
        original="上九：何校滅耳，凶。",
        vernacular="頸上枷鎖蓋過耳朵 — 罪重不聽勸，凶。",
    ),
    # ---------- 卦 22 山火賁 ----------
    (22, 1): YaoCiEntry(
        original="初九：賁其趾，舍車而徒。",
        vernacular="只裝飾自己的腳趾 — 棄車步行，務實樸素。",
    ),
    (22, 2): YaoCiEntry(
        original="六二：賁其須。",
        vernacular="修飾自己的鬍鬚 — 隨人主動，有所附麗。",
    ),
    (22, 3): YaoCiEntry(
        original="九三：賁如濡如，永貞吉。",
        vernacular="文采華美又溫潤 — 長保正道則吉。",
    ),
    (22, 4): YaoCiEntry(
        original="六四：賁如皤如，白馬翰如。匪寇婚媾。",
        vernacular="素白文飾、白馬翩翩 — 來者不是賊，是求婚者。",
    ),
    (22, 5): YaoCiEntry(
        original="六五：賁于丘園，束帛戔戔，吝終吉。",
        vernacular="樸素裝飾於山丘田園，禮帛雖薄 — 雖小有可惜，最終吉。",
    ),
    (22, 6): YaoCiEntry(
        original="上九：白賁，無咎。",
        vernacular="返樸歸真，純白無修飾 — 無咎。",
    ),
    # ---------- 卦 23 山地剝 ----------
    (23, 1): YaoCiEntry(
        original="初六：剝床以足，蔑貞凶。",
        vernacular="床腳開始被剝蝕 — 漠視守正則凶。",
    ),
    (23, 2): YaoCiEntry(
        original="六二：剝床以辨，蔑貞凶。",
        vernacular="床的支架也被剝蝕 — 漠視守正則凶。",
    ),
    (23, 3): YaoCiEntry(
        original="六三：剝之，無咎。",
        vernacular="處於剝蝕中卻能保持中正 — 無咎。",
    ),
    (23, 4): YaoCiEntry(
        original="六四：剝床以膚，凶。",
        vernacular="剝蝕已及人身肌膚 — 大凶迫在眉睫。",
    ),
    (23, 5): YaoCiEntry(
        original="六五：貫魚，以宮人寵，無不利。",
        vernacular="像魚串排序順從 — 引領眾人和諧，無不利。",
    ),
    (23, 6): YaoCiEntry(
        original="上九：碩果不食，君子得輿，小人剝廬。",
        vernacular="頂端碩果不被吃掉 — 君子得車駕、小人連屋頂都剝光。",
    ),
    # ---------- 卦 24 地雷復 ----------
    (24, 1): YaoCiEntry(
        original="初九：不遠復，無祇悔，元吉。",
        vernacular="走不遠就回頭 — 沒大悔，元吉。",
    ),
    (24, 2): YaoCiEntry(
        original="六二：休復，吉。",
        vernacular="美好地回歸 — 吉。",
    ),
    (24, 3): YaoCiEntry(
        original="六三：頻復，厲無咎。",
        vernacular="一再地回頭修正 — 雖危險，無大過。",
    ),
    (24, 4): YaoCiEntry(
        original="六四：中行獨復。",
        vernacular="眾人之中獨自走回正道 — 知錯能改的勇氣。",
    ),
    (24, 5): YaoCiEntry(
        original="六五：敦復，無悔。",
        vernacular="以敦厚之心回歸 — 無悔。",
    ),
    (24, 6): YaoCiEntry(
        original="上六：迷復，凶，有災眚。用行師，終有大敗，以其國君凶，至于十年不克征。",
        vernacular="迷失而不知歸 — 大凶，動兵必敗，國君遭殃，十年不能再戰。",
    ),
    # ---------- 卦 25 天雷無妄 ----------
    (25, 1): YaoCiEntry(
        original="初九：無妄，往吉。",
        vernacular="不妄為地前往 — 吉。",
    ),
    (25, 2): YaoCiEntry(
        original="六二：不耕穫，不菑畬，則利有攸往。",
        vernacular="不貪求未種就收 — 不刻意求取，反而適合前往。",
    ),
    (25, 3): YaoCiEntry(
        original="六三：無妄之災，或繫之牛，行人之得，邑人之災。",
        vernacular="意外飛來橫禍 — 路人撿到的牛，卻變成住戶被冤的災。",
    ),
    (25, 4): YaoCiEntry(
        original="九四：可貞，無咎。",
        vernacular="守正則無咎。",
    ),
    (25, 5): YaoCiEntry(
        original="九五：無妄之疾，勿藥有喜。",
        vernacular="無端而來的病 — 不必吃藥也會自癒。",
    ),
    (25, 6): YaoCiEntry(
        original="上九：無妄，行有眚，無攸利。",
        vernacular="妄動前行則有災 — 無利可言。",
    ),
    # ---------- 卦 26 山天大畜 ----------
    (26, 1): YaoCiEntry(
        original="初九：有厲，利已。",
        vernacular="前有危險 — 適時止步較好。",
    ),
    (26, 2): YaoCiEntry(
        original="九二：輿說輹，",
        vernacular="馬車輪軸脫落 — 暫停前行，避免衝撞。",
    ),
    (26, 3): YaoCiEntry(
        original="九三：良馬逐，利艱貞。曰閑輿衛，利有攸往。",
        vernacular="良馬奔逐 — 守正勤練、習車防衛，前往有利。",
    ),
    (26, 4): YaoCiEntry(
        original="六四：童牛之牿，元吉。",
        vernacular="幫小牛戴上橫木預防牴觸 — 防患於未然，大吉。",
    ),
    (26, 5): YaoCiEntry(
        original="六五：豶豕之牙，吉。",
        vernacular="閹割野豬制其牙利 — 從根源治理，吉。",
    ),
    (26, 6): YaoCiEntry(
        original="上九：何天之衢，亨。",
        vernacular="開通天衢大道 — 亨通。",
    ),
    # ---------- 卦 27 山雷頤 ----------
    (27, 1): YaoCiEntry(
        original="初九：舍爾靈龜，觀我朵頤，凶。",
        vernacular="放著靈龜寶物不要，眼巴巴看人吃喝 — 失本求外，凶。",
    ),
    (27, 2): YaoCiEntry(
        original="六二：顛頤，拂經于丘頤，征凶。",
        vernacular="顛倒養生求養於下又攀附於上 — 違反常理，前往凶。",
    ),
    (27, 3): YaoCiEntry(
        original="六三：拂頤貞凶，十年勿用，無攸利。",
        vernacular="違背養生之道 — 守正仍凶，十年不能成事。",
    ),
    (27, 4): YaoCiEntry(
        original="六四：顛頤吉。虎視眈眈，其欲逐逐，無咎。",
        vernacular="自下求養而吉 — 像虎注視獵物般專注追求，無咎。",
    ),
    (27, 5): YaoCiEntry(
        original="六五：拂經，居貞吉，不可涉大川。",
        vernacular="違背常經 — 安居守正則吉，不宜冒險渡大川。",
    ),
    (27, 6): YaoCiEntry(
        original="上九：由頤，厲吉，利涉大川。",
        vernacular="眾人靠你養活 — 雖危但吉，宜涉大川闖事業。",
    ),
    # ---------- 卦 28 澤風大過 ----------
    (28, 1): YaoCiEntry(
        original="初六：藉用白茅，無咎。",
        vernacular="用潔白茅草墊著行禮 — 慎重恭敬，無咎。",
    ),
    (28, 2): YaoCiEntry(
        original="九二：枯楊生稊，老夫得其女妻，無不利。",
        vernacular="枯楊發新芽、老翁得少妻 — 老樹開花，無不利。",
    ),
    (28, 3): YaoCiEntry(
        original="九三：棟橈，凶。",
        vernacular="梁柱彎曲變形 — 結構不穩，凶。",
    ),
    (28, 4): YaoCiEntry(
        original="九四：棟隆，吉，有它吝。",
        vernacular="梁柱挺立堅固 — 吉，但若旁生枝節則小有遺憾。",
    ),
    (28, 5): YaoCiEntry(
        original="九五：枯楊生華，老婦得其士夫，無咎無譽。",
        vernacular="枯楊開花、老婦得少夫 — 無大錯也無美名，平平。",
    ),
    (28, 6): YaoCiEntry(
        original="上六：過涉滅頂，凶，無咎。",
        vernacular="冒險渡水滅頂 — 為大義捨身，雖凶卻無罪。",
    ),
    # ---------- 卦 29 坎為水 ----------
    (29, 1): YaoCiEntry(
        original="初六：習坎，入于坎窞，凶。",
        vernacular="一險再險、跌進坑底 — 凶。",
    ),
    (29, 2): YaoCiEntry(
        original="九二：坎有險，求小得。",
        vernacular="險中求進，只能得小利 — 別貪。",
    ),
    (29, 3): YaoCiEntry(
        original="六三：來之坎坎，險且枕，入于坎窞，勿用。",
        vernacular="來來去去都是險 — 此時別輕舉妄動。",
    ),
    (29, 4): YaoCiEntry(
        original="六四：樽酒簋貳，用缶，納約自牖，終無咎。",
        vernacular="一樽酒、兩盆食、樸實器皿，從窗口送進去 — 簡約相處，終無咎。",
    ),
    (29, 5): YaoCiEntry(
        original="九五：坎不盈，祇既平，無咎。",
        vernacular="險水未滿，剛達平面 — 險將過，無咎。",
    ),
    (29, 6): YaoCiEntry(
        original="上六：係用徽纆，寘于叢棘，三歲不得，凶。",
        vernacular="被繩索捆綁丟在荊棘叢，三年都脫不了身 — 凶。",
    ),
    # ---------- 卦 30 離為火 ----------
    (30, 1): YaoCiEntry(
        original="初九：履錯然，敬之，無咎。",
        vernacular="開頭腳步雜亂 — 心存敬慎，便無咎。",
    ),
    (30, 2): YaoCiEntry(
        original="六二：黃離，元吉。",
        vernacular="居中和煦如黃光 — 元吉。",
    ),
    (30, 3): YaoCiEntry(
        original="九三：日昃之離，不鼓缶而歌，則大耋之嗟，凶。",
        vernacular="夕陽西下 — 不灑脫看開反而哀嘆衰老，凶。",
    ),
    (30, 4): YaoCiEntry(
        original="九四：突如其來如，焚如，死如，棄如。",
        vernacular="火勢突如其來 — 燒、死、棄三重災，慎避其鋒。",
    ),
    (30, 5): YaoCiEntry(
        original="六五：出涕沱若，戚嗟若，吉。",
        vernacular="涕淚交流、傷感長嘆 — 知憂則吉。",
    ),
    (30, 6): YaoCiEntry(
        original="上九：王用出征，有嘉折首，獲匪其醜，無咎。",
        vernacular="王者出征有功 — 只懲首惡、不擴大牽連，無咎。",
    ),
    # ---------- 卦 31 澤山咸 ----------
    (31, 1): YaoCiEntry(
        original="初六：咸其拇。",
        vernacular="感應只到大腳趾 — 微弱初動。",
    ),
    (31, 2): YaoCiEntry(
        original="六二：咸其腓，凶，居吉。",
        vernacular="感應到小腿就妄動 — 凶；安居不動則吉。",
    ),
    (31, 3): YaoCiEntry(
        original="九三：咸其股，執其隨，往吝。",
        vernacular="感應到大腿便盲從 — 跟風前往則可惜。",
    ),
    (31, 4): YaoCiEntry(
        original="九四：貞吉，悔亡。憧憧往來，朋從爾思。",
        vernacular="守正則吉、無悔；心思往來不定，朋友照樣循你心意而從。",
    ),
    (31, 5): YaoCiEntry(
        original="九五：咸其脢，無悔。",
        vernacular="感應到背脊深處 — 不為情所動，無悔。",
    ),
    (31, 6): YaoCiEntry(
        original="上六：咸其輔頰舌。",
        vernacular="感應只在嘴頰舌頭上 — 光說不練。",
    ),
    # ---------- 卦 32 雷風恆 ----------
    (32, 1): YaoCiEntry(
        original="初六：浚恆，貞凶，無攸利。",
        vernacular="一開始就求過深的恆久 — 守正仍凶，無利。",
    ),
    (32, 2): YaoCiEntry(
        original="九二：悔亡。",
        vernacular="持恆守中 — 悔事消亡。",
    ),
    (32, 3): YaoCiEntry(
        original="九三：不恆其德，或承之羞，貞吝。",
        vernacular="不能恆守其德 — 將遭羞辱，守正也可惜。",
    ),
    (32, 4): YaoCiEntry(
        original="九四：田無禽。",
        vernacular="田獵卻一無所獲 — 方法錯了再恆久也徒勞。",
    ),
    (32, 5): YaoCiEntry(
        original="六五：恆其德，貞，婦人吉，夫子凶。",
        vernacular="柔順守恆 — 婦人吉，但有為之士會錯失機會。",
    ),
    (32, 6): YaoCiEntry(
        original="上六：振恆，凶。",
        vernacular="動盪不安還想求恆久 — 凶。",
    ),
    # ---------- 卦 33 天山遯 ----------
    (33, 1): YaoCiEntry(
        original="初六：遯尾，厲，勿用有攸往。",
        vernacular="逃避落在最後 — 危險，別輕舉妄動。",
    ),
    (33, 2): YaoCiEntry(
        original="六二：執之用黃牛之革，莫之勝說。",
        vernacular="用黃牛皮繩牢牢繫住 — 心志堅定，無人能解。",
    ),
    (33, 3): YaoCiEntry(
        original="九三：係遯，有疾厲，畜臣妾吉。",
        vernacular="想退卻又被牽絆 — 有病險，宜安頓家眷僕從則吉。",
    ),
    (33, 4): YaoCiEntry(
        original="九四：好遯，君子吉，小人否。",
        vernacular="懂得適時退隱 — 君子吉，小人做不到。",
    ),
    (33, 5): YaoCiEntry(
        original="九五：嘉遯，貞吉。",
        vernacular="完美的退隱 — 守正則吉。",
    ),
    (33, 6): YaoCiEntry(
        original="上九：肥遯，無不利。",
        vernacular="從容寬裕地退隱 — 無不利。",
    ),
    # ---------- 卦 34 雷天大壯 ----------
    (34, 1): YaoCiEntry(
        original="初九：壯于趾，征凶，有孚。",
        vernacular="腳趾就先剛強 — 莽撞前進凶，但誠信仍在。",
    ),
    (34, 2): YaoCiEntry(
        original="九二：貞吉。",
        vernacular="守正則吉。",
    ),
    (34, 3): YaoCiEntry(
        original="九三：小人用壯，君子用罔。貞厲。羝羊觸藩，羸其角。",
        vernacular="小人靠蠻力、君子用智計 — 守正仍危；公羊撞籬反卡住角。",
    ),
    (34, 4): YaoCiEntry(
        original="九四：貞吉，悔亡。藩決不羸，壯于大輿之輹。",
        vernacular="守正則吉、無悔 — 籬笆衝開不卡，車軸強壯前進。",
    ),
    (34, 5): YaoCiEntry(
        original="六五：喪羊于易，無悔。",
        vernacular="在邊地失去羊群 — 該放就放，無悔。",
    ),
    (34, 6): YaoCiEntry(
        original="上六：羝羊觸藩，不能退，不能遂，無攸利。艱則吉。",
        vernacular="公羊撞籬卡住進退兩難 — 一無所利；唯艱守則吉。",
    ),
    # ---------- 卦 35 火地晉 ----------
    (35, 1): YaoCiEntry(
        original="初六：晉如摧如，貞吉。罔孚，裕無咎。",
        vernacular="升進受挫 — 守正則吉；不被信任時，從容寬裕則無咎。",
    ),
    (35, 2): YaoCiEntry(
        original="六二：晉如愁如，貞吉。受茲介福，于其王母。",
        vernacular="升進中帶著憂慮 — 守正則吉，從祖母（尊長）處受到大福。",
    ),
    (35, 3): YaoCiEntry(
        original="六三：眾允，悔亡。",
        vernacular="獲眾人信任 — 悔事消亡。",
    ),
    (35, 4): YaoCiEntry(
        original="九四：晉如鼫鼠，貞厲。",
        vernacular="升進像田鼠般貪佔 — 守正仍危。",
    ),
    (35, 5): YaoCiEntry(
        original="六五：悔亡，失得勿恤，往吉，無不利。",
        vernacular="悔亡 — 得失別放心上，前往吉，無不利。",
    ),
    (35, 6): YaoCiEntry(
        original="上九：晉其角，維用伐邑，厲吉，無咎，貞吝。",
        vernacular="升至犄角極點 — 唯適合自治內患，雖危而吉，無咎、守正可惜。",
    ),
    # ---------- 卦 36 地火明夷 ----------
    (36, 1): YaoCiEntry(
        original="初九：明夷于飛，垂其翼。君子于行，三日不食，有攸往，主人有言。",
        vernacular="光明受傷垂翼飛 — 君子出行三日斷食，所到之處主人有閒話。",
    ),
    (36, 2): YaoCiEntry(
        original="六二：明夷，夷于左股，用拯馬壯，吉。",
        vernacular="光明受傷及左腿 — 用強壯馬匹拯救，吉。",
    ),
    (36, 3): YaoCiEntry(
        original="九三：明夷于南狩，得其大首，不可疾貞。",
        vernacular="於南方狩獵中除害 — 抓到首惡，但不能急著要求一切歸正。",
    ),
    (36, 4): YaoCiEntry(
        original="六四：入于左腹，獲明夷之心，于出門庭。",
        vernacular="深入內裡、看清黑暗的真相 — 然後選擇離開。",
    ),
    (36, 5): YaoCiEntry(
        original="六五：箕子之明夷，利貞。",
        vernacular="像箕子那樣裝瘋避禍藏明 — 守正則利。",
    ),
    (36, 6): YaoCiEntry(
        original="上六：不明晦，初登于天，後入于地。",
        vernacular="極度的昏暗 — 起初高升如登天，最後墜落入地。",
    ),
    # ---------- 卦 37 風火家人 ----------
    (37, 1): YaoCiEntry(
        original="初九：閑有家，悔亡。",
        vernacular="一開始就把家規立好 — 悔事消亡。",
    ),
    (37, 2): YaoCiEntry(
        original="六二：無攸遂，在中饋，貞吉。",
        vernacular="不專斷、安於主持家中飲食 — 守正則吉。",
    ),
    (37, 3): YaoCiEntry(
        original="九三：家人嗃嗃，悔厲吉。婦子嘻嘻，終吝。",
        vernacular="家人嚴厲管教，雖悔危但吉；婦孺嘻笑放縱，終可惜。",
    ),
    (37, 4): YaoCiEntry(
        original="六四：富家，大吉。",
        vernacular="使家庭富裕和樂 — 大吉。",
    ),
    (37, 5): YaoCiEntry(
        original="九五：王假有家，勿恤吉。",
        vernacular="王者以德感格家人 — 不必憂慮，吉。",
    ),
    (37, 6): YaoCiEntry(
        original="上九：有孚威如，終吉。",
        vernacular="持守誠信又有威儀 — 終吉。",
    ),
    # ---------- 卦 38 火澤睽 ----------
    (38, 1): YaoCiEntry(
        original="初九：悔亡，喪馬勿逐，自復。見惡人，無咎。",
        vernacular="悔消失 — 馬跑了別追，會自己回來；見到惡人也無咎。",
    ),
    (38, 2): YaoCiEntry(
        original="九二：遇主于巷，無咎。",
        vernacular="在小巷意外遇到主君 — 反而通達無咎。",
    ),
    (38, 3): YaoCiEntry(
        original="六三：見輿曳，其牛掣，其人天且劓，無初有終。",
        vernacular="車被拖、牛被牽、人被刑 — 開頭凶險，最終仍有結果。",
    ),
    (38, 4): YaoCiEntry(
        original="九四：睽孤，遇元夫，交孚，厲無咎。",
        vernacular="孤立無援的乖隔之中遇到大丈夫 — 互信交誠，雖危無咎。",
    ),
    (38, 5): YaoCiEntry(
        original="六五：悔亡，厥宗噬膚，往何咎？",
        vernacular="悔消 — 同宗如咬其膚般親密，前往有何咎？",
    ),
    (38, 6): YaoCiEntry(
        original="上九：睽孤，見豕負塗，載鬼一車，先張之弧，後說之弧。匪寇婚媾，往遇雨則吉。",
        vernacular="疑神疑鬼看到豬背泥、車載鬼 — 放下成見才知是親人，雨後吉。",
    ),
    # ---------- 卦 39 水山蹇 ----------
    (39, 1): YaoCiEntry(
        original="初六：往蹇，來譽。",
        vernacular="前進有險阻 — 不如止步歸來，反得美譽。",
    ),
    (39, 2): YaoCiEntry(
        original="六二：王臣蹇蹇，匪躬之故。",
        vernacular="大臣為國事歷盡險難 — 並非為自己。",
    ),
    (39, 3): YaoCiEntry(
        original="九三：往蹇，來反。",
        vernacular="前往遇險 — 折返回家較安全。",
    ),
    (39, 4): YaoCiEntry(
        original="六四：往蹇，來連。",
        vernacular="前往遇險 — 回來與同志聯合，蓄勢待時。",
    ),
    (39, 5): YaoCiEntry(
        original="九五：大蹇，朋來。",
        vernacular="處於最大艱難 — 然朋友來相助。",
    ),
    (39, 6): YaoCiEntry(
        original="上六：往蹇，來碩，吉。利見大人。",
        vernacular="前往險難，回來反成大事 — 吉，宜見貴人。",
    ),
    # ---------- 卦 40 雷水解 ----------
    (40, 1): YaoCiEntry(
        original="初六：無咎。",
        vernacular="險難初解 — 無咎。",
    ),
    (40, 2): YaoCiEntry(
        original="九二：田獲三狐，得黃矢，貞吉。",
        vernacular="田獵得三狐又獲黃箭 — 除害有利，守正則吉。",
    ),
    (40, 3): YaoCiEntry(
        original="六三：負且乘，致寇至，貞吝。",
        vernacular="該背的卻坐車炫耀 — 招來盜匪，守正也遺憾。",
    ),
    (40, 4): YaoCiEntry(
        original="九四：解而拇，朋至斯孚。",
        vernacular="解開腳趾的羈絆 — 真正的朋友才會來，相互信任。",
    ),
    (40, 5): YaoCiEntry(
        original="六五：君子維有解，吉，有孚于小人。",
        vernacular="君子能化解紛擾 — 吉，連小人都被誠信感化。",
    ),
    (40, 6): YaoCiEntry(
        original="上六：公用射隼于高墉之上，獲之，無不利。",
        vernacular="王公射下高牆上的猛禽 — 一擊即中，無不利。",
    ),
    # ---------- 卦 41 山澤損 ----------
    (41, 1): YaoCiEntry(
        original="初九：已事遄往，無咎，酌損之。",
        vernacular="事情完成立即動身 — 無咎，並酌量減損自己。",
    ),
    (41, 2): YaoCiEntry(
        original="九二：利貞，征凶，弗損益之。",
        vernacular="守正有利 — 妄動則凶，不要再減損反該幫他人。",
    ),
    (41, 3): YaoCiEntry(
        original="六三：三人行，則損一人。一人行，則得其友。",
        vernacular="三人同行會少一人，一人獨行反得新伴 — 過猶不及。",
    ),
    (41, 4): YaoCiEntry(
        original="六四：損其疾，使遄有喜，無咎。",
        vernacular="減去自身的毛病 — 越快越喜，無咎。",
    ),
    (41, 5): YaoCiEntry(
        original="六五：或益之十朋之龜，弗克違，元吉。",
        vernacular="獲贈十朋之龜的厚禮 — 推不掉的福氣，元吉。",
    ),
    (41, 6): YaoCiEntry(
        original="上九：弗損益之，無咎，貞吉。利有攸往，得臣無家。",
        vernacular="不減損反增益於他人 — 無咎、守正吉，前往得忠臣相助。",
    ),
    # ---------- 卦 42 風雷益 ----------
    (42, 1): YaoCiEntry(
        original="初九：利用為大作，元吉，無咎。",
        vernacular="此時宜大展身手做大事 — 元吉、無咎。",
    ),
    (42, 2): YaoCiEntry(
        original="六二：或益之十朋之龜，弗克違，永貞吉。王用享于帝，吉。",
        vernacular="獲十朋之龜的厚賜 — 永守正則吉；王者用以祭天，吉。",
    ),
    (42, 3): YaoCiEntry(
        original="六三：益之用凶事，無咎。有孚中行，告公用圭。",
        vernacular="把資源用於救凶事上 — 無咎；以誠信中道，向上稟告以求支持。",
    ),
    (42, 4): YaoCiEntry(
        original="六四：中行，告公從。利用為依遷國。",
        vernacular="持中道 — 稟告君公必獲允從，宜舉大事如遷都。",
    ),
    (42, 5): YaoCiEntry(
        original="九五：有孚惠心，勿問元吉。有孚惠我德。",
        vernacular="懷誠信施惠之心 — 不必問必元吉，他人也以誠信回報。",
    ),
    (42, 6): YaoCiEntry(
        original="上九：莫益之，或擊之，立心勿恆，凶。",
        vernacular="貪求不止反而被攻擊 — 心無恆守，凶。",
    ),
    # ---------- 卦 43 澤天夬 ----------
    (43, 1): YaoCiEntry(
        original="初九：壯于前趾，往不勝為咎。",
        vernacular="腳趾就先逞強 — 前往不能勝任就是過錯。",
    ),
    (43, 2): YaoCiEntry(
        original="九二：惕號，莫夜有戎，勿恤。",
        vernacular="戒備示警 — 即使深夜遭襲，也不必憂慮。",
    ),
    (43, 3): YaoCiEntry(
        original="九三：壯于頄，有凶。君子夬夬獨行，遇雨若濡，有慍無咎。",
        vernacular="顴骨剛強顯露易凶 — 君子果決獨行，遇雨遭詆毀也無咎。",
    ),
    (43, 4): YaoCiEntry(
        original="九四：臀無膚，其行次且。牽羊悔亡，聞言不信。",
        vernacular="坐立難安、進退踟躕 — 順勢牽羊則悔消，但聽勸難。",
    ),
    (43, 5): YaoCiEntry(
        original="九五：莧陸夬夬中行，無咎。",
        vernacular="像清除柔軟莧菜般果斷而中道 — 無咎。",
    ),
    (43, 6): YaoCiEntry(
        original="上六：無號，終有凶。",
        vernacular="孤立無援呼救無人 — 終究凶。",
    ),
    # ---------- 卦 44 天風姤 ----------
    (44, 1): YaoCiEntry(
        original="初六：繫于金柅，貞吉。有攸往，見凶。羸豕孚蹢躅。",
        vernacular="繫於金屬車塞守住 — 守正則吉；妄動則凶，如瘦豬躁動踢踏。",
    ),
    (44, 2): YaoCiEntry(
        original="九二：包有魚，無咎，不利賓。",
        vernacular="廚房裡有魚 — 自家無咎，但不適合招待賓客。",
    ),
    (44, 3): YaoCiEntry(
        original="九三：臀無膚，其行次且，厲，無大咎。",
        vernacular="坐立不安、行走遲疑 — 危險，但無大過。",
    ),
    (44, 4): YaoCiEntry(
        original="九四：包無魚，起凶。",
        vernacular="廚房裡沒魚 — 失去民心，將起凶。",
    ),
    (44, 5): YaoCiEntry(
        original="九五：以杞包瓜，含章，有隕自天。",
        vernacular="以杞葉包瓜，內含華美 — 喜事如天降。",
    ),
    (44, 6): YaoCiEntry(
        original="上九：姤其角，吝，無咎。",
        vernacular="相遇於犄角的高點 — 隔閡可惜，但無大咎。",
    ),
    # ---------- 卦 45 澤地萃 ----------
    (45, 1): YaoCiEntry(
        original="初六：有孚不終，乃亂乃萃，若號，一握為笑，勿恤，往無咎。",
        vernacular="誠信不能始終，又紛亂又集結；呼號中互相一握化為笑 — 別憂，前往無咎。",
    ),
    (45, 2): YaoCiEntry(
        original="六二：引吉，無咎，孚乃利用禴。",
        vernacular="被人引導前去則吉 — 無咎，誠信即便薄祭也合宜。",
    ),
    (45, 3): YaoCiEntry(
        original="六三：萃如嗟如，無攸利。往無咎，小吝。",
        vernacular="想聚卻被嘆息 — 無利可圖；前往無咎，但小有遺憾。",
    ),
    (45, 4): YaoCiEntry(
        original="九四：大吉，無咎。",
        vernacular="眾人歸聚於己 — 大吉、無咎。",
    ),
    (45, 5): YaoCiEntry(
        original="九五：萃有位，無咎。匪孚，元永貞，悔亡。",
        vernacular="居高位以聚眾 — 無咎；若未獲信任，需以長久守正消解悔。",
    ),
    (45, 6): YaoCiEntry(
        original="上六：齎咨涕洟，無咎。",
        vernacular="嘆息流涕 — 真情流露，反而無咎。",
    ),
    # ---------- 卦 46 地風升 ----------
    (46, 1): YaoCiEntry(
        original="初六：允升，大吉。",
        vernacular="獲眾允可而上升 — 大吉。",
    ),
    (46, 2): YaoCiEntry(
        original="九二：孚乃利用禴，無咎。",
        vernacular="以誠信獻祭即可 — 無咎。",
    ),
    (46, 3): YaoCiEntry(
        original="九三：升虛邑。",
        vernacular="升入空無人之城 — 暢通無阻。",
    ),
    (46, 4): YaoCiEntry(
        original="六四：王用亨于岐山，吉，無咎。",
        vernacular="王者祭岐山 — 吉、無咎。",
    ),
    (46, 5): YaoCiEntry(
        original="六五：貞吉，升階。",
        vernacular="守正則吉 — 拾級而上。",
    ),
    (46, 6): YaoCiEntry(
        original="上六：冥升，利于不息之貞。",
        vernacular="盲目向上爬 — 唯有不止息地守正才有利。",
    ),
    # ---------- 卦 47 澤水困 ----------
    (47, 1): YaoCiEntry(
        original="初六：臀困于株木，入于幽谷，三歲不覿。",
        vernacular="坐困樹根、墜入深谷 — 三年不見光明。",
    ),
    (47, 2): YaoCiEntry(
        original="九二：困于酒食，朱紱方來，利用享祀，征凶，無咎。",
        vernacular="困於酒食富貴 — 王命將至，宜祭祀；妄動凶，但無罪。",
    ),
    (47, 3): YaoCiEntry(
        original="六三：困于石，據于蒺藜。入于其宮，不見其妻，凶。",
        vernacular="困於石、立於蒺藜 — 回家見不到妻子，凶。",
    ),
    (47, 4): YaoCiEntry(
        original="九四：來徐徐，困于金車，吝，有終。",
        vernacular="前來緩慢，困於金車 — 雖可惜仍有結果。",
    ),
    (47, 5): YaoCiEntry(
        original="九五：劓刖，困于赤紱，乃徐有說，利用祭祀。",
        vernacular="受刑被困於官位 — 慢慢才能解脫，宜以祭祀求通。",
    ),
    (47, 6): YaoCiEntry(
        original="上六：困于葛藟，于臲卼，曰動悔，有悔，征吉。",
        vernacular="困於藤蔓不安 — 自覺一動則悔；能誠悔改，前往則吉。",
    ),
    # ---------- 卦 48 水風井 ----------
    (48, 1): YaoCiEntry(
        original="初六：井泥不食，舊井無禽。",
        vernacular="井底淤泥不能喝 — 廢井連禽鳥都不來。",
    ),
    (48, 2): YaoCiEntry(
        original="九二：井谷射鮒，甕敝漏。",
        vernacular="井邊射小魚、水甕又破漏 — 雖有才能卻無用。",
    ),
    (48, 3): YaoCiEntry(
        original="九三：井渫不食，為我心惻，可用汲，王明，並受其福。",
        vernacular="井已淘乾淨卻沒人喝 — 令人惋惜；若王者明察，眾人共享其福。",
    ),
    (48, 4): YaoCiEntry(
        original="六四：井甃，無咎。",
        vernacular="修整井壁 — 無咎。",
    ),
    (48, 5): YaoCiEntry(
        original="九五：井洌，寒泉食。",
        vernacular="井水清澈、寒泉可飲 — 美德可享。",
    ),
    (48, 6): YaoCiEntry(
        original="上六：井收勿幕，有孚元吉。",
        vernacular="井水汲出不蓋蓋子 — 有誠信，利眾，元吉。",
    ),
    # ---------- 卦 49 澤火革 ----------
    (49, 1): YaoCiEntry(
        original="初九：鞏用黃牛之革。",
        vernacular="用黃牛皮先穩固結構 — 變革之初要謹慎不可妄動。",
    ),
    (49, 2): YaoCiEntry(
        original="六二：己日乃革之，征吉，無咎。",
        vernacular="到了適當時機才行變革 — 前往吉、無咎。",
    ),
    (49, 3): YaoCiEntry(
        original="九三：征凶，貞厲。革言三就，有孚。",
        vernacular="貿然前進凶、守正仍危 — 變革之言三度成熟才可信。",
    ),
    (49, 4): YaoCiEntry(
        original="九四：悔亡，有孚改命，吉。",
        vernacular="悔消失 — 以誠信改變舊命，吉。",
    ),
    (49, 5): YaoCiEntry(
        original="九五：大人虎變，未占有孚。",
        vernacular="大人物如虎之蛻變斑斕 — 不必占卜，眾人自然信服。",
    ),
    (49, 6): YaoCiEntry(
        original="上六：君子豹變，小人革面。征凶，居貞吉。",
        vernacular="君子如豹紋日新，小人也只改表面 — 妄動則凶，安居守正則吉。",
    ),
    # ---------- 卦 50 火風鼎 ----------
    (50, 1): YaoCiEntry(
        original="初六：鼎顛趾，利出否。得妾以其子，無咎。",
        vernacular="鼎顛倒腳朝上 — 趁機倒出舊穢；如妾以子貴，無咎。",
    ),
    (50, 2): YaoCiEntry(
        original="九二：鼎有實，我仇有疾，不我能即，吉。",
        vernacular="鼎中有實物 — 對手有病無法靠近，吉。",
    ),
    (50, 3): YaoCiEntry(
        original="九三：鼎耳革，其行塞，雉膏不食。方雨虧悔，終吉。",
        vernacular="鼎耳變動、提不起來 — 美味暫不能食；待雨來消悔，終吉。",
    ),
    (50, 4): YaoCiEntry(
        original="九四：鼎折足，覆公餗，其形渥，凶。",
        vernacular="鼎腿折斷、傾覆王餐 — 大失職，凶。",
    ),
    (50, 5): YaoCiEntry(
        original="六五：鼎黃耳金鉉，利貞。",
        vernacular="鼎裝黃耳金扛 — 中正穩固，守正則利。",
    ),
    (50, 6): YaoCiEntry(
        original="上九：鼎玉鉉，大吉，無不利。",
        vernacular="鼎用玉扛 — 至貴至寶，大吉，無不利。",
    ),
    # ---------- 卦 51 震為雷 ----------
    (51, 1): YaoCiEntry(
        original="初九：震來虩虩，後笑言啞啞，吉。",
        vernacular="雷聲一來戰戰兢兢，過後談笑風生 — 吉。",
    ),
    (51, 2): YaoCiEntry(
        original="六二：震來厲，億喪貝，躋于九陵。勿逐，七日得。",
        vernacular="雷聲震險、損失財物 — 不要追，七日後自會得回。",
    ),
    (51, 3): YaoCiEntry(
        original="六三：震蘇蘇，震行無眚。",
        vernacular="雷聲讓人緩過神來 — 警覺前行則無災。",
    ),
    (51, 4): YaoCiEntry(
        original="九四：震遂泥。",
        vernacular="雷震卻陷在泥裡 — 衝勁被消磨，宜檢討處境。",
    ),
    (51, 5): YaoCiEntry(
        original="六五：震往來厲，億無喪，有事。",
        vernacular="雷震往來都有險 — 自警則不至大失，仍有事可為。",
    ),
    (51, 6): YaoCiEntry(
        original="上六：震索索，視矍矍，征凶。震不于其躬，于其鄰，無咎，婚媾有言。",
        vernacular="震到發抖、目光驚惶 — 妄進則凶；震在鄰人不在己身，無咎，但婚事多口舌。",
    ),
    # ---------- 卦 52 艮為山 ----------
    (52, 1): YaoCiEntry(
        original="初六：艮其趾，無咎，利永貞。",
        vernacular="止住腳趾不妄動 — 無咎，宜永守正。",
    ),
    (52, 2): YaoCiEntry(
        original="六二：艮其腓，不拯其隨，其心不快。",
        vernacular="止住小腿但救不了被牽連的人 — 心中不快。",
    ),
    (52, 3): YaoCiEntry(
        original="九三：艮其限，列其夤，厲薰心。",
        vernacular="硬把腰部止住、撕裂脊肉 — 危險如火薰心。",
    ),
    (52, 4): YaoCiEntry(
        original="六四：艮其身，無咎。",
        vernacular="止住自身慾念 — 無咎。",
    ),
    (52, 5): YaoCiEntry(
        original="六五：艮其輔，言有序，悔亡。",
        vernacular="止住口舌、出言有序 — 悔消亡。",
    ),
    (52, 6): YaoCiEntry(
        original="上九：敦艮，吉。",
        vernacular="敦厚地止住 — 吉。",
    ),
    # ---------- 卦 53 風山漸 ----------
    (53, 1): YaoCiEntry(
        original="初六：鴻漸于干，小子厲，有言，無咎。",
        vernacular="鴻雁漸進到水邊 — 小子有險、有閒言，但無咎。",
    ),
    (53, 2): YaoCiEntry(
        original="六二：鴻漸于磐，飲食衎衎，吉。",
        vernacular="鴻雁進到大石上 — 飲食安和，吉。",
    ),
    (53, 3): YaoCiEntry(
        original="九三：鴻漸于陸，夫征不復，婦孕不育，凶。利禦寇。",
        vernacular="鴻雁進到陸地 — 夫遠征不歸、婦懷孕不育，凶；唯利於防禦。",
    ),
    (53, 4): YaoCiEntry(
        original="六四：鴻漸于木，或得其桷，無咎。",
        vernacular="鴻雁進到樹上 — 找到平直枝可棲，無咎。",
    ),
    (53, 5): YaoCiEntry(
        original="九五：鴻漸于陵，婦三歲不孕，終莫之勝，吉。",
        vernacular="鴻雁進到山陵 — 婦三年不孕，但最終無人能勝，吉。",
    ),
    (53, 6): YaoCiEntry(
        original="上九：鴻漸于陸，其羽可用為儀，吉。",
        vernacular="鴻雁進到高地 — 翎羽可作禮儀飾物，吉。",
    ),
    # ---------- 卦 54 雷澤歸妹 ----------
    (54, 1): YaoCiEntry(
        original="初九：歸妹以娣，跛能履，征吉。",
        vernacular="少女陪嫁姊妹 — 雖如跛而能行，前往則吉。",
    ),
    (54, 2): YaoCiEntry(
        original="九二：眇能視，利幽人之貞。",
        vernacular="獨眼仍能看 — 宜隱士守正之道。",
    ),
    (54, 3): YaoCiEntry(
        original="六三：歸妹以須，反歸以娣。",
        vernacular="待嫁卻久未嫁 — 不如以陪嫁身份歸去。",
    ),
    (54, 4): YaoCiEntry(
        original="九四：歸妹愆期，遲歸有時。",
        vernacular="出嫁延遲 — 等對的時候再歸。",
    ),
    (54, 5): YaoCiEntry(
        original="六五：帝乙歸妹，其君之袂不如其娣之袂良。月幾望，吉。",
        vernacular="帝乙嫁妹 — 嫡服反不如陪嫁的好；月將圓不滿盈，吉。",
    ),
    (54, 6): YaoCiEntry(
        original="上六：女承筐無實，士刲羊無血，無攸利。",
        vernacular="女捧空筐、男刲羊無血 — 形式空洞，無利。",
    ),
    # ---------- 卦 55 雷火豐 ----------
    (55, 1): YaoCiEntry(
        original="初九：遇其配主，雖旬無咎，往有尚。",
        vernacular="遇到匹配的主人 — 共處十日無咎，前往有獎賞。",
    ),
    (55, 2): YaoCiEntry(
        original="六二：豐其蔀，日中見斗。往得疑疾，有孚發若，吉。",
        vernacular="光被遮蔽、日中見北斗 — 前往易遭疑；唯誠信可化解，吉。",
    ),
    (55, 3): YaoCiEntry(
        original="九三：豐其沛，日中見沫。折其右肱，無咎。",
        vernacular="豐盛卻被遮蔽、日中見小星；折斷右臂似失助 — 但無咎。",
    ),
    (55, 4): YaoCiEntry(
        original="九四：豐其蔀，日中見斗。遇其夷主，吉。",
        vernacular="光被遮 — 但遇到平等的主人合作，吉。",
    ),
    (55, 5): YaoCiEntry(
        original="六五：來章，有慶譽，吉。",
        vernacular="美才來歸 — 有喜有譽，吉。",
    ),
    (55, 6): YaoCiEntry(
        original="上六：豐其屋，蔀其家，闚其戶，闃其無人，三歲不覿，凶。",
        vernacular="屋大卻空、窺門無人 — 三年不見人影，凶。",
    ),
    # ---------- 卦 56 火山旅 ----------
    (56, 1): YaoCiEntry(
        original="初六：旅瑣瑣，斯其所取災。",
        vernacular="旅途中斤斤計較瑣事 — 自找麻煩。",
    ),
    (56, 2): YaoCiEntry(
        original="六二：旅即次，懷其資，得童僕貞。",
        vernacular="旅人投宿安頓、攜帶足資、有忠僕相隨 — 守正而安。",
    ),
    (56, 3): YaoCiEntry(
        original="九三：旅焚其次，喪其童僕，貞厲。",
        vernacular="旅館失火、又失忠僕 — 守正仍危。",
    ),
    (56, 4): YaoCiEntry(
        original="九四：旅于處，得其資斧，我心不快。",
        vernacular="旅居有住處、有錢有工具 — 但心仍不安，異鄉終難樂。",
    ),
    (56, 5): YaoCiEntry(
        original="六五：射雉，一矢亡，終以譽命。",
        vernacular="射雉雖失一箭 — 最終仍獲讚譽與爵命。",
    ),
    (56, 6): YaoCiEntry(
        original="上九：鳥焚其巢，旅人先笑後號咷。喪牛于易，凶。",
        vernacular="鳥巢被燒、旅人先笑後哭 — 在邊地失牛，凶。",
    ),
    # ---------- 卦 57 巽為風 ----------
    (57, 1): YaoCiEntry(
        original="初六：進退，利武人之貞。",
        vernacular="進退猶豫不定 — 適合勇武有決斷者守正。",
    ),
    (57, 2): YaoCiEntry(
        original="九二：巽在床下，用史巫紛若，吉，無咎。",
        vernacular="謙卑伏於床下 — 借助禮儀相助而紛紜，吉、無咎。",
    ),
    (57, 3): YaoCiEntry(
        original="九三：頻巽，吝。",
        vernacular="一再地謙讓退縮 — 過頭可惜。",
    ),
    (57, 4): YaoCiEntry(
        original="六四：悔亡，田獲三品。",
        vernacular="悔消 — 田獵獲三類禽，收穫豐。",
    ),
    (57, 5): YaoCiEntry(
        original="九五：貞吉，悔亡，無不利。無初有終，先庚三日，後庚三日，吉。",
        vernacular="守正則吉、悔亡、無不利 — 雖無好開頭仍有好結果，把握時機則吉。",
    ),
    (57, 6): YaoCiEntry(
        original="上九：巽在床下，喪其資斧，貞凶。",
        vernacular="過於謙伏到失了財與斧（資源工具）— 守正仍凶。",
    ),
    # ---------- 卦 58 兌為澤 ----------
    (58, 1): YaoCiEntry(
        original="初九：和兌，吉。",
        vernacular="以和氣相悅 — 吉。",
    ),
    (58, 2): YaoCiEntry(
        original="九二：孚兌，吉，悔亡。",
        vernacular="以誠信相悅 — 吉、悔消。",
    ),
    (58, 3): YaoCiEntry(
        original="六三：來兌，凶。",
        vernacular="主動逢迎討好他人 — 凶。",
    ),
    (58, 4): YaoCiEntry(
        original="九四：商兌未寧，介疾有喜。",
        vernacular="心中商量取悅尚未安定 — 能割捨小毛病則有喜。",
    ),
    (58, 5): YaoCiEntry(
        original="九五：孚于剝，有厲。",
        vernacular="信任剝蝕者 — 有險。",
    ),
    (58, 6): YaoCiEntry(
        original="上六：引兌。",
        vernacular="一味引人取悅 — 表面相悅，內裡空虛。",
    ),
    # ---------- 卦 59 風水渙 ----------
    (59, 1): YaoCiEntry(
        original="初六：用拯馬壯，吉。",
        vernacular="用強壯的馬來拯救 — 吉。",
    ),
    (59, 2): YaoCiEntry(
        original="九二：渙奔其機，悔亡。",
        vernacular="渙散時奔向所依案桌 — 悔消亡。",
    ),
    (59, 3): YaoCiEntry(
        original="六三：渙其躬，無悔。",
        vernacular="放下自身私念 — 無悔。",
    ),
    (59, 4): YaoCiEntry(
        original="六四：渙其群，元吉。渙有丘，匪夷所思。",
        vernacular="化解小團體、聚為大群 — 元吉，這是常人想不到的格局。",
    ),
    (59, 5): YaoCiEntry(
        original="九五：渙汗其大號，渙王居，無咎。",
        vernacular="如汗一發如令一出、王居散發感化 — 無咎。",
    ),
    (59, 6): YaoCiEntry(
        original="上九：渙其血，去逖出，無咎。",
        vernacular="化散血光之災、遠離隱患 — 無咎。",
    ),
    # ---------- 卦 60 水澤節 ----------
    (60, 1): YaoCiEntry(
        original="初九：不出戶庭，無咎。",
        vernacular="不出大門 — 自我節制，無咎。",
    ),
    (60, 2): YaoCiEntry(
        original="九二：不出門庭，凶。",
        vernacular="該行動時仍不出門 — 過度節制，凶。",
    ),
    (60, 3): YaoCiEntry(
        original="六三：不節若，則嗟若，無咎。",
        vernacular="不能自我節制就會嘆息 — 知改則無咎。",
    ),
    (60, 4): YaoCiEntry(
        original="六四：安節，亨。",
        vernacular="安然守節制 — 亨通。",
    ),
    (60, 5): YaoCiEntry(
        original="九五：甘節，吉，往有尚。",
        vernacular="心甘情願地守節 — 吉，前往有獎。",
    ),
    (60, 6): YaoCiEntry(
        original="上六：苦節，貞凶，悔亡。",
        vernacular="苦撐過度的節制 — 守正仍凶，但能悔則消。",
    ),
    # ---------- 卦 61 風澤中孚 ----------
    (61, 1): YaoCiEntry(
        original="初九：虞吉，有它不燕。",
        vernacular="預先安排則吉 — 心思他騖則不安寧。",
    ),
    (61, 2): YaoCiEntry(
        original="九二：鳴鶴在陰，其子和之。我有好爵，吾與爾靡之。",
        vernacular="鶴在幽處鳴叫，其雛應和 — 我有好酒，與你共享。",
    ),
    (61, 3): YaoCiEntry(
        original="六三：得敵，或鼓或罷，或泣或歌。",
        vernacular="遇到對手 — 一會兒擊鼓、一會兒罷休、一會兒泣、一會兒歌，心無定見。",
    ),
    (61, 4): YaoCiEntry(
        original="六四：月幾望，馬匹亡，無咎。",
        vernacular="月將圓 — 失去同行馬匹，無咎，因為要獨立向上。",
    ),
    (61, 5): YaoCiEntry(
        original="九五：有孚攣如，無咎。",
        vernacular="以誠信使人緊密相連 — 無咎。",
    ),
    (61, 6): YaoCiEntry(
        original="上九：翰音登于天，貞凶。",
        vernacular="雞鳴聲響徹天 — 名實不符地誇張，守正仍凶。",
    ),
    # ---------- 卦 62 雷山小過 ----------
    (62, 1): YaoCiEntry(
        original="初六：飛鳥以凶。",
        vernacular="鳥兒高飛超過分寸 — 凶。",
    ),
    (62, 2): YaoCiEntry(
        original="六二：過其祖，遇其妣。不及其君，遇其臣，無咎。",
        vernacular="超過祖父輩、見到祖母輩；攀不上君主，遇上臣子 — 無咎。",
    ),
    (62, 3): YaoCiEntry(
        original="九三：弗過防之，從或戕之，凶。",
        vernacular="不防著小過失 — 隨後就被害，凶。",
    ),
    (62, 4): YaoCiEntry(
        original="九四：無咎。弗過遇之，往厲必戒。勿用，永貞。",
        vernacular="無咎 — 不過分相遇恰好；妄行有險須戒，不可妄動，永守正。",
    ),
    (62, 5): YaoCiEntry(
        original="六五：密雲不雨，自我西郊。公弋取彼在穴。",
        vernacular="密雲不雨，從西郊起 — 王公射取藏穴中物，徒勞無功。",
    ),
    (62, 6): YaoCiEntry(
        original="上六：弗遇過之，飛鳥離之，凶，是謂災眚。",
        vernacular="不能相遇而過分 — 飛鳥被網羅，凶，是謂災殃。",
    ),
    # ---------- 卦 63 水火既濟 ----------
    (63, 1): YaoCiEntry(
        original="初九：曳其輪，濡其尾，無咎。",
        vernacular="拖住車輪、沾濕狐尾 — 開始就懂節制，無咎。",
    ),
    (63, 2): YaoCiEntry(
        original="六二：婦喪其茀，勿逐，七日得。",
        vernacular="婦人失車簾 — 不必追，七日自得。",
    ),
    (63, 3): YaoCiEntry(
        original="九三：高宗伐鬼方，三年克之。小人勿用。",
        vernacular="高宗征伐鬼方歷三年才勝 — 大事費時，小人別用。",
    ),
    (63, 4): YaoCiEntry(
        original="六四：繻有衣袽，終日戒。",
        vernacular="華服中藏破爛布備漏 — 整天保持戒備，居安思危。",
    ),
    (63, 5): YaoCiEntry(
        original="九五：東鄰殺牛，不如西鄰之禴祭，實受其福。",
        vernacular="東家盛大殺牛祭祀，不如西家簡樸虔誠 — 真誠勝於排場。",
    ),
    (63, 6): YaoCiEntry(
        original="上六：濡其首，厲。",
        vernacular="渡水沾濕了頭 — 收尾失節，危。",
    ),
    # ---------- 卦 64 火水未濟 ----------
    (64, 1): YaoCiEntry(
        original="初六：濡其尾，吝。",
        vernacular="渡河沾濕尾巴 — 開頭莽撞，可惜。",
    ),
    (64, 2): YaoCiEntry(
        original="九二：曳其輪，貞吉。",
        vernacular="拖住車輪緩進 — 守正則吉。",
    ),
    (64, 3): YaoCiEntry(
        original="六三：未濟，征凶，利涉大川。",
        vernacular="尚未渡過 — 妄進凶，但若時機成熟仍宜涉大川。",
    ),
    (64, 4): YaoCiEntry(
        original="九四：貞吉，悔亡。震用伐鬼方，三年有賞于大國。",
        vernacular="守正則吉、悔消 — 奮力征伐鬼方三年，終獲大國封賞。",
    ),
    (64, 5): YaoCiEntry(
        original="六五：貞吉，無悔。君子之光，有孚，吉。",
        vernacular="守正則吉、無悔 — 君子的光輝出於誠信，吉。",
    ),
    (64, 6): YaoCiEntry(
        original="上九：有孚于飲酒，無咎。濡其首，有孚失是。",
        vernacular="以誠信飲酒慶賀無咎 — 但若沉醉沾濕頭，連誠信也失去。",
    ),
}


def validate_yao_ci_table() -> None:
    expected_keys = {(h, p) for h in range(1, 65) for p in range(1, 7)}
    missing = expected_keys - YAO_CI.keys()
    if missing:
        raise RuntimeError(f"YAO_CI incomplete: missing {len(missing)} entries, e.g. {sorted(missing)[:3]}")


def get_yao_ci(hex_num: int, line_pos: int) -> YaoCiEntry:
    """Lookup 爻辭 by (卦號, 爻位 1-6). Raises KeyError if missing."""
    return YAO_CI[(hex_num, line_pos)]


validate_yao_ci_table()  # boot-time guard

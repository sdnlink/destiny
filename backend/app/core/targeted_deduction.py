"""Targeted deduction engine synthesizing authentic multi-system evidence to directly answer specific user questions."""

from typing import Any, Dict, List, Optional
from app.core.inquiry_parser import parse_inquiry_intent

TRIGRAM_COLOR_PROFILES = {
    "乾": {
        "primary": ["大赤色", "玄色（深黑红）", "素白色", "金黄色"],
        "tones": "明亮端庄、质感挺括、金属光泽",
        "style": "正装、高品质挺拔服饰、名牌或配有金属配饰",
        "element": "金",
    },
    "坤": {
        "primary": ["黄色", "土黄色", "黑黄色", "棕褐色", "米白色"],
        "tones": "温和质朴、大地色系、沉稳低调",
        "style": "棉麻宽松、休闲舒适、宽大质朴",
        "element": "土",
    },
    "震": {
        "primary": ["青绿色", "深绿色", "翠绿色", "碧色"],
        "tones": "生机盎然、鲜活深邃、对比鲜明",
        "style": "运动休闲装、带条纹或拉链饰物、便于活动的服装",
        "element": "木",
    },
    "巽": {
        "primary": ["纯青色", "草绿色", "浅蓝浅绿", "青白色"],
        "tones": "轻盈淡雅、清爽柔和、飘逸",
        "style": "丝质薄衫、风衣、飘逸长裙/长袍、清凉轻便",
        "element": "木",
    },
    "坎": {
        "primary": ["纯黑色", "深蓝色", "藏青色", "深紫色", "墨色"],
        "tones": "深邃暗沉、冷色调、收敛防风",
        "style": "防水防风外套、深色连帽衫、暗系防寒装",
        "element": "水",
    },
    "离": {
        "primary": ["大红色", "赤红色", "亮橙色", "鲜艳花色", "亮紫色"],
        "tones": "鲜艳夺目、光彩照人、明亮吸睛",
        "style": "时尚前卫、亮眼色彩、剪裁合身或带荧光/反光设计",
        "element": "火",
    },
    "艮": {
        "primary": ["棕色", "棕黄色", "咖啡色", "卡其色", "土黄米色"],
        "tones": "厚重坚实、复古沉稳、大地厚土色",
        "style": "立领厚外套、毛呢保暖服、工装或登山户外装",
        "element": "土",
    },
    "兑": {
        "primary": ["素白色", "亮银色", "浅黄色", "浅粉色"],
        "tones": "明亮清雅、闪耀精致、温和柔丽",
        "style": "精致时尚装、带有破损/开口设计或精美金属扣件饰品",
        "element": "金",
    },
}

TRIGRAM_ACTIVITY_PROFILES = {
    "乾": {
        "activity": "正在主持全局、做出重要决策、深度规划思考、开高层会议或统领协调工作",
        "state": "神情专注威严、主动掌控局面、处于主导与指挥位置",
    },
    "坤": {
        "activity": "正在静止休息、整理内务、用餐休养、包容配合他人或处理接地气的琐碎杂务",
        "state": "心境平和沉稳、顺其自然、不争不抢、安静从容",
    },
    "震": {
        "activity": "正在快步行走、运动锻炼、发声演讲、打电话交流、操作机械仪器或奔波赶路",
        "state": "行动敏捷、情绪高昂或有突发紧迫感、充满动能",
    },
    "巽": {
        "activity": "正在撰写文书、商谈谋划、发送信息、查阅资料、散步漫游或随风穿梭",
        "state": "思维活跃通达、权衡进退、态度温和融通",
    },
    "坎": {
        "activity": "正在饮水饮茶、洗浴清洁、闭目沉思、暗中处理私密事项、涉水或处于休眠状态",
        "state": "心机深沉、防范审慎、专注内省或略带疲惫",
    },
    "离": {
        "activity": "正在使用手机/电脑/平板屏幕、阅读书籍文案、查看视觉图像、撰写材料或对镜梳妆",
        "state": "目光聚焦、思维敏锐通透、精神饱满活跃",
    },
    "艮": {
        "activity": "正在静坐止息、安守等待、看守看顾、整理杂物书籍或止步驻足观望",
        "state": "笃定沉着、安详不动、保持观察等待时机",
    },
    "兑": {
        "activity": "正在与人畅谈聊天、聚会用餐、唱歌欢笑、讨论业务或进行辩论演讲",
        "state": "心情欢快愉悦、善于表达、互动热络",
    },
}

TRIGRAM_LOCATION_PROFILES = {
    "乾": {"direction": "西北方", "environment": "开阔高地、政府机构、核心写字楼、高档场所或明亮大堂"},
    "坤": {"direction": "西南方", "environment": "开阔平地、宽敞庭院、乡村田野、仓库或舒适居室"},
    "震": {"direction": "正东方", "environment": "闹市街道、交通枢纽、运动场馆、车间或林木繁茂之地"},
    "巽": {"direction": "东南方", "environment": "通风走廊、花园草坪、邮政通讯处、机场车站或临风之地"},
    "坎": {"direction": "正北方", "environment": "临水潮湿处、水吧茶室、浴室洗手间、地下室或阴凉背光处"},
    "离": {"direction": "正南方", "environment": "明亮窗边、电子屏幕前、演播室、展厅或灯火通明处"},
    "艮": {"direction": "东北方", "environment": "安静角落、高山坡地、门阙门厅、书房靠墙处或坚固建筑内"},
    "兑": {"direction": "正西方", "environment": "餐厅酒馆、咖啡馆、会议讨论室、娱乐场所或临水浅滩"},
}

TRIGRAM_ITEM_PROFILES = {
    "乾": {
        "shape": "圆形、规整挺拔、坚硬高档、无瑕疵",
        "material": "金银首饰、高档金属制品、钟表、玉石珠宝、贵重证件或重要钱物",
        "state": "放置在高处、干燥明亮处、主位抽屉或金属盒中",
    },
    "坤": {
        "shape": "方形、宽大平整、厚重柔软、容纳器皿",
        "material": "布匹棉麻、陶瓷陶土、箱包布袋、日用百杂、纸箱收纳盒",
        "state": "放置在低处、地面、抽屉底层、角落或衣柜深处",
    },
    "震": {
        "shape": "直长条形、带支架/管状、可发声震动、运动部件",
        "material": "竹木器具、乐器音响、电动工具、车钥匙、运动器材、机械电子",
        "state": "放置在常走动通道、门后、玄关挂钩或带有声响震动之处",
    },
    "巽": {
        "shape": "细长条形、轻柔细软、带绳索拉链、轻便飘逸",
        "material": "丝绸织物、绳索线缆、文具信件、票据证件、轻薄塑料袋",
        "state": "悬挂在衣架上、搭在椅背上、通风窗口边或书架缝隙夹层",
    },
    "坎": {
        "shape": "下大上小、曲折弧形、中实外虚、易滚动液体状",
        "material": "水杯茶具、液体饮料、洗漱用品、油性胶质物、深色小包",
        "state": "遗落在临水潮湿处、水吧卫生间、洗手池旁、地下室或背光暗角",
    },
    "离": {
        "shape": "中空外实、扁平明亮、带有屏幕或发光发热部件",
        "material": "手机电脑平板、书籍文案、合同公文、发热电器、美妆镜饰",
        "state": "放置在窗台桌面明亮处、充电发热源旁、茶几中央或灯光直射处",
    },
    "艮": {
        "shape": "凸起隆起、坚硬结实、块状、带有底座支撑",
        "material": "石材玉器、陶瓷坚固器皿、厚重箱盒、印章门禁卡",
        "state": "遗落在靠墙死角、门后凹陷处、书柜顶层或重物压着下方",
    },
    "兑": {
        "shape": "带有缺口开口、凹陷形、小巧精致、可发声或开合",
        "material": "金属挂件、带拉链小零钱包、刀剪工具、首饰耳钉、酒杯",
        "state": "遗落在餐桌茶几、沙发缝隙、娱乐场所或废弃收纳盒中",
    },
}

TRIGRAM_ACCESSORY_PROFILES = {
    "乾": {"accessories": "金表、金属戒指、高档名牌手袋、高品质圆形眼镜、硬币或金属钥匙", "style": "高贵精致、金属质感、品质考究"},
    "坤": {"accessories": "棉麻布包、皮质钱包、陶瓷手串、质朴发带、日常环保袋", "style": "质朴低调、实用百搭、天然材质"},
    "震": {"accessories": "运动手环/智能手表、带金属声响钥匙扣、耳机、运动发带、电子手柄", "style": "动感时尚、带有科技或运动属性"},
    "巽": {"accessories": "丝巾飘带、细链首饰、风衣腰带、长款皮夹、文件手提袋、香囊", "style": "轻柔飘逸、长条形设计、文雅风尚"},
    "坎": {"accessories": "深色折叠雨伞、保温水杯、黑色墨镜、防水包、暗色耳机、水系配饰", "style": "深沉低调、防风防水、收纳防护"},
    "离": {"accessories": "红色手绳、亮眼项链、彩框眼镜、发光/屏幕数码配件、美妆镜盒、亮色卡包", "style": "鲜艳抓眼、发光发热、视觉焦点"},
    "艮": {"accessories": "沉香/木质文玩手串、玉石吊坠、厚重指环、工装/双肩登山背包", "style": "厚重文玩、天然石木、坚实耐用"},
    "兑": {"accessories": "亮银耳钉、带拉链精致零钱包、口红美妆、金属挂件、开口时尚手镯", "style": "小巧精致、带有开口/金属光泽"},
}

TRIGRAM_TRANSPORT_PROFILES = {
    "乾": {"mode": "高级轿车、自驾商务车、高铁一等座、飞机商务舱", "feature": "稳重高效、掌控感强、高档舒适"},
    "坤": {"mode": "步行、公共大巴、慢速平稳交通工具、地面交通", "feature": "平稳安全、不急不躁、随遇而安"},
    "震": {"mode": "高铁动车、自驾快车、越野车、快跑运动出行", "feature": "速度极快、动力充沛、充满动能"},
    "巽": {"mode": "自行车、电动车、轻便骑行、顺风漫步、航班飞机", "feature": "顺风而行、灵活穿梭、轻盈机动"},
    "坎": {"mode": "地下铁道（地铁）、轮船渡轮、临水涉水、雨中出行", "feature": "地下或暗道穿行、深水涉水、隐秘行进"},
    "离": {"mode": "新能源纯电汽车、带有明显视觉标识的车辆、夜间灯光出行", "feature": "动力明快、视觉醒目、电能驱动"},
    "艮": {"mode": "徒步登山、越野车、止步等待换乘、山道行车", "feature": "稳健缓行、逢山过坎、安全第一"},
    "兑": {"mode": "与朋友拼车、敞篷休闲车、游船观光车、欢快同行", "feature": "气氛欢悦、结伴同行、互动畅快"},
}

TRIGRAM_BODY_PROFILES = {
    "乾": {"organs": "头部、大脑、骨骼、肺部与中枢神经", "guidance": "注意头部血液循环、防止劳心过度与思虑耗神。"},
    "坤": {"organs": "脾胃、腹部、肌肉组织、消化系统", "guidance": "注意饮食规律、健脾和胃、防止湿气困脾。"},
    "震": {"organs": "足部、腿部、肝脏、神经系统", "guidance": "注意运动拉伤、舒肝理气、保持作息规律防虚火。"},
    "巽": {"organs": "股部、大腿、呼吸道、气管与神经", "guidance": "注意防风防凉、保持呼吸道通畅、适度拉伸放松。"},
    "坎": {"organs": "耳部、肾脏、泌尿系统、血液循环与水液代谢", "guidance": "注意保暖避寒、适量饮水、防范肾经虚耗与熬夜。"},
    "离": {"organs": "眼睛、视力、心脏、心血管与面部", "guidance": "注意用眼疲劳、远离长时间强光屏幕、静心安神。"},
    "艮": {"organs": "手部、手指、背部、脊椎、脾胃与关节", "guidance": "注意颈椎腰椎保护、避免久坐久站、适度活动关节。"},
    "兑": {"organs": "口齿、咽喉、舌部、呼吸系统与肺气", "guidance": "多饮温水润喉、注意用嗓节制、防范呼吸道干燥。"},
}

QIMEN_GATE_ACTIVITIES = {
    "开门": "正在正规公司、政府机构或核心岗位处理公职工作、主持全局或开业拓展",
    "休门": "正在休假调养、拜访贵人、聚会饮宴、安享闲暇或家庭团聚",
    "生门": "正在开展商务经营、求财投资、采购生产、买卖房产或推进增值业务",
    "伤门": "正在外出奔波、运动捕猎、索要账目、处理突发竞争或承受身体劳碌",
    "杜门": "正在闭门潜修、保密谋划、躲避烦扰、技术研发或处于隐秘堵塞状态",
    "景门": "正在阅读文书合同、设计视觉美化、使用手机电脑屏幕、参加宴会或发布信息",
    "死门": "正在处理不动产物业、执着坚守固有方案、探望旧物或处于停滞胶着状态",
    "惊门": "正在与人辩论沟通、法律咨询、演说谈判、受惊疑虑或防范口舌是非",
}

SIX_RELATIVE_ACTIVITIES = {
    "父母": "正在研读文书书籍、接打电话、发送短信邮件、处理合同资质或与长辈上级沟通",
    "官鬼": "正在应对工作考核、处理紧急公务、承受压力攻坚、管理规范或奔波履职",
    "兄弟": "正在与同事朋友聚会闲聊、团队协同作业、商讨利益分配或打牌互动",
    "妻财": "正在采购消费、结算盘点资金账目、享用美食或打理资产物资",
    "子孙": "正在休闲娱乐、创作设计、享受闲暇、陪伴孩子宠物或运动放松解压",
}

SIX_SPIRIT_NUANCES = {
    "青龙": "氛围喜悦祥和、有贵人相伴或享用高雅事物，状态大吉顺畅",
    "朱雀": "伴随口舌言语、电话通讯、文字信息交流或文案创作",
    "勾陈": "处于室内伏案、被陈旧繁琐事务牵绊、节奏稳健但略有拖延",
    "螣蛇": "心绪不定、有所挂虑疑忌、反复确认细节或正在寻找物品",
    "白虎": "动作幅度大、雷厉风行、身体略感劳累或正在处理急难险重事务",
    "玄武": "处于私密隐蔽环境、暗中行事、饮水休歇或防范他人打扰",
}


def _find_module_result(module_results: List[Dict[str, Any]], module_name: str) -> Optional[Dict[str, Any]]:
    for item in module_results:
        if item.get("module") == module_name:
            return item.get("result", {})
    return None


def generate_targeted_deduction(
    module_results: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Perform targeted multi-system deduction directly answering the parsed inquiry intent."""
    question = (context or {}).get("question_summary", "")
    category = (context or {}).get("category", "other")
    intent_data = parse_inquiry_intent(question, category)
    subject = intent_data["subject"]

    # Gather multi-system facts
    meihua = _find_module_result(module_results, "meihua")
    zhouyi = _find_module_result(module_results, "zhouyi")
    liuyao = _find_module_result(module_results, "liuyao")
    liuren = _find_module_result(module_results, "liuren")
    qimen = _find_module_result(module_results, "qimen")
    ziwei = _find_module_result(module_results, "ziwei")

    # Determine primary trigrams & elements
    body_tri_name = "乾"
    use_tri_name = "乾"
    changed_use_tri_name = "乾"
    relation_code = "same_element"
    moving_line = 1

    if meihua and "facts" in meihua:
        body_use = meihua["facts"].get("body_use", {})
        body_tri_name = body_use.get("body_trigram", {}).get("name", "乾")
        use_tri_name = body_use.get("use_trigram", {}).get("name", "乾")
        changed_use_tri_name = body_use.get("changed_use_trigram", {}).get("name", use_tri_name)
        moving_line = meihua["facts"].get("moving_line", 1)
        original_ev = next((e for e in meihua.get("evidence", []) if e.get("stage") == "original"), {})
        relation_code = original_ev.get("code", "same_element")
    elif zhouyi and "facts" in zhouyi:
        facts = zhouyi["facts"]
        body_tri_name = facts.get("original", {}).get("lower_trigram", {}).get("name", "乾")
        use_tri_name = facts.get("original", {}).get("upper_trigram", {}).get("name", "乾")
        changed_use_tri_name = facts.get("changed", {}).get("upper_trigram", {}).get("name", use_tri_name)
        moving_lines = facts.get("moving_lines", [1])
        moving_line = moving_lines[0] if moving_lines else 1

    # Liuyao facts
    moving_line_six_rel = ""
    moving_line_six_spirit = ""
    if liuyao and "facts" in liuyao:
        lines = liuyao["facts"].get("line_chart", [])
        moving_items = [line for line in lines if line.get("is_moving")]
        if moving_items:
            moving_line_six_rel = moving_items[0].get("six_relative", "")
            moving_line_six_spirit = moving_items[0].get("six_spirit", "")
        elif lines:
            host_pos = liuyao["facts"].get("palace", {}).get("host_line", 1)
            target = next((line for line in lines if line.get("position") == host_pos), lines[0])
            moving_line_six_rel = target.get("six_relative", "")
            moving_line_six_spirit = target.get("six_spirit", "")

    # Liuren facts
    liuren_initial_branch = ""
    if liuren and "facts" in liuren:
        transmissions = liuren["facts"].get("three_transmissions", {}).get("transmissions", [])
        if transmissions:
            liuren_initial_branch = transmissions[0]

    # Qimen facts
    qimen_gate = ""
    if qimen and "facts" in qimen:
        qimen_gate = qimen["facts"].get("zhi_shi_gate", "")

    # Ziwei facts
    ziwei_main_stars = []
    ziwei_sihua_str = ""
    if ziwei and "facts" in ziwei:
        ming_p = next((p for p in ziwei["facts"].get("palaces_by_order", []) if p.get("name") == "命宫"), None)
        if ming_p:
            ziwei_main_stars = [s["name"] for s in ming_p.get("main_stars", [])]
        sihua = ziwei["facts"].get("si_hua", {})
        if sihua:
            ziwei_sihua_str = "、".join(f"{v}{k}" for k, v in sihua.items())

    findings: List[Dict[str, Any]] = []

    # 1. Clothing & Color Deduction
    if "clothing_color" in intent_data["intents"]:
        use_profile = TRIGRAM_COLOR_PROFILES.get(use_tri_name, TRIGRAM_COLOR_PROFILES["乾"])
        chg_profile = TRIGRAM_COLOR_PROFILES.get(changed_use_tri_name, use_profile)
        body_profile = TRIGRAM_COLOR_PROFILES.get(body_tri_name, TRIGRAM_COLOR_PROFILES["乾"])

        primary_colors = list(dict.fromkeys(use_profile["primary"][:2] + chg_profile["primary"][:2]))
        base_colors = list(dict.fromkeys(body_profile["primary"][:2]))

        color_conclusion = (
            f"【主色调倾向】主要穿着 **{'、'.join(primary_colors[:3])}** 等色系（{use_profile['tones']}）；"
            f"【底色与搭配】内衬或下装可能搭配 **{'、'.join(base_colors[:2])}**；"
            f"【服装风格】{use_profile['style']}。"
        )
        evidence_chain = (
            f"梅花易数以用卦【{use_tri_name}】（属{use_profile['element']}）主外表服饰与气色，"
            f"变卦之用【{changed_use_tri_name}】（属{chg_profile['element']}）主延伸色调，"
            f"体卦【{body_tri_name}】（属{body_profile['element']}）为主体底色。"
        )

        findings.append({
            "key": "clothing_color",
            "title": f"👔 推算【{subject}】衣着颜色与服饰特征",
            "conclusion": color_conclusion,
            "highlight": f"主要色调：{'、'.join(primary_colors[:2])}；搭配色：{'、'.join(base_colors[:2])}",
            "palette": primary_colors[:4],
            "evidence": evidence_chain,
            "confidence": "依据梅花体用、变卦类象与五行正变色确定性推导",
            "rules": ["XIANG-TRIGRAM-001", "MH-BODYUSE-001", "XIANG-COLOR-001"],
        })

    # 2. Current Activity Deduction
    if "current_activity" in intent_data["intents"]:
        use_act = TRIGRAM_ACTIVITY_PROFILES.get(use_tri_name, TRIGRAM_ACTIVITY_PROFILES["乾"])
        body_act = TRIGRAM_ACTIVITY_PROFILES.get(body_tri_name, TRIGRAM_ACTIVITY_PROFILES["乾"])

        rel_nuance = SIX_RELATIVE_ACTIVITIES.get(moving_line_six_rel, "")
        spirit_nuance = SIX_SPIRIT_NUANCES.get(moving_line_six_spirit, "")
        qimen_nuance = QIMEN_GATE_ACTIVITIES.get(qimen_gate, "")

        act_parts = [f"【核心动态】{use_act['activity']}。"]
        if qimen_nuance:
            act_parts.append(f"【时空奇门格局】值使临【{qimen_gate}】，提示{qimen_nuance}。")
        if rel_nuance:
            act_parts.append(f"【所涉具体事项】六爻动爻临{moving_line_six_rel}，指向{rel_nuance}。")
        if spirit_nuance:
            act_parts.append(f"【伴随情境与形态】临{moving_line_six_spirit}神煞，提示{spirit_nuance}。")
        act_parts.append(f"【状态体貌】{use_act['state']}。")

        act_conclusion = "".join(act_parts)
        evidence_chain = (
            f"依据用卦【{use_tri_name}】八卦万物类象之行为特征"
            f"{f'，奇门遁甲值使【{qimen_gate}】' if qimen_gate else ''}"
            f"{f'，结合六爻第{moving_line}爻动爻六亲【{moving_line_six_rel}】与六神【{moving_line_six_spirit}】' if moving_line_six_rel else ''}"
            f"{f'，大六壬初传【{liuren_initial_branch}】发端事由' if liuren_initial_branch else ''}交叉印证。"
        )

        findings.append({
            "key": "current_activity",
            "title": f"⚡ 推算【{subject}】当前正在从事的行为与状态",
            "conclusion": act_conclusion,
            "highlight": use_act["activity"],
            "evidence": evidence_chain,
            "confidence": "依据八卦行为类象、奇门八门、六亲动变与六神情态交叉印证推导",
            "rules": ["XIANG-TRIGRAM-001", "QM-GATE-001", "LY-RELATIVE-001", "LY-SPIRIT-001"],
        })

    # 3. Location & Direction Deduction
    if "location_direction" in intent_data["intents"]:
        use_loc = TRIGRAM_LOCATION_PROFILES.get(use_tri_name, TRIGRAM_LOCATION_PROFILES["乾"])
        loc_conclusion = (
            f"【方位指向】位于求问基准点或所处区域的 **{use_loc['direction']}**；"
            f"【场所环境特征】多处于 **{use_loc['environment']}**。"
        )
        evidence_chain = f"依据用卦【{use_tri_name}】后天八卦方位与空间环境类象推导。"

        findings.append({
            "key": "location_direction",
            "title": f"🧭 推算【{subject}】所处方位与环境场所",
            "conclusion": loc_conclusion,
            "highlight": f"方位：{use_loc['direction']}；环境：{use_loc['environment']}",
            "evidence": evidence_chain,
            "confidence": "依据后天八卦方位与地理类象推导",
            "rules": ["XIANG-TRIGRAM-001", "YI-DIRECTION-001"],
        })

    # 4. Character State Deduction
    if "character_state" in intent_data["intents"]:
        body_act = TRIGRAM_ACTIVITY_PROFILES.get(body_tri_name, TRIGRAM_ACTIVITY_PROFILES["乾"])
        relation_labels = {
            "same_element": "比和（内外同频，心情从容平和）",
            "use_generates_body": "用生体（外部生旺，心态积极愉悦，受贵人与环境支持）",
            "body_generates_use": "体生用（主体耗泄，精力持续投入，略感疲惫但极具责任感）",
            "use_controls_body": "用克体（外力制约，面临规则或外部压力，神情警觉严肃）",
            "body_controls_use": "体克用（主体掌控，自信果决，占据主导地位）",
        }
        rel_desc = relation_labels.get(relation_code, "气机交织")
        char_parts = [f"【当前心境气场】体用呈现{rel_desc}；【体质神情】{body_act['state']}。"]
        if ziwei_main_stars:
            char_parts.append(f"【紫微命盘主星】命坐【{'、'.join(ziwei_main_stars)}】" + (f"，生年四化【{ziwei_sihua_str}】" if ziwei_sihua_str else "") + "，呈现自主进取与稳重兼备之格。")
        char_conclusion = "".join(char_parts)
        evidence_chain = f"依据体卦【{body_tri_name}】与用卦【{use_tri_name}】五行生克格局" + (f"，紫微主星【{'、'.join(ziwei_main_stars)}】" if ziwei_main_stars else "") + "分析。"

        findings.append({
            "key": "character_state",
            "title": f"🧠 推算【{subject}】心智情绪与神态特征",
            "conclusion": char_conclusion,
            "highlight": rel_desc,
            "evidence": evidence_chain,
            "confidence": "依据体用生克与体卦本质气机推导",
            "rules": ["MH-BODYUSE-001", "MH-FIVE-ELEMENT-001", "ZW-STARS-001"],
        })

    # 5. Accessories & Items Carried (随身配饰与携带物)
    if "accessories_items" in intent_data["intents"]:
        use_acc = TRIGRAM_ACCESSORY_PROFILES.get(use_tri_name, TRIGRAM_ACCESSORY_PROFILES["乾"])
        body_acc = TRIGRAM_ACCESSORY_PROFILES.get(body_tri_name, TRIGRAM_ACCESSORY_PROFILES["乾"])
        acc_conclusion = (
            f"【随身携带物与配饰】多带有 **{use_acc['accessories']}**；"
            f"【配饰风格特征】{use_acc['style']}（主体底蕴搭配：{body_acc['accessories'][:15]}...）。"
        )
        evidence_chain = f"依据用卦【{use_tri_name}】器物类象与体卦【{body_tri_name}】贴身饰物象数推导。"

        findings.append({
            "key": "accessories_items",
            "title": f"💍 推算【{subject}】随身配饰与携带物品",
            "conclusion": acc_conclusion,
            "highlight": f"特征配饰：{use_acc['accessories'][:16]}...",
            "evidence": evidence_chain,
            "confidence": "依据八卦器物配饰类象确定性推导",
            "rules": ["XIANG-TRIGRAM-001", "XIANG-ACCESSORY-001"],
        })

    # 6. Transport & Travel Mode (出行方式与交通工具)
    if "transport_travel" in intent_data["intents"]:
        use_trans = TRIGRAM_TRANSPORT_PROFILES.get(use_tri_name, TRIGRAM_TRANSPORT_PROFILES["乾"])
        trans_conclusion = (
            f"【出行方式倾向】主要采用 **{use_trans['mode']}**；"
            f"【行程特征】{use_trans['feature']}。"
        )
        evidence_chain = f"依据用卦【{use_tri_name}】动象、交通与行路万物类象推导。"

        findings.append({
            "key": "transport_travel",
            "title": f"🚗 推算【{subject}】出行方式与交通工具",
            "conclusion": trans_conclusion,
            "highlight": f"出行方式：{use_trans['mode'][:14]}...",
            "evidence": evidence_chain,
            "confidence": "依据八卦动象与交通工具类象推导",
            "rules": ["XIANG-TRIGRAM-001", "XIANG-TRANSPORT-001"],
        })

    # 7. Health & Body Parts (身体部位与脏腑健康)
    if "health_body" in intent_data["intents"]:
        body_health = TRIGRAM_BODY_PROFILES.get(body_tri_name, TRIGRAM_BODY_PROFILES["乾"])
        use_health = TRIGRAM_BODY_PROFILES.get(use_tri_name, TRIGRAM_BODY_PROFILES["乾"])
        health_conclusion = (
            f"【主体气血对应部位】体卦【{body_tri_name}】主 **{body_health['organs']}**；"
            f"【外界影响与互动】用卦【{use_tri_name}】牵引 **{use_health['organs']}**；"
            f"【养生调理指引】{body_health['guidance']}"
        )
        evidence_chain = f"依据体卦【{body_tri_name}】人体脏腑部位对应与生克平衡模型推导。"

        findings.append({
            "key": "health_body",
            "title": f"🌿 推算【{subject}】身体部位与脏腑气机",
            "conclusion": health_conclusion,
            "highlight": f"核心对应：{body_health['organs']}",
            "evidence": evidence_chain,
            "confidence": "依据中医五行藏象与八卦人体部位模型推导",
            "rules": ["XIANG-TRIGRAM-001", "TCM-BODY-001"],
        })

    # 8. Item Nature / Lost Item Deduction (射覆与寻物推演)
    if "item_nature" in intent_data["intents"]:
        use_item = TRIGRAM_ITEM_PROFILES.get(use_tri_name, TRIGRAM_ITEM_PROFILES["乾"])
        loc_dir = TRIGRAM_LOCATION_PROFILES.get(use_tri_name, {"direction": "周边"})["direction"]

        item_conclusion = (
            f"【物品形态与材质】形态特征偏向 **{use_item['shape']}**；材质品类主要为 **{use_item['material']}**；"
            f"【寻找方位与存放处】建议优先前往 **{loc_dir}** 寻找，多位于 **{use_item['state']}**。"
        )
        evidence_chain = (
            f"依据用卦【{use_tri_name}】八卦射覆万物类象"
            f"{f'与变卦【{changed_use_tri_name}】形态转化' if changed_use_tri_name != use_tri_name else ''}"
            f"，结合后天八卦方位【{loc_dir}】推导寻找线索。"
        )

        findings.append({
            "key": "item_nature",
            "title": f"🔍 推算【{subject}】物品特征与寻物线索",
            "conclusion": item_conclusion,
            "highlight": f"主要材质：{use_item['material'][:12]}...；寻找方位：{loc_dir}",
            "evidence": evidence_chain,
            "confidence": "依据八卦射覆万物类象与后天八卦空间定位推导",
            "rules": ["XIANG-TRIGRAM-001", "XIANG-ITEM-001", "YI-DIRECTION-001"],
        })

    # 9. Outcome & Timing / General Development
    if "outcome_timing" in intent_data["intents"] or not findings:
        relation_guidance = {
            "same_element": ("顺遂平稳", "内外和合，阻力极小，适合稳步推进与团队协作。"),
            "use_generates_body": ("吉利受助", "外部条件有利，常有良机或贵人提携，顺势而为必有所获。"),
            "body_generates_use": ("付出蓄力", "当前处于大量投入与打底阶段，需防范过度消耗，循序渐进。"),
            "use_controls_body": ("受制谨守", "外部规则与阻力较大，切忌盲目硬碰硬，宜低调防守避其锋芒。"),
            "body_controls_use": ("主导破局", "自身实力与突破能力强，能够克服阻碍赢得主导，但需戒骄戒躁。"),
        }
        status_label, desc = relation_guidance.get(relation_code, ("审慎发展", "需根据各阶段变数审慎应对。"))
        dev_conclusion = f"【综合吉凶走势】**{status_label}**。{desc} 动在第{moving_line}爻，提示局势转折关键点在于该阶段的因势利导。"
        evidence_chain = f"梅花易数体卦【{body_tri_name}】、用卦【{use_tri_name}】生克关系判定，结合动爻【第{moving_line}爻】转折时位。"

        findings.append({
            "key": "outcome_timing",
            "title": "🎯 事项综合研判与转折时机",
            "conclusion": dev_conclusion,
            "highlight": f"大势倾向：{status_label}",
            "evidence": evidence_chain,
            "confidence": "依据体用生克法则与周易时位卦理推导",
            "rules": ["MH-BODYUSE-001", "YI-RELATION-001"],
        })

    return {
        "schema_version": "1.0",
        "question": question,
        "category": category,
        "subject": subject,
        "intents": intent_data["intents"],
        "findings_count": len(findings),
        "findings": findings,
        "summary": f"已针对您的问题“{question}”完成多术数象数专项推演，成功提取 {len(findings)} 项针对性推断结论。",
    }

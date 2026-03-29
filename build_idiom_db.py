import json
import sqlite3
from pypinyin import pinyin, Style

DB_NAME = 'idiom.db'

def split_pinyin(pinyin_str):
    """
    将拼音拆分为声母和韵母，采用日常习惯规则：
    - 如果拼音以 zh/ch/sh 开头，则取前两个字母为声母，剩余为韵母
    - 如果拼音以 y/w 开头，则声母为 y 或 w，韵母为剩余部分（例如 yan -> y + an）
    - 否则，取第一个字母为声母，剩余为韵母
    - 对于韵母中的 ü 保留为 v（便于输入）
    """
    # 先处理复合声母
    if pinyin_str.startswith(('zh', 'ch', 'sh')):
        initial = pinyin_str[:2]
        final = pinyin_str[2:]
    else:
        initial = pinyin_str[0]
        final = pinyin_str[1:]
    # 特殊情况：如果韵母为空，则设为空字符串
    if not final:
        final = ''
    return initial, final

def get_pinyin_details(idiom):
    # 获取带声调的完整拼音（用于显示）
    full_pinyin = pinyin(idiom, style=Style.TONE)
    # 获取无声调的拼音（用于拆分）
    no_tone = pinyin(idiom, style=Style.NORMAL)
    # 获取带数字的声调（如 "yan3"）
    tones = pinyin(idiom, style=Style.TONE3)

    details = []
    for i in range(len(idiom)):
        tone_mark = tones[i][0]
        tone_num = 0
        for ch in tone_mark:
            if ch.isdigit():
                tone_num = int(ch)
                break
        py = no_tone[i][0]
        initial, final = split_pinyin(py)
        # 将韵母中的 ü 转换为 v（便于输入和显示）
        final = final.replace('ü', 'v')
        details.append({
            'character': idiom[i],
            'pinyin': py,
            'pinyin_tone': full_pinyin[i][0],
            'initial': initial,
            'final': final,
            'tone': tone_num
        })
    return details

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS idiom (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL UNIQUE,
        pinyin TEXT NOT NULL,
        explanation TEXT,
        derivation TEXT,
        example TEXT,
        char1 TEXT, initial1 TEXT, final1 TEXT, tone1 INTEGER,
        char2 TEXT, initial2 TEXT, final2 TEXT, tone2 INTEGER,
        char3 TEXT, initial3 TEXT, final3 TEXT, tone3 INTEGER,
        char4 TEXT, initial4 TEXT, final4 TEXT, tone4 INTEGER
    )
''')
print("数据库表创建成功")

try:
    with open('idiom.json', 'r', encoding='utf-8') as f:
        idioms = json.load(f)
    print(f"成功读取 {len(idioms)} 条成语数据")
except FileNotFoundError:
    print("错误：未找到 idiom.json 文件")
    exit()

count = 0
for item in idioms:
    word = item.get('word')
    if not word or len(word) != 4:
        continue
    pinyin_str = item.get('pinyin', '')
    explanation = item.get('explanation', '')
    derivation = item.get('derivation', '')
    example = item.get('example', '')
    details = get_pinyin_details(word)
    if len(details) != 4:
        continue
    sql = '''
        INSERT OR REPLACE INTO idiom (
            word, pinyin, explanation, derivation, example,
            char1, initial1, final1, tone1,
            char2, initial2, final2, tone2,
            char3, initial3, final3, tone3,
            char4, initial4, final4, tone4
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    values = [
        word, pinyin_str, explanation, derivation, example,
        details[0]['character'], details[0]['initial'], details[0]['final'], details[0]['tone'],
        details[1]['character'], details[1]['initial'], details[1]['final'], details[1]['tone'],
        details[2]['character'], details[2]['initial'], details[2]['final'], details[2]['tone'],
        details[3]['character'], details[3]['initial'], details[3]['final'], details[3]['tone']
    ]
    cursor.execute(sql, values)
    count += 1
    if count % 1000 == 0:
        print(f"已处理 {count} 条成语...")

conn.commit()
print(f"完成！共 {count} 条成语存入 {DB_NAME}")
conn.close()

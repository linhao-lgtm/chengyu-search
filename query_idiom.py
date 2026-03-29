#!/usr/bin/env python3
import sqlite3
import re

DB_PATH = 'idiom.db'

def print_help():
    print("\n成语查询工具 - 使用说明")
    print("输入条件的格式：位置拼音属性=值")
    print("位置: 1,2,3,4 或 一,二,三,四 或 首,次,三,末")
    print("属性: shengmu, yunmu, shengdiao (或声母,韵母,声调)")
    print("示例:")
    print("  1声母=j 3声调=2        # 第一个字声母j，第三个字声调2")
    print("  2韵母=u 4声母=l        # 第二个字韵母u，第四个字声母l")
    print("  首声母=y 末韵母=ong     # 首字声母y，末字韵母ong")
    print("  clear                  # 清除所有条件")
    print("  list                   # 列出当前条件")
    print("  exit                   # 退出")
    print()

def parse_condition(cond_str):
    """解析类似 '1声母=j' 或 '首韵母=u' 的字符串，返回 (位置, 属性, 值)"""
    # 支持中英文属性名
    prop_map = {
        'shengmu': 'initial', '声母': 'initial',
        'yunmu': 'final', '韵母': 'final',
        'shengdiao': 'tone', '声调': 'tone'
    }
    # 位置映射
    pos_map = {
        '1': 1, '一': 1, '首': 1,
        '2': 2, '二': 2, '次': 2,
        '3': 3, '三': 3,
        '4': 4, '四': 4, '末': 4
    }
    # 用正则提取: 位置+属性+值
    match = re.match(r'([一二三四首次数末1-4])([^\d=]+)=(.+)', cond_str)
    if not match:
        return None
    pos_str, prop_str, value = match.groups()
    pos = pos_map.get(pos_str)
    if pos is None:
        return None
    prop = prop_map.get(prop_str.strip())
    if prop is None:
        return None
    # 声调值必须是数字
    if prop == 'tone':
        try:
            value = int(value)
        except:
            return None
    return (pos, prop, value)

def build_sql(conditions):
    """根据条件字典构建SQL查询"""
    sql = "SELECT word, pinyin, explanation FROM idiom WHERE 1=1"
    params = []
    for pos, prop, val in conditions:
        col = f"{prop}{pos}"
        sql += f" AND {col} = ?"
        params.append(val)
    return sql, params

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    conditions = []
    print("成语查询工具已启动 (输入 help 查看帮助)")
    while True:
        try:
            cmd = input("\n> ").strip()
            if not cmd:
                continue
            if cmd.lower() == 'exit':
                break
            if cmd.lower() == 'help':
                print_help()
                continue
            if cmd.lower() == 'clear':
                conditions.clear()
                print("已清除所有条件")
                continue
            if cmd.lower() == 'list':
                if not conditions:
                    print("当前无任何条件")
                else:
                    print("当前条件:")
                    for pos, prop, val in conditions:
                        print(f"  第{pos}字 {prop}={val}")
                continue
            # 解析条件
            cond = parse_condition(cmd)
            if cond is None:
                print("无法解析，请参考格式：1声母=j  或  首韵母=u")
                continue
            pos, prop, val = cond
            # 避免重复条件
            if (pos, prop) in [(c[0], c[1]) for c in conditions]:
                print(f"第{pos}字的{prop}已设置，请先 clear 或修改")
                continue
            conditions.append((pos, prop, val))
            # 构建SQL并查询
            sql, params = build_sql(conditions)
            cursor.execute(sql, params)
            results = cursor.fetchall()
            if results:
                print(f"找到 {len(results)} 个成语:")
                for word, pinyin, explanation in results[:20]:  # 最多显示20个
                    print(f"  {word} ({pinyin})")
                    if explanation:
                        print(f"      {explanation[:80]}...")
                if len(results) > 20:
                    print(f"  ... 还有 {len(results)-20} 个未显示")
            else:
                print("没有找到匹配的成语")
        except KeyboardInterrupt:
            print("\n退出")
            break
        except Exception as e:
            print(f"错误: {e}")
    conn.close()

if __name__ == '__main__':
    main()

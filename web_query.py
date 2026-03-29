#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
from flask import Flask, request, jsonify, render_template_string
from pypinyin import pinyin, Style

app = Flask(__name__)
DB_PATH = 'idiom.db'

def split_pinyin(pinyin_str):
    """与 build 脚本中的逻辑保持一致"""
    if pinyin_str.startswith(('zh', 'ch', 'sh')):
        initial = pinyin_str[:2]
        final = pinyin_str[2:]
    else:
        initial = pinyin_str[0]
        final = pinyin_str[1:]
    if not final:
        final = ''
    return initial, final

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>成语拼音查询工具 - 增强版</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; background: #f0f2f5; }
        .container { max-width: 1300px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1a73e8; text-align: center; }
        .subtitle { text-align: center; color: #5f6368; margin-bottom: 20px; }
        .tool-section { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #ddd; }
        .tool-section h3 { margin-top: 0; color: #1a73e8; }
        .tool-input { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .tool-input input { padding: 8px; width: 150px; }
        .tool-input button { padding: 8px 16px; background: #1a73e8; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .tool-result { margin-top: 10px; font-family: monospace; }
        .global-condition { background: #e8f0fe; padding: 12px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
        .global-condition label { font-weight: bold; }
        .global-condition input { padding: 6px; width: 100px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #1a73e8; color: white; font-size: 0.95em; }
        td { background-color: #f9f9f9; }
        .word-label { font-weight: bold; background-color: #e8f0fe; }
        input { width: 100%; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; text-align: center; box-sizing: border-box; }
        input:focus { outline: none; border-color: #1a73e8; box-shadow: 0 0 3px #1a73e8; }
        .exclude-input { background-color: #fff0f0; border-color: #dc3545; }
        .button-group { text-align: center; margin: 20px 0; }
        button { padding: 10px 24px; font-size: 16px; border: none; border-radius: 6px; cursor: pointer; margin: 0 8px; transition: 0.2s; }
        .search-btn { background-color: #1a73e8; color: white; }
        .search-btn:hover { background-color: #0c5bcd; }
        .clear-btn { background-color: #dc3545; color: white; }
        .clear-btn:hover { background-color: #c82333; }
        .result-area { margin-top: 30px; border-top: 2px solid #eee; padding-top: 20px; }
        .result-item { border-bottom: 1px solid #eee; padding: 12px 0; }
        .word { font-size: 20px; font-weight: bold; color: #1a73e8; }
        .pinyin { color: #5f6368; margin-left: 15px; font-size: 16px; }
        .explanation { margin-top: 6px; color: #333; line-height: 1.4; }
        .footer { text-align: center; margin-top: 25px; font-size: 12px; color: #aaa; }
        .note { background: #fff3cd; padding: 8px; border-radius: 4px; margin-top: 10px; font-size: 13px; }
        .char-input { width: 80px; }
    </style>
</head>
<body>
<div class="container">
    <h1>🔍 成语拼音查询工具</h1>
    <div class="subtitle">根据位置或全局条件精准查找成语</div>

    <div class="tool-section">
        <h3>📖 汉字拼音分解查询</h3>
        <div class="tool-input">
            <input type="text" id="charInput" placeholder="输入一个汉字" maxlength="1">
            <button onclick="queryChar()">查询拼音分解</button>
        </div>
        <div class="tool-result" id="charResult"></div>
        <div class="note">💡 提示：韵母中的 "ü" 请用 "v" 代替。例如“绿”的韵母为 "v"。</div>
    </div>

    <!-- 全局条件 -->
    <div class="global-condition">
        <span>🔎 全局包含：</span>
        <label>声母：</label>
        <input type="text" id="global_initial" placeholder="例: ch">
        <label>韵母：</label>
        <input type="text" id="global_final" placeholder="例: ang">
        <label>汉字：</label>
        <input type="text" id="global_char" placeholder="例: 山">
        <span style="font-size:12px; color:#555;">（任意位置）</span>
        <span style="margin-left:20px;">🚫 全局排除汉字：</span>
        <input type="text" id="global_exclude_char" placeholder="例: 死">
    </div>

    <form id="searchForm">
        <table>
            <thead>
                <tr><th>位置</th><th>汉字</th><th>声母</th><th>韵母</th><th>声调</th><th style="background-color:#f8d7da;">排除字</th></tr>
            </thead>
            <tbody>
                <tr><td class="word-label">第1字</td>
                    <td><input type="text" class="char-input" id="char1" placeholder="如: 卷" style="width:80px"></td>
                    <td><input type="text" id="initial1" placeholder="例: j"></td>
                    <td><input type="text" id="final1" placeholder="例: uan"></td>
                    <td><input type="text" id="tone1" placeholder="例: 3"></td>
                    <td style="background:#f8d7da;"><input type="text" id="exclude1" placeholder="排除字" class="exclude-input"></td>
                </tr>
                <tr><td class="word-label">第2字</td>
                    <td><input type="text" class="char-input" id="char2" placeholder="如: 土"></td>
                    <td><input type="text" id="initial2" placeholder="例: t"></td>
                    <td><input type="text" id="final2" placeholder="例: u"></td>
                    <td><input type="text" id="tone2" placeholder="例: 3"></td>
                    <td style="background:#f8d7da;"><input type="text" id="exclude2" placeholder="排除字" class="exclude-input"></td>
                </tr>
                <tr><td class="word-label">第3字</td>
                    <td><input type="text" class="char-input" id="char3" placeholder="如: 重"></td>
                    <td><input type="text" id="initial3" placeholder="例: ch"></td>
                    <td><input type="text" id="final3" placeholder="例: ong"></td>
                    <td><input type="text" id="tone3" placeholder="例: 2"></td>
                    <td style="background:#f8d7da;"><input type="text" id="exclude3" placeholder="排除字" class="exclude-input"></td>
                </tr>
                <tr><td class="word-label">第4字</td>
                    <td><input type="text" class="char-input" id="char4" placeholder="如: 来"></td>
                    <td><input type="text" id="initial4" placeholder="例: l"></td>
                    <td><input type="text" id="final4" placeholder="例: ai"></td>
                    <td><input type="text" id="tone4" placeholder="例: 2"></td>
                    <td style="background:#f8d7da;"><input type="text" id="exclude4" placeholder="排除字" class="exclude-input"></td>
                </tr>
            </tbody>
        </table>
        <div class="button-group">
            <button type="button" class="search-btn" onclick="search()">🔎 查询</button>
            <button type="button" class="clear-btn" onclick="clearForm()">🗑 清空所有</button>
        </div>
    </form>

    <div class="result-area" id="result">
        <p>✨ 等待查询...</p>
    </div>
    <div class="footer">数据来源：chinese-xinhua 成语库 | 韵母中的 "ü" 请输入 "v" | 若填写汉字，则该字的拼音条件将被忽略 | 排除字表示该位置不能是此字 | 全局条件不受位置限制</div>
</div>

<script>
    async function queryChar() {
        const char = document.getElementById('charInput').value.trim();
        if (char.length === 0) {
            document.getElementById('charResult').innerHTML = '<span style="color:red;">请输入一个汉字</span>';
            return;
        }
        if (char.length > 1) {
            document.getElementById('charResult').innerHTML = '<span style="color:red;">请输入单个汉字</span>';
            return;
        }
        try {
            const response = await fetch('/api/pinyin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ char: char })
            });
            const data = await response.json();
            if (data.error) {
                document.getElementById('charResult').innerHTML = `<span style="color:red;">${data.error}</span>`;
            } else {
                document.getElementById('charResult').innerHTML = `
                    <strong>${char}</strong> → 声母: ${data.initial || '无'} | 韵母: ${data.final} | 声调: ${data.tone}
                `;
            }
        } catch (err) {
            document.getElementById('charResult').innerHTML = `<span style="color:red;">请求失败: ${err}</span>`;
        }
    }

    function clearForm() {
        for (let i = 1; i <= 4; i++) {
            document.getElementById(`char${i}`).value = '';
            document.getElementById(`initial${i}`).value = '';
            document.getElementById(`final${i}`).value = '';
            document.getElementById(`tone${i}`).value = '';
            document.getElementById(`exclude${i}`).value = '';
        }
        document.getElementById('global_initial').value = '';
        document.getElementById('global_final').value = '';
        document.getElementById('global_char').value = '';
        document.getElementById('global_exclude_char').value = '';
        document.getElementById('result').innerHTML = '<p>✨ 已清空，等待查询...</p>';
    }

    function search() {
        const conditions = [];

        // 全局条件
        let globalInitial = document.getElementById('global_initial').value.trim();
        let globalFinal = document.getElementById('global_final').value.trim();
        let globalChar = document.getElementById('global_char').value.trim();
        let globalExcludeChar = document.getElementById('global_exclude_char').value.trim();

        if (globalInitial !== '') {
            conditions.push({ attr: 'global_initial', value: globalInitial });
        }
        if (globalFinal !== '') {
            let finalForDB = globalFinal.replace(/v/g, 'ü');
            conditions.push({ attr: 'global_final', value: finalForDB });
        }
        if (globalChar !== '') {
            conditions.push({ attr: 'global_char', value: globalChar });
        }
        if (globalExcludeChar !== '') {
            conditions.push({ attr: 'global_exclude_char', value: globalExcludeChar });
        }

        // 位置条件
        for (let pos = 1; pos <= 4; pos++) {
            const charVal = document.getElementById(`char${pos}`).value.trim();
            const initialVal = document.getElementById(`initial${pos}`).value.trim();
            const finalVal = document.getElementById(`final${pos}`).value.trim();
            let toneVal = document.getElementById(`tone${pos}`).value.trim();
            const excludeVal = document.getElementById(`exclude${pos}`).value.trim();

            if (charVal !== '') {
                conditions.push({ pos: pos, attr: 'char', value: charVal });
            } else {
                if (initialVal !== '') {
                    conditions.push({ pos: pos, attr: 'initial', value: initialVal });
                }
                if (finalVal !== '') {
                    let finalForDB = finalVal.replace(/v/g, 'ü');
                    conditions.push({ pos: pos, attr: 'final', value: finalForDB });
                }
                if (toneVal !== '') {
                    const num = parseInt(toneVal);
                    if (!isNaN(num) && num >= 1 && num <= 5) {
                        conditions.push({ pos: pos, attr: 'tone', value: num });
                    } else {
                        alert(`第${pos}字声调请输入1-5的数字`);
                        return;
                    }
                }
            }
            if (excludeVal !== '') {
                conditions.push({ pos: pos, attr: 'exclude', value: excludeVal });
            }
        }

        if (conditions.length === 0) {
            document.getElementById('result').innerHTML = '<p>⚠️ 请至少填写一个条件</p>';
            return;
        }

        fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conditions: conditions })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('result').innerHTML = `<p>❌ 错误: ${data.error}</p>`;
                return;
            }
            if (data.results.length === 0) {
                document.getElementById('result').innerHTML = '<p>😔 没有找到匹配的成语</p>';
                return;
            }
            let html = `<p>✅ 找到 ${data.results.length} 个成语：</p>`;
            for (let item of data.results) {
                html += `
                    <div class="result-item">
                        <span class="word">${item.word}</span>
                        <span class="pinyin">${item.pinyin}</span>
                        <div class="explanation">${item.explanation || '暂无解释'}</div>
                    </div>
                `;
            }
            document.getElementById('result').innerHTML = html;
        })
        .catch(err => {
            document.getElementById('result').innerHTML = `<p>❌ 请求失败: ${err}</p>`;
        });
    }
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/pinyin', methods=['POST'])
def get_pinyin():
    data = request.get_json()
    char = data.get('char', '')
    if not char or len(char) != 1:
        return jsonify({'error': '请输入一个汉字'})
    py = pinyin(char, style=Style.NORMAL)[0][0]
    initial, final = split_pinyin(py)
    tone_str = pinyin(char, style=Style.TONE3)[0][0]
    tone_num = 0
    for ch in tone_str:
        if ch.isdigit():
            tone_num = int(ch)
            break
    final_display = final.replace('ü', 'v')
    return jsonify({
        'initial': initial,
        'final': final_display,
        'tone': tone_num
    })

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    conditions = data.get('conditions', [])
    if not conditions:
        return jsonify({'error': '没有提供查询条件'})

    sql = "SELECT word, pinyin, explanation FROM idiom WHERE 1=1"
    params = []

    for cond in conditions:
        attr = cond.get('attr')
        if attr == 'global_initial':
            value = cond['value']
            sql += f" AND (initial1 = ? OR initial2 = ? OR initial3 = ? OR initial4 = ?)"
            params.extend([value, value, value, value])
        elif attr == 'global_final':
            value = cond['value']
            sql += f" AND (final1 = ? OR final2 = ? OR final3 = ? OR final4 = ?)"
            params.extend([value, value, value, value])
        elif attr == 'global_char':
            value = cond['value']
            sql += f" AND (char1 = ? OR char2 = ? OR char3 = ? OR char4 = ?)"
            params.extend([value, value, value, value])
        elif attr == 'global_exclude_char':
            value = cond['value']
            sql += f" AND (char1 != ? AND char2 != ? AND char3 != ? AND char4 != ?)"
            params.extend([value, value, value, value])
        else:
            pos = cond.get('pos')
            if not pos:
                return jsonify({'error': '位置缺失'})
            value = cond['value']
            if attr == 'char':
                col = f'char{pos}'
                sql += f" AND {col} = ?"
                params.append(value)
            elif attr == 'initial':
                col = f'initial{pos}'
                sql += f" AND {col} = ?"
                params.append(value)
            elif attr == 'final':
                col = f'final{pos}'
                sql += f" AND {col} = ?"
                params.append(value)
            elif attr == 'tone':
                col = f'tone{pos}'
                sql += f" AND {col} = ?"
                params.append(value)
            elif attr == 'exclude':
                col = f'char{pos}'
                sql += f" AND {col} != ?"
                params.append(value)
            else:
                return jsonify({'error': f'无效的属性 {attr}'})

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'word': row[0],
                'pinyin': row[1],
                'explanation': row[2][:200] if row[2] else ''
            })
        conn.close()
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

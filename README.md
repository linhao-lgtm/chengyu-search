```markdown
# 成语拼音搜索引擎 🔍

基于 Flask + SQLite + pypinyin 的成语查询工具，支持按位置（汉字、声母、韵母、声调、排除字）和全局条件（任意位置包含/排除汉字、声母、韵母）进行精确查找。提供 Web 界面，适合局域网内使用。

## ✨ 功能特点

- **汉字拼音分解**：输入任意汉字，自动显示其声母、韵母、声调（韵母中的 `ü` 显示为 `v`，方便输入）。
- **多维度位置查询**：每个字可独立设置：
  - 汉字（精确匹配）
  - 声母
  - 韵母
  - 声调（1-4）
  - 排除字（该位置不能是某个汉字）
- **全局条件**（不限制位置）：
  - 包含声母 / 韵母 / 汉字（至少一字满足）
  - 排除汉字（整个成语中不能出现该字）
- **精准快速**：所有条件为 AND 关系，结果实时显示，支持 3 万余条成语。
- **纯 Web 界面**：无需安装客户端，局域网内任何设备通过浏览器访问即可。

## 🚀 快速开始

### 1. 环境要求

- Ubuntu / Debian / 其他 Linux 发行版（或 WSL）
- Python 3.10+
- 能够连接互联网（用于下载成语数据和安装依赖）

### 2. 克隆项目

```bash
git clone https://github.com/你的用户名/chengyu-search.git
cd chengyu-search
```

### 3. 创建虚拟环境并安装依赖

```bash
python3 -m venv venv
source venv/bin/activate          # Linux/Mac
# 或 venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

如果没有 `requirements.txt`，手动安装：

```bash
pip install flask pypinyin
```

### 4. 下载成语数据并生成数据库

```bash
# 下载原始数据（约 2.3 MB）
wget https://github.com/pwxcoo/chinese-xinhua/archive/refs/heads/master.zip
unzip master.zip
cp chinese-xinhua-master/data/idiom.json .

# 运行构建脚本
python3 build_idiom_db.py
```

等待约 1-2 分钟，生成 `idiom.db` 文件。

### 5. 启动 Web 服务

```bash
python3 web_query.py
```

输出示例：
```
 * Running on all addresses (0.0.0.0)
 * Running on http://192.168.1.120:5000
```

### 6. 访问使用

在浏览器中打开 `http://你的服务器IP:5000` 即可。

## 📖 使用说明

### 界面分区

1. **汉字拼音分解查询**：输入单字，查看其声母、韵母、声调。
2. **全局条件**：
   - 全局包含：声母 / 韵母 / 汉字（任意位置至少出现一次）
   - 全局排除汉字：整个成语中不能出现该字
3. **位置条件表格**：四个字，每行可填写：
   - 汉字（若填写，则同行的声母/韵母/声调条件失效）
   - 声母、韵母、声调（可单独或组合使用）
   - 排除字（该位置不能是此字）

### 查询逻辑

- 所有填写条件为 **AND** 关系（必须同时满足）。
- 留空的条件不参与筛选。
- 若某字填写了“汉字”，则忽略该行的拼音条件，仅匹配汉字。

### 示例

- **查找“卷土重来”**：
  - 第1字汉字：`卷`
  - 第2字韵母：`u`
  - 第3字声母：`ch`
  - 第4字声母：`l`
- **查找所有包含“ang”韵母的成语**：全局包含韵母 `ang`
- **查找所有不含“死”字的成语**：全局排除汉字 `死`

## 🗂️ 项目结构

```
chengyu-search/
├── build_idiom_db.py      # 数据库构建脚本
├── web_query.py           # Flask Web 服务主程序
├── requirements.txt       # Python 依赖
├── README.md              # 本文件
├── .gitignore             # Git 忽略规则
└── idiom.db               # 生成的 SQLite 数据库（运行后产生）
```

## 📦 依赖清单

- Python 3.10+
- Flask 2.0+
- pypinyin 0.48+
- SQLite3（内置）

## 📄 数据来源

成语数据来自开源项目 [chinese-xinhua](https://github.com/pwxcoo/chinese-xinhua)，采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request，帮助改进功能或修复问题。

## 📜 许可证

本项目采用 MIT 许可证。

## ❓ 常见问题

### Q: 访问时提示“无法连接”？
A: 检查 Ubuntu 防火墙：`sudo ufw allow 5000/tcp`；确认 Flask 服务正在运行且监听 `0.0.0.0`。

### Q: 查询不到结果？
A: 使用页面上的“汉字拼音分解查询”工具确认输入的声母、韵母是否正确。注意 `ü` 需用 `v` 代替。

### Q: 如何后台运行？
A: 使用 `nohup python3 web_query.py > web.log 2>&1 &` 或 `screen`。

## 🙏 致谢

感谢 [chinese-xinhua](https://github.com/pwxcoo/chinese-xinhua) 提供成语数据。

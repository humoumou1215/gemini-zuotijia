# Gemini 做题助手

一个基于Google Gemini的智能题目解答助手，可以自动识别屏幕中的题目并给出答案。

## 功能特点

- 一键截屏并识别题目
- 使用Google Gemini AI进行智能分析
- 通过语音播报答案
- 支持快捷键操作（默认Shift+R）

## 安装要求

- Python 3.6+
- Google Gemini API密钥
- Windows操作系统（目前仅支持Windows）

## 安装方法

1. 克隆仓库：
```bash
git clone [你的仓库地址]
cd gemini-zuotijia
```

2. 安装依赖：
```bash
conda create -n gemini-zuotijia python=3.11
conda activate gemini-zuotijia
pip install --upgrade pip
pip install -e .
```

3. 调试应用
```bash
python screen_gemini_assistant.py
```
按下Shift+R测试截图、API调用和语音播报功能。

4. QA
本地运行可能在命令行中没有通过代理访问，网络不通，需要设置代理。在power shell中举例如下：
```bash
$env:http_proxy="http://127.0.0.1:7890"
$env:https_proxy="http://127.0.0.1:7890"
```
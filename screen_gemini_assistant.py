import os
import keyboard
import pyautogui
from PIL import Image
import google.generativeai as genai
from gtts import gTTS
from playsound import playsound
import threading
import time
from dotenv import load_dotenv
import io
import datetime

# 加载环境变量
load_dotenv()

# 配置 Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("错误：GOOGLE_API_KEY 环境变量未设置。")
    exit()
genai.configure(api_key=GOOGLE_API_KEY)

"""
$env:http_proxy="http://127.0.0.1:7890"
$env:https_proxy="http://127.0.0.1:7890"
"""

# 配置快捷键
HOTKEY = 'shift+r'  # 您可以更改为您想要的快捷键

# 创建tmp目录
TMP_DIR = os.path.join(os.getcwd(), 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# 用于存储当前播放的音频文件路径
current_audio_file = None
# 用于存储当前处理线程
current_thread = None
# 标记是否正在处理任务
is_processing = False

def stop_current_task():
    global is_processing, current_audio_file, current_thread
    if is_processing:
        is_processing = False
        # 如果有音频文件正在播放，尝试删除它
        if current_audio_file and os.path.exists(current_audio_file):
            try:
                os.remove(current_audio_file)
            except Exception as e:
                print(f"清理音频文件时发生错误: {e}")
        current_audio_file = None
        # 如果有正在运行的线程，等待它结束
        if current_thread and current_thread.is_alive():
            current_thread.join(timeout=1)

# 在文件开头导入新的库
import winsound

# 在文件开头添加新的导入
from pydub import AudioSegment
from pydub.playback import play

def capture_and_process():
    global is_processing, current_audio_file, current_thread
    
    # 停止当前正在执行的任务
    stop_current_task()
    
    is_processing = True
    print(f"快捷键 {HOTKEY} 被按下，开始处理...")

    try:
        # 1. 截取当前屏幕
        print("正在截取屏幕...")
        screenshot = pyautogui.screenshot()
        # 将 PIL Image 对象转换为字节流，以便发送给 Gemini
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        print("屏幕截图成功。")

        # 准备图像部分的内容
        image_part = {
            "mime_type": "image/png",
            "data": img_byte_arr
        }

        # 2. 获取用户问题
        user_question = """
            1、使用中文回答问题
            2、使用简短的自然语音回答问题，不要使用过多的符号（如*号等），字数不要超过100字。你的回答开头2个字永远是“好的”
            3、查看图片内容，查找图片中是否有一个编程领域的问题，题目通常是选择题的形式。
            4、如果没有找到问题，返回“没有找到编程问题”，不用多说其他废话。
            5、如果找到问题，只需要说出问题的答案。
        """
        print(f"用户问题：{user_question}")

        # 3. 发送问题和截图给 Gemini
        print("正在发送请求给 Gemini API...")
        model = genai.GenerativeModel('gemini-2.0-flash') # 使用支持图像的模型
        try:
            response = model.generate_content([user_question, image_part])
            print("Gemini API 调用完成。") # 新增日志
            print(f"原始响应对象: {response}") # 新增日志，打印完整响应对象
            print(f"响应 Candidates: {response.candidates}") # 新增日志，打印 candidates
            print(f"响应 Prompt Feedback: {response.prompt_feedback}") # 新增日志，打印 prompt_feedback

            if response.parts:
                gemini_response_text = response.text
            else:
                # 如果没有 parts，尝试从 prompt_feedback 获取是否有阻塞信息
                block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else '未知原因'
                gemini_response_text = f"Gemini API 未返回有效内容，可能已被阻止。原因：{block_reason}"
                # 尝试获取更详细的完成原因
                if response.candidates and response.candidates[0].finish_reason:
                     gemini_response_text += f" Finish reason: {response.candidates[0].finish_reason.name}"
                # 检查是否有安全相关的拒绝
                if response.prompt_feedback and response.prompt_feedback.block_reason == 'SAFETY':
                    gemini_response_text += " (内容可能因安全策略被阻止)"
                    # 可以考虑打印更详细的安全评分信息，如果API提供的话
                    # for rating in response.prompt_feedback.safety_ratings:
                    #     print(f"  Category: {rating.category}, Probability: {rating.probability.name}")

        except Exception as api_call_error:
            print(f"调用 Gemini API 时发生错误: {api_call_error}") # 新增API调用特定错误捕获
            gemini_response_text = f"调用 Gemini API 失败: {str(api_call_error)[:200]}" # 将错误信息传递下去

        print(f"Gemini 响应文本: {gemini_response_text}") # 修改日志，确保在任何情况下都打印

        # 4. 将 Gemini 的响应转换为语音并播报
        if gemini_response_text and is_processing:  # 检查是否被中断
            print("正在将文本转换为语音...")
            # 使用时间戳创建唯一的音频文件名，保存在tmp目录
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            current_audio_file = os.path.join(TMP_DIR, f"response_{timestamp}.mp3")
            
            tts = gTTS(text=gemini_response_text, lang='zh-cn')
            tts.save(current_audio_file)
            print(f"语音文件已保存为 {current_audio_file}")
            
            # 修改播放音频的部分
            def play_audio(audio_file):
                try:
                    # 直接使用pydub播放，不需要额外的音频库
                    audio = AudioSegment.from_mp3(audio_file)
                    current_wav_file = os.path.join(TMP_DIR, f"response_{timestamp}.wav")
                    # 导出为wav格式并播放
                    audio.export(current_wav_file, format="wav")
                    print(f"音频文件已保存为 {current_wav_file}")
                    winsound.PlaySound(current_wav_file, winsound.SND_FILENAME)
                    # play(current_wav_file)
                    if os.path.exists(current_wav_file):
                        os.remove(current_wav_file)
                        current_wav_file = None
                except Exception as e:
                    print(f"播放音频时发生错误: {e}")
            
            if is_processing:  # 再次检查是否被中断
                print("正在播放语音...")
                play_audio(current_audio_file)
                print("语音播放完毕。")
            
            # 播放完成后删除音频文件
            if os.path.exists(current_audio_file):
                try:
                    os.remove(current_audio_file)
                    current_audio_file = None
                except Exception as e:
                    print(f"删除音频文件时发生错误: {e}")
        else:
            print("Gemini 未返回文本响应或任务已被中断，无法播报。")

    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        if is_processing:  # 只在未被中断的情况下播报错误
            try:
                error_message = f"处理失败，错误信息：{str(e)[:100]}"
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                current_audio_file = os.path.join(TMP_DIR, f"error_{timestamp}.mp3")
                
                # 在错误处理部分也要替换
                tts = gTTS(text=error_message, lang='zh-cn')
                tts.save(current_audio_file)
                play_audio(current_audio_file)
                
                if os.path.exists(current_audio_file):
                    os.remove(current_audio_file)
                    current_audio_file = None
            except Exception as audio_err:
                print(f"播报错误信息失败: {audio_err}")
    finally:
        is_processing = False
        current_thread = None

def listen_for_hotkey():
    global current_thread
    print(f"程序已启动，正在监听快捷键 {HOTKEY}...")
    print("按下快捷键以截图、发送问题给 Gemini 并播报响应。")
    print("要停止程序，请关闭此窗口或按 Ctrl+C (如果从命令行运行)。")
    
    def start_capture():
        global current_thread
        current_thread = threading.Thread(target=capture_and_process, daemon=True)
        current_thread.start()
    
    keyboard.add_hotkey(HOTKEY, start_capture)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序被用户中断。")
    finally:
        print("程序正在退出...")
        stop_current_task()
        keyboard.remove_all_hotkeys()

if __name__ == "__main__":
    # 确保 .env 文件中的 GOOGLE_API_KEY 已设置
    if not GOOGLE_API_KEY:
        print("请在 .env 文件中或环境变量中设置 GOOGLE_API_KEY。")
    else:
        # 不再需要占位符替换逻辑，直接使用导入的 keyboard
        try:
            listen_for_hotkey()
        except ImportError:
            print("错误：无法导入 'keyboard' 库。请确保已安装：pip install keyboard")
        except Exception as e:
            print(f"启动监听时发生未知错误: {e}")
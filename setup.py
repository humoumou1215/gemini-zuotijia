from setuptools import setup, find_packages

setup(
    name="gemini-zuotijia",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'keyboard',
        'pyautogui',
        'Pillow',
        'google-generativeai',
        'gTTS',
        'playsound',
        'python-dotenv',
        'pydub',
    ],
    entry_points={
        'console_scripts': [
            'gemini-zuotijia=screen_gemini_assistant:listen_for_hotkey',
        ],
    },
    author="Your Name",
    description="一个基于Gemini的编程题目自动解答助手",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
)
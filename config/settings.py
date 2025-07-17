import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API配置
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    TIKHUB_API_KEY = os.environ.get('TIKHUB_API_KEY') 
    TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN')
    
    # API端点
    TIKHUB_BASE_URL = 'https://api.tikhub.io/api/v1'
    GEMINI_BASE_URL = os.environ.get('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta')
    
    # 限制配置
    MAX_VIDEO_COUNT = 10  # 最大批量处理视频数
    MAX_VIDEO_DURATION = 8 * 60 * 60  # 8小时限制（秒）
    DEFAULT_STOCK_DAYS = 30  # 默认股票数据天数
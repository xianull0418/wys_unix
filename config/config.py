import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # MySQL数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'douban_movie')
    
    # 爬虫配置
    CRAWL_INTERVAL = int(os.getenv('CRAWL_INTERVAL', 1))  # 爬虫间隔(秒)
    MAX_THREADS = int(os.getenv('MAX_THREADS', 5))        # 最大线程数
    
    # API配置
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    
    # 豆瓣网站配置
    DOUBAN_URL = 'https://movie.douban.com'
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    ] 
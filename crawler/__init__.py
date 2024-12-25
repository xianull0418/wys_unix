from abc import ABC, abstractmethod
from typing import List, Dict, Any
import random
import time
from fake_useragent import UserAgent
import requests
from bs4 import BeautifulSoup
from config.config import Config
import urllib3
import warnings

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class BaseCrawler(ABC):
    def __init__(self):
        self.headers = {'User-Agent': UserAgent().random}
        self.config = Config()
        
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.config.USER_AGENTS)
    
    def _get_soup(self, url: str) -> BeautifulSoup:
        """获取页面解析对象"""
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Connection': 'close'
        }
        session = requests.Session()
        response = session.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'lxml')
    
    def _handle_rate_limit(self):
        """处理请求限制"""
        time.sleep(self.config.CRAWL_INTERVAL)
    
    @abstractmethod
    def crawl(self, *args, **kwargs):
        """爬取数据的抽象方法"""
        pass 
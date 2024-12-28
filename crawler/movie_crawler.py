from typing import List, Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import BaseCrawler
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os

class MovieCrawler(BaseCrawler):
    def __init__(self, db_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
        self.driver = None
        self.use_selenium = False  # 是否使用 Selenium
        self._init_chrome_options()  # 预初始化 Chrome 选项
    
    def _init_chrome_options(self):
        """初始化 Chrome 选项"""
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')  # 无头模式
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('--disable-logging')
        self.chrome_options.add_argument('--disable-notifications')
        self.chrome_options.add_argument('--disable-default-apps')
        self.chrome_options.add_argument('--disable-popup-blocking')
        self.chrome_options.add_argument('--window-size=1920,1080')  # 设置窗口大小
        self.chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
        self.chrome_options.add_argument('--ignore-ssl-errors')  # 忽略SSL错误
        self.chrome_options.page_load_strategy = 'eager'
    
    def _init_driver(self):
        """初始化 Selenium WebDriver"""
        if not self.driver:
            try:
                # 设置下载路径为当前目录
                chrome_driver_path = os.path.join(os.getcwd(), 'chromedriver')
                os.environ['WDM_LOCAL'] = '1'  # 使用本地缓存
                os.environ['WDM_SSL_VERIFY'] = '0'  # 禁用SSL验证
                
                # 添加随机User-Agent
                self.chrome_options.add_argument(f'user-agent={self._get_random_user_agent()}')
                
                # 使用 Service 对象
                service = Service()
                self.driver = webdriver.Chrome(
                    service=service,
                    options=self.chrome_options
                )
                
                # 设置超时时间
                self.driver.set_page_load_timeout(20)
                self.driver.implicitly_wait(10)
                
            except Exception as e:
                self.logger.error(f"初始化WebDriver失败: {str(e)}")
                if self.driver:
                    self.driver.quit()
                raise
    
    def crawl(self, *args, **kwargs):
        """实现抽象方法"""
        pass
    
    def get_movie_detail(self, douban_id: str) -> Dict[str, Any]:
        """获取电影详细信息"""
        try:
            # 获取详细信息
            detail_url = f"https://movie.douban.com/subject/{douban_id}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.100.4758.11 Safari/537.36'
            }
            
            detail_response = requests.get(detail_url, headers=headers)
            detail_response.raise_for_status()
            
            soup = BeautifulSoup(detail_response.text, 'html.parser')
            
            # 获取基本信息
            name = soup.select_one('meta[property="og:title"]')['content']
            img_url = soup.select_one('meta[property="og:image"]')['content']
            
            # 处理图片URL
            if img_url:
                img_url = img_url.replace('s_ratio', 'l_ratio')
                img_url = img_url.replace('img1.doubanio.com', 'img9.doubanio.com')
                img_url = img_url.replace('img2.doubanio.com', 'img9.doubanio.com')
                img_url = img_url.replace('img3.doubanio.com', 'img9.doubanio.com')
            
            # 获取年份和副标题
            year = None
            sub_title = ''
            title_element = soup.select_one('#content h1')
            if title_element:
                # 处理年份
                year_match = re.search(r'\((\d{4})\)', title_element.text)
                if year_match:
                    year = year_match.group(1)
                    name = re.sub(r'\s*\(\d{4}\)\s*', '', name)  # 从标题中移除年份
                
                # 处理副标题
                spans = title_element.select('span.year')
                if len(spans) > 0:
                    # 移除副标题中的年份部分
                    title_text = title_element.text.replace(spans[0].text, '').strip()
                    # 获取主标题之后的文本作为副标题
                    if name in title_text:
                        sub_title = title_text.replace(name, '').strip()
            
            # 获取其他信息
            director = soup.select_one('a[rel="v:directedBy"]')
            director = director.text.strip() if director else '未知'
            
            rating_element = soup.select_one('#interest_sectl strong.rating_num')
            rating = float(rating_element.text.strip()) if rating_element else None
            
            actors_element = soup.select('a[rel="v:starring"]')
            actors = '/'.join([actor.text.strip() for actor in actors_element[:3]]) if actors_element else ''
            
            genre_elements = soup.select('span[property="v:genre"]')
            genre = '/'.join([g.text.strip() for g in genre_elements]) if genre_elements else ''
            
            release_date = soup.select_one('span[property="v:initialReleaseDate"]')
            release_date = datetime.strptime(release_date.text.split('(')[0], '%Y-%m-%d') if release_date else None
            
            return {
                'douban_id': douban_id,
                'name': name,
                'rating': rating,
                'director': director,
                'actors': actors,
                'genre': genre,
                'release_date': release_date,
                'img_url': img_url,
                'year': year,
                'sub_title': sub_title
            }
            
        except Exception as e:
            self.logger.error(f"获取电影详情失败: {str(e)}")
            raise
    
    def search_movies(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索电影"""
        try:
            # 首先尝试使用普通请求
            if not self.use_selenium:
                try:
                    return self._search_with_api(keyword)
                except Exception as e:
                    self.logger.warning(f"API搜索失败，切换到Selenium模式: {str(e)}")
                    self.use_selenium = True
                    # 显示切换提示
                    print("检测到豆瓣反爬限制，正在切换到浏览器模式...")
            
            # 如果API请求失败，使用Selenium
            return self._search_with_selenium(keyword)
            
        except Exception as e:
            self.logger.error(f"搜索电影失败: {str(e)}")
            return []
    
    def _search_with_api(self, keyword: str) -> List[Dict[str, Any]]:
        """使用API搜索"""
        url = f"https://movie.douban.com/j/subject_suggest?q={keyword}"
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://movie.douban.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': self._get_random_user_agent()
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        if '检测到有异常请求' in response.text:
            raise Exception("检测到反爬限制")
            
        movies_data = response.json()
        return self._process_api_results(movies_data)
    
    def _search_with_selenium(self, keyword: str) -> List[Dict[str, Any]]:
        """使用Selenium搜索"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                self._init_driver()
                url = f"https://movie.douban.com/subject_search?search_text={keyword}"
                self.driver.get(url)
                
                # 等待搜索结果加载
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'item-root'))
                    )
                except Exception as e:
                    self.logger.warning(f"等待搜索结果超时: {str(e)}")
                    return []
                
                # 获取页面内容并解析
                movies = []
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                items = soup.select('.item-root')
                
                if not items:
                    self.logger.warning("未找到搜索结果")
                    return []
                
                for item in items[:10]:
                    try:
                        movie_info = self._extract_movie_info(item)
                        if movie_info:
                            movies.append(movie_info)
                    except Exception as e:
                        self.logger.error(f"处理电影信息失败: {str(e)}")
                        continue
                
                return movies
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Selenium搜索失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count >= max_retries:
                    return []
                time.sleep(2)  # 等待2秒后重试
                
            finally:
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
    
    def _process_api_results(self, movies_data: List[Dict]) -> List[Dict[str, Any]]:
        """处理API搜索结果"""
        movies = []
        for movie in movies_data[:10]:
            if movie.get('type') == 'movie':
                try:
                    # 获取电影详情以获取评分和导演信息
                    detail_url = f"https://movie.douban.com/subject/{movie.get('id')}/"
                    headers = {
                        'User-Agent': self._get_random_user_agent(),
                        'Referer': 'https://movie.douban.com/'
                    }
                    
                    # 添加随机延时避免被封
                    time.sleep(random.uniform(1, 2))
                    
                    detail_response = requests.get(detail_url, headers=headers, timeout=5)
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    
                    # 获取评分
                    rating_element = detail_soup.select_one('#interest_sectl strong.rating_num')
                    rating = float(rating_element.text.strip()) if rating_element else None
                    
                    # 获取导演
                    director = ''
                    director_element = detail_soup.select_one('a[rel="v:directedBy"]')
                    if director_element:
                        director = director_element.text.strip()
                    
                    movie_info = {
                        'douban_id': movie.get('id'),
                        'name': movie.get('title', ''),
                        'year': movie.get('year', ''),
                        'img': movie.get('img', '').replace('s_ratio', 'l_ratio'),
                        'director': director,  # 使用从详情页获取的导演信息
                        'rating': rating,
                        'sub_title': '',
                        'is_added': self.db_manager.check_movie_exists(movie.get('id'))
                    }
                    movies.append(movie_info)
                except Exception as e:
                    self.logger.error(f"处理电影信息失败: {str(e)}")
        return movies
    
    def _process_selenium_results(self, page_source: str) -> List[Dict[str, Any]]:
        """处理Selenium搜索结果"""
        soup = BeautifulSoup(page_source, 'html.parser')
        movies = []
        
        for item in soup.select('.item-root')[:10]:
            try:
                movie_info = self._extract_movie_info(item)
                if movie_info:
                    movies.append(movie_info)
            except Exception as e:
                self.logger.error(f"处理电影信息失败: {str(e)}")
                continue
        
        return movies
    
    def _extract_movie_info(self, item: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """从搜索结果项提取电影信息"""
        try:
            link = item.select_one('a.cover-link')
            if not link:
                return None
            
            douban_id = re.search(r'subject/(\d+)/', link.get('href', '')).group(1)
            title = item.select_one('.title')
            name = title.text.strip() if title else ''
            
            # 提取年份
            year = ''
            year_match = re.search(r'\((\d{4})\)', name)
            if year_match:
                year = year_match.group(1)
                name = re.sub(r'\s*\(\d{4})\s*', '', name)
            
            # 获取评分
            rating = None
            rating_element = item.select_one('.rating_nums')
            if rating_element and rating_element.text.strip():
                try:
                    rating = float(rating_element.text.strip())
                except ValueError:
                    rating = None
            
            # 获取导演等信息
            info = item.select_one('.subject-cast')
            director = ''
            if info:
                info_text = info.text.strip()
                director_match = re.search(r'导演:\s*(.*?)(?:\s+|$)', info_text)
                if director_match:
                    director = director_match.group(1).strip()
            
            # 获取图片URL
            img_url = ''
            img_element = item.select_one('img')
            if img_element:
                img_url = img_element.get('src', '').replace('s_ratio', 'l_ratio')
            
            return {
                'douban_id': douban_id,
                'name': name,
                'year': year,
                'img': img_url,
                'director': director,
                'rating': rating,
                'sub_title': '',
                'genre': '',  # 添加空的genre字段
                'is_added': self.db_manager.check_movie_exists(douban_id)
            }
        except Exception as e:
            self.logger.error(f"提取电影信息失败: {str(e)}")
            return None
    
    def get_movie_comments(self, douban_id: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """获取电影评论"""
        comments = []
        try:
            for page in range(max_pages):
                url = f"https://movie.douban.com/subject/{douban_id}/comments"
                params = {
                    'start': page * 20,
                    'limit': 20,
                    'status': 'P',
                    'sort': 'new_score'
                }
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Connection': 'close',
                    'Host': 'movie.douban.com',
                    'Referer': 'https://movie.douban.com/'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 获取评论区域
                comment_items = soup.find_all('div', class_='comment-item')
                
                for item in comment_items:
                    try:
                        # 获取用户名
                        user = item.find('span', class_='comment-info').find('a').text.strip()
                        
                        # 获取评论内容
                        comment_text = item.find('span', class_='short').text.strip()
                        
                        # 获取评论时间并处理格式
                        date_str = item.find('span', class_='comment-time').get('title', '').strip()
                        if not date_str:  # 如果title属性为空，获取文本内容
                            date_str = item.find('span', class_='comment-time').text.strip()
                        
                        try:
                            # 尝试解析完整的日期时间格式
                            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                # 尝试解析只有日期的格式
                                date = datetime.strptime(date_str, '%Y-%m-%d')
                            except ValueError:
                                # 如果都失败了，只保留日期部分
                                date_str = date_str.split()[0]  # 取第一部分（日期）
                                date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # 只有评论内容不为空时才添加
                        if comment_text.strip():
                            comments.append({
                                'user': user,
                                'comment_text': comment_text,
                                'date': date,
                                'sentiment': None
                            })
                        
                    except Exception as e:
                        self.logger.error(f"解析评论失败: {str(e)}")
                        continue
                
                # 检查是否获取到评论
                if not comment_items:
                    self.logger.warning(f"页面 {page + 1} 未获取到评论，可能需要登录或遇到反爬限制")
                    break
                
                # 添加随机延时避免被封
                time.sleep(random.uniform(2, 4))
            
            if not comments:
                self.logger.warning("未获取到任何有效评论")
            else:
                self.logger.info(f"成功获取 {len(comments)} 条评论")
            
            return comments
            
        except Exception as e:
            self.logger.error(f"获取电影评论失败: {str(e)}")
            return [] 
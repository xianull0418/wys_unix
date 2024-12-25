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

class MovieCrawler(BaseCrawler):
    def __init__(self, db_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
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
            # 使用豆瓣搜索API
            url = f"https://movie.douban.com/j/subject_suggest?q={keyword}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://movie.douban.com/',
                'Host': 'movie.douban.com',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # 随机延时
            time.sleep(random.uniform(1, 2))
            
            session = requests.Session()
            retries = 3
            while retries > 0:
                try:
                    response = session.get(
                        url, 
                        headers=headers,
                        timeout=10,
                        verify=True  # 启用SSL验证
                    )
                    response.raise_for_status()
                    movies_data = response.json()
                    break
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        raise
                    time.sleep(random.uniform(2, 3))  # 失败后随机延时
            
            # 处理搜索结果
            movies = []
            for movie in movies_data[:10]:
                if movie.get('type') == 'movie':
                    try:
                        # 每个详情请求之间添加随机延时
                        time.sleep(random.uniform(1, 2))
                        movie_info = self._get_movie_detail_simple(movie)
                        if movie_info:
                            movies.append(movie_info)
                    except Exception as e:
                        self.logger.error(f"获取电影详情失败: {str(e)}")
                        continue
            
            return movies
            
        except Exception as e:
            self.logger.error(f"搜索电影失败: {str(e)}")
            return []
    
    def _get_movie_detail_simple(self, movie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取单个电影的简单信息（用于搜索结果）"""
        try:
            movie_info = {
                'douban_id': movie_data.get('id'),
                'name': movie_data.get('title'),
                'year': movie_data.get('year'),
                'img': movie_data.get('img'),
                'sub_title': '',
                'is_added': self.db_manager.check_movie_exists(movie_data.get('id'))
            }
            
            # 处理图片URL
            if movie_info['img']:
                movie_info['img'] = movie_info['img'].replace('s_ratio', 'l_ratio')
            
            # 获取详细信息
            detail_url = f"https://movie.douban.com/subject/{movie_info['douban_id']}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Host': 'movie.douban.com',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            session = requests.Session()
            response = session.get(
                detail_url, 
                headers=headers,
                timeout=10,
                verify=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取评分和导演
            rating_element = soup.select_one('#interest_sectl strong.rating_num')
            movie_info['rating'] = float(rating_element.text.strip()) if rating_element else None
            
            director_element = soup.select_one('a[rel="v:directedBy"]')
            movie_info['director'] = director_element.text.strip() if director_element else '未知'
            
            return movie_info
            
        except Exception as e:
            self.logger.error(f"获取电影详情失败: {str(e)}")
            return None
    
    def get_movie_comments(self, movie_id: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """获取电影评论"""
        try:
            url = f"{self.config.DOUBAN_URL}/subject/{movie_id}/comments"
            comments = []
            
            for page in range(max_pages):
                page_url = f"{url}?start={page * 20}&limit=20&sort=new_score"
                soup = self._get_soup(page_url)
                
                comment_items = soup.find_all('div', class_='comment-item')
                for item in comment_items:
                    try:
                        user = item.find('span', class_='comment-info').find('a').text.strip()
                        comment_text = item.find('span', class_='short').text.strip()
                        date = item.find('span', class_='comment-time').text.strip()
                        
                        comments.append({
                            'user': user,
                            'comment_text': comment_text,
                            'date': datetime.strptime(date, '%Y-%m-%d'),
                            'sentiment': None  # 情感分析将在后续处理
                        })
                    except Exception as e:
                        self.logger.error(f"解析评论失败: {str(e)}")
                        continue
                
                self._handle_rate_limit()
            
            return comments
            
        except Exception as e:
            self.logger.error(f"获取电影评论失败: {str(e)}")
            return [] 
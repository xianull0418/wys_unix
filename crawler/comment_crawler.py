from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor
from . import BaseCrawler
from database.models import Comment
from datetime import datetime

class CommentCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def _parse_comment(self, item) -> Dict[str, Any]:
        """解析单个评论信息"""
        try:
            # 获取用户名
            user = item.find('span', class_='comment-info').find('a').text.strip()
            
            # 获取评论内容
            comment_text = item.find('span', class_='short').text.strip()
            
            # 获取评论时间
            date_str = item.find('span', class_='comment-time').text.strip()
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            return {
                'user': user,
                'comment_text': comment_text,
                'date': date,
                'sentiment': None  # 情感分析将在后续处理
            }
        except Exception as e:
            self.logger.error(f"解析评论失败: {str(e)}")
            return None
    
    def _crawl_movie_comments(self, movie_id: str, page: int) -> List[Dict[str, Any]]:
        """爬取单个电影单页评论"""
        try:
            url = f"{self.config.DOUBAN_URL}/subject/{movie_id}/comments?start={(page-1)*20}&limit=20&status=P&sort=new_score"
            soup = self._get_soup(url)
            comment_items = soup.find_all('div', class_='comment-item')
            
            comments = []
            for item in comment_items:
                comment_data = self._parse_comment(item)
                if comment_data:
                    comment_data['movie_id'] = movie_id
                    comments.append(comment_data)
                    
            self._handle_rate_limit()
            return comments
            
        except Exception as e:
            self.logger.error(f"爬取电影{movie_id}第{page}页评论失败: {str(e)}")
            return []
    
    def crawl(self, movie_id: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        爬取指定电影的评论
        :param movie_id: 电影ID
        :param max_pages: 最大爬取页数
        :return: 评论数据列表
        """
        all_comments = []
        
        with ThreadPoolExecutor(max_workers=self.config.MAX_THREADS) as executor:
            future_to_page = {
                executor.submit(self._crawl_movie_comments, movie_id, page): page 
                for page in range(1, max_pages + 1)
            }
            
            for future in future_to_page:
                page = future_to_page[future]
                try:
                    comments = future.result()
                    all_comments.extend(comments)
                    self.logger.info(f"成功爬取电影{movie_id}第{page}页评论，获取{len(comments)}条评论")
                except Exception as e:
                    self.logger.error(f"处理电影{movie_id}第{page}页评论失败: {str(e)}")
        
        return all_comments 
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from database.models import Movie, Comment

class DataCleaner:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def clean_movie_data(self, movies: List[Movie]) -> pd.DataFrame:
        """
        清洗电影数据
        :param movies: 电影对象列表
        :return: 清洗后的DataFrame
        """
        try:
            # 转换为DataFrame
            df = pd.DataFrame([{
                'id': movie.id,
                'name': movie.name,
                'rating': movie.rating,
                'director': movie.director,
                'actors': movie.actors,
                'genre': movie.genre,
                'release_date': movie.release_date
            } for movie in movies])
            
            # 处理缺失值
            df['rating'].fillna(df['rating'].mean(), inplace=True)
            df['director'].fillna('未知', inplace=True)
            df['actors'].fillna('未知', inplace=True)
            df['genre'].fillna('其他', inplace=True)
            
            # 处理异常值
            df.loc[df['rating'] > 10, 'rating'] = 10
            df.loc[df['rating'] < 0, 'rating'] = 0
            
            # 标准化处理
            df['genre'] = df['genre'].str.strip()
            df['director'] = df['director'].str.strip()
            df['actors'] = df['actors'].str.strip()
            
            self.logger.info("电影数据清洗完成")
            return df
            
        except Exception as e:
            self.logger.error(f"电影数据清洗失败: {str(e)}")
            raise
    
    def clean_comment_data(self, comments: List[Comment]) -> pd.DataFrame:
        """
        清洗评论数据
        :param comments: 评论对象列表
        :return: 清洗后的DataFrame
        """
        try:
            # 转换为DataFrame
            df = pd.DataFrame([{
                'id': comment.id,
                'movie_id': comment.movie_id,
                'user': comment.user,
                'comment_text': comment.comment_text,
                'sentiment': comment.sentiment,
                'date': comment.date
            } for comment in comments])
            
            # 处理缺失值
            df['comment_text'].fillna('', inplace=True)
            df['user'].fillna('匿名用户', inplace=True)
            
            # 去除重复评论
            df.drop_duplicates(subset=['movie_id', 'user', 'comment_text'], keep='first', inplace=True)
            
            # 去除空评论
            df = df[df['comment_text'].str.len() > 0]
            
            # 文本清洗
            df['comment_text'] = df['comment_text'].apply(self._clean_text)
            
            self.logger.info("评论数据清洗完成")
            return df
            
        except Exception as e:
            self.logger.error(f"评论数据清洗失败: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """清洗文本数据"""
        if not isinstance(text, str):
            return ''
        
        # 去除特殊字符
        text = text.strip()
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')
        
        # 去除多余空格
        text = ' '.join(text.split())
        
        return text 
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any
import logging
from wordcloud import WordCloud
import jieba
from collections import Counter
import numpy as np
from database.models import Movie, Comment
from database.db_manager import DatabaseManager

class DataVisualizer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
    
    def plot_rating_distribution(self, movies: List[Movie], save_path: str = None):
        """绘制电影评分分布图"""
        try:
            ratings = [movie.rating for movie in movies]
            plt.figure(figsize=(10, 6))
            sns.histplot(ratings, bins=20)
            plt.title('电影评分分布')
            plt.xlabel('评分')
            plt.ylabel('数量')
            
            if save_path:
                plt.savefig(save_path)
                plt.close()
            else:
                plt.show()
                
        except Exception as e:
            self.logger.error(f"绘制评分分布图失败: {str(e)}")
    
    def plot_genre_statistics(self, movies: List[Movie], save_path: str = None):
        """绘制电影类型统计图"""
        try:
            # 统计各类型电影数量
            genre_counter = Counter()
            for movie in movies:
                genres = movie.genre.split('/')
                genre_counter.update(genres)
            
            # 绘制柱状图
            plt.figure(figsize=(12, 6))
            genres = list(genre_counter.keys())
            counts = list(genre_counter.values())
            
            plt.bar(genres, counts)
            plt.title('电影类型分布')
            plt.xlabel('类型')
            plt.ylabel('数量')
            plt.xticks(rotation=45)
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
                plt.close()
            else:
                plt.show()
                
        except Exception as e:
            self.logger.error(f"绘制类型统计图失败: {str(e)}")
    
    def generate_wordcloud(self, comments: List[Comment], save_path: str = None):
        """生成评论词云图"""
        try:
            # 合并所有评论文本
            text = ' '.join([comment.comment_text for comment in comments])
            
            # 分词
            words = jieba.cut(text)
            word_space_split = ' '.join(words)
            
            # 生成词云
            wordcloud = WordCloud(
                font_path='simhei.ttf',  # 中文字体路径
                width=800,
                height=400,
                background_color='white'
            ).generate(word_space_split)
            
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            
            if save_path:
                plt.savefig(save_path)
                plt.close()
            else:
                plt.show()
                
        except Exception as e:
            self.logger.error(f"生成词云图失败: {str(e)}")
    
    def plot_sentiment_analysis(self, movie_id: int, save_path: str = None):
        """绘制情感分析结果图"""
        try:
            comments = self.db_manager.get_movie_comments(movie_id)
            sentiments = [comment.sentiment for comment in comments if comment.sentiment]
            
            # 统计各情感类型数量
            sentiment_counts = Counter(sentiments)
            
            # 绘制饼图
            plt.figure(figsize=(8, 8))
            plt.pie(
                sentiment_counts.values(),
                labels=sentiment_counts.keys(),
                autopct='%1.1f%%'
            )
            plt.title('评论情感分布')
            
            if save_path:
                plt.savefig(save_path)
                plt.close()
            else:
                plt.show()
                
        except Exception as e:
            self.logger.error(f"绘制情感分析图失败: {str(e)}") 
from typing import List, Dict, Any
import logging
from snownlp import SnowNLP
import pandas as pd
import os
from database.models import Comment
from database.db_manager import DatabaseManager
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba

class SentimentAnalyzer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # 确保存储目录存在
        self.static_dir = 'web/static/analysis'
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)
    
    def analyze_movie(self, movie_id: int) -> Dict[str, Any]:
        """
        分析电影评论
        :param movie_id: 电影ID
        :return: 分析结果
        """
        try:
            # 获取电影评论
            comments = self.db_manager.get_movie_comments(movie_id)
            
            # 情感分析
            sentiment_results = []
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            
            for comment in comments:
                if not comment.sentiment:  # 如果评论还没有情感分析结果
                    analysis = self._analyze_comment(comment.comment_text)
                    # 更新数据库
                    self.db_manager.update_comment_sentiment(comment.id, analysis['sentiment'])
                    sentiment = analysis['sentiment']
                else:
                    sentiment = comment.sentiment
                
                # 统计情感分布
                if sentiment == '正面':
                    positive_count += 1
                elif sentiment == '负面':
                    negative_count += 1
                else:
                    neutral_count += 1
            
            # 生成词云
            wordcloud_path = self._generate_wordcloud(comments, movie_id)
            
            # 生成情感分析图表
            sentiment_chart_path = self._generate_sentiment_chart(
                positive_count, neutral_count, negative_count, movie_id
            )
            
            # 保存分析结果
            result = {
                'wordcloud_path': f'/static/analysis/wordcloud_{movie_id}.png',
                'sentiment_chart_path': f'/static/analysis/sentiment_{movie_id}.png',
                'positive_count': positive_count,
                'neutral_count': neutral_count,
                'negative_count': negative_count
            }
            
            # 保存到数据库
            self.db_manager.save_analysis_result(movie_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"电影评论分析失败: {str(e)}")
            raise
    
    def _analyze_comment(self, text: str) -> Dict[str, Any]:
        """分析单条评论的情感倾向"""
        try:
            s = SnowNLP(text)
            sentiment_score = s.sentiments
            
            # 根据分数判断情感倾向
            if sentiment_score > 0.6:
                sentiment = '正面'
            elif sentiment_score < 0.4:
                sentiment = '负面'
            else:
                sentiment = '中性'
            
            return {
                'score': sentiment_score,
                'sentiment': sentiment
            }
        except Exception as e:
            self.logger.error(f"情感分析失败: {str(e)}")
            return {'score': 0.5, 'sentiment': '中性'}
    
    def _generate_wordcloud(self, comments: List[Comment], movie_id: int) -> str:
        """生成词云图"""
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
            
            # 保存图片
            save_path = os.path.join(self.static_dir, f'wordcloud_{movie_id}.png')
            wordcloud.to_file(save_path)
            
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成词云图失败: {str(e)}")
            raise
    
    def _generate_sentiment_chart(self, positive: int, neutral: int, negative: int, movie_id: int) -> str:
        """生成情感分析图表"""
        try:
            plt.figure(figsize=(8, 8))
            plt.pie(
                [positive, neutral, negative],
                labels=['正面', '中性', '负面'],
                autopct='%1.1f%%',
                colors=['#28a745', '#6c757d', '#dc3545']
            )
            plt.title('评论情感分布')
            
            # 保存图片
            save_path = os.path.join(self.static_dir, f'sentiment_{movie_id}.png')
            plt.savefig(save_path)
            plt.close()
            
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成情感分析图表失败: {str(e)}")
            raise 
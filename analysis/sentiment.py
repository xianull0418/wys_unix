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
import re

class SentimentAnalyzer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # 确保存储目录存在
        self.static_dir = 'web/static/analysis'
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)
        
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False     # 用来正常显示负号
    
    def analyze_movie(self, movie_id: str) -> Dict[str, Any]:
        """分析电影评论"""
        try:
            comments = self.db_manager.get_movie_comments(movie_id)
            if not comments:
                raise ValueError("没有找到任何评论数据")
            
            movie_dir = os.path.join(self.static_dir, str(movie_id))
            os.makedirs(movie_dir, exist_ok=True)
            
            # 评论文本和时间列表
            comment_texts = []
            comment_dates = []
            
            # 情感分析统计
            sentiment_results = {
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'total': 0,
                'avg_score': 0.0
            }
            
            # 评论长度统计
            length_stats = {
                'short': 0,   # 小于50字
                'medium': 0,  # 50-200字
                'long': 0     # 超过200字
            }
            
            # 评论时间分布
            time_distribution = {str(i): 0 for i in range(24)}  # 24小时分布
            
            # 热门词统计
            word_freq = {}
            
            for comment in comments:
                if comment.comment_text:
                    text = comment.comment_text.strip()
                    comment_texts.append(text)
                    
                    # 统计评论长度
                    text_length = len(text)
                    if text_length < 50:
                        length_stats['short'] += 1
                    elif text_length < 200:
                        length_stats['medium'] += 1
                    else:
                        length_stats['long'] += 1
                    
                    # 统计发布时间
                    if comment.date:
                        comment_dates.append(comment.date)
                        hour = comment.date.hour
                        time_distribution[str(hour)] += 1
                    
                    # 情感分析
                    analysis = self._analyze_comment(text)
                    sentiment = analysis['sentiment']
                    score = analysis['score']
                    
                    sentiment_results['total'] += 1
                    sentiment_results['avg_score'] += score
                    
                    if sentiment == '正面':
                        sentiment_results['positive'] += 1
                    elif sentiment == '负面':
                        sentiment_results['negative'] += 1
                    else:
                        sentiment_results['neutral'] += 1
                    
                    # 分词统计
                    words = jieba.cut(text)
                    for word in words:
                        if len(word) > 1:  # 排除单字词
                            word_freq[word] = word_freq.get(word, 0) + 1
            
            if not comment_texts:
                raise ValueError("没有有效的评论文本")
            
            # 计算平均情感得分
            sentiment_results['avg_score'] /= sentiment_results['total']
            
            # 获取热门词Top10
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 生成各种可视化
            self._generate_wordcloud(comment_texts, os.path.join(movie_dir, 'wordcloud.png'))
            self._generate_sentiment_chart(sentiment_results, os.path.join(movie_dir, 'sentiment.png'))
            self._generate_time_distribution(time_distribution, os.path.join(movie_dir, 'time_dist.png'))
            self._generate_length_distribution(length_stats, os.path.join(movie_dir, 'length_dist.png'))
            
            result = {
                'wordcloud_path': f'/static/analysis/{movie_id}/wordcloud.png',
                'sentiment_chart_path': f'/static/analysis/{movie_id}/sentiment.png',
                'time_dist_path': f'/static/analysis/{movie_id}/time_dist.png',
                'length_dist_path': f'/static/analysis/{movie_id}/length_dist.png',
                'sentiment_stats': sentiment_results,
                'length_stats': length_stats,
                'top_words': top_words,
                'total_comments': sentiment_results['total'],
                'avg_sentiment_score': round(sentiment_results['avg_score'], 2)
            }
            
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
    
    def _generate_wordcloud(self, texts: List[str], save_path: str) -> None:
        """生成词云图"""
        try:
            # 合并所有评论文本
            text = ' '.join(texts)
            
            # 停用词列表
            stop_words = set([
                '的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
                '之', '在', '也', '这', '那', '有', '我', '你', '他', '她',
                '它', '们', '个', '上', '下', '不', '没', '很', '到', '去',
                '又', '这个', '那个', '这样', '那样', '什么', '为什么', '怎么',
                '电影', '片子', '剧情', '感觉', '觉得', '认为', '还是', '比较',
                '一个', '一部', '这部', '这种', '那种', '一样', '这么', '那么',
                '挺', '真的', '确实', '其实', '可能', '应该', '一直', '一定',
                '但是', '因为', '所以', '如果', '虽然', '就是', '只是', '但',
                '啊', '吧', '啦', '呢', '呀', '了', '哦', '哈', '嗯', '噢',
                '的话', '来说', '而且', '只有', '由于', '一些', '一下', '一点',
                '看', '说', '讲', '写', '想', '做', '看到', '听到', '说到'
            ])
            
            # 分词并过滤
            words = []
            for word in jieba.cut(text):
                if all([
                    len(word.strip()) > 1,  # 过滤单字
                    word.strip() not in stop_words,  # 过滤停用词
                    not word.isdigit(),  # 过滤纯数字
                    not bool(re.search(r'^[a-zA-Z0-9_]+$', word.strip()))  # 过滤纯英文和数字组合
                ]):
                    words.append(word.strip())
            
            if not words:
                self.logger.warning("过滤后没有剩余词语，使用原始分词结果")
                # 如果过滤太严格，退回到简单的分词结果
                words = [word for word in jieba.cut(text) if len(word.strip()) > 1]
            
            if not words:
                raise ValueError("无法提取有效词语，可能评论内容过短或无效")
            
            word_space_split = ' '.join(words)
            
            # 生成词云
            wordcloud = WordCloud(
                font_path='simhei.ttf',
                width=800,
                height=400,
                background_color='white',
                max_words=100,  # 最多显示100个词
                min_font_size=10,
                max_font_size=80,
                random_state=42,  # 固定随机状态，使每次生成的词云位置相对固定
                collocations=False  # 避免词语重复
            ).generate(word_space_split)
            
            # 绘制词云图
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('评论关键词云图')
            
            # 保存图片
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            plt.close()
            
        except Exception as e:
            self.logger.error(f"生成词云图失败: {str(e)}")
            raise
    
    def _generate_sentiment_chart(self, sentiment_results: Dict[str, Any], save_path: str) -> None:
        """生成情感分析图表"""
        try:
            plt.figure(figsize=(8, 8))
            plt.pie(
                [sentiment_results['positive'], sentiment_results['neutral'], sentiment_results['negative']],
                labels=['正面', '中性', '负面'],
                autopct='%1.1f%%',
                colors=['#28a745', '#6c757d', '#dc3545']
            )
            plt.title('评论情感分布')
            
            # 保存图片
            plt.savefig(save_path)
            plt.close()
            
        except Exception as e:
            self.logger.error(f"生成情感分析图表失败: {str(e)}")
            raise
    
    def _generate_time_distribution(self, time_dist: Dict[str, int], save_path: str) -> None:
        """生成评论时间分布图"""
        plt.figure(figsize=(12, 6))
        hours = range(24)
        counts = [time_dist[str(h)] for h in hours]
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 绘制柱状图
        bars = plt.bar(hours, counts, color='#007722', alpha=0.8)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # 只在有数据的柱子上显示数字
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')
        
        # 设置x轴标签
        plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
        
        plt.title('评论发布时间分布（24小时制）')
        plt.xlabel('发布时间')
        plt.ylabel('评论数量')
        plt.grid(True, alpha=0.3)
        
        # 调整布局，确保标签不被切掉
        plt.tight_layout()
        
        plt.savefig(save_path)
        plt.close()
    
    def _generate_length_distribution(self, length_stats: Dict[str, int], save_path: str) -> None:
        """生成评论长���分布图"""
        plt.figure(figsize=(8, 6))
        categories = ['短评论\n(<50字)', '中等长度\n(50-200字)', '长评论\n(>200字)']
        values = [length_stats['short'], length_stats['medium'], length_stats['long']]
        
        plt.bar(categories, values, color=['#91cc75', '#fac858', '#ee6666'])
        plt.title('评论长度分布')
        plt.ylabel('评论数量')
        
        plt.savefig(save_path)
        plt.close() 
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import json

from .models import Base, Movie, Comment, ProxyPool, AnalysisResult
from config.config import Config

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # 创建MySQL数据库连接
        self.engine = create_engine(
            f'mysql+pymysql://{self.config.MYSQL_USER}:{self.config.MYSQL_PASSWORD}'
            f'@{self.config.MYSQL_HOST}:{self.config.MYSQL_PORT}/{self.config.MYSQL_DATABASE}'
            '?charset=utf8mb4',
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600
        )
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 创建表
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("数据库表创建成功")
        except SQLAlchemyError as e:
            self.logger.error(f"创建数据库表失败: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def save_movies(self, movies: List[Dict[str, Any]]) -> List[Movie]:
        """
        保存电影数据
        :param movies: 电影数据列表
        :return: 保存的Movie对象列表
        """
        session = self.get_session()
        saved_movies = []
        
        try:
            for movie_data in movies:
                # 检查电影是否已存在
                existing_movie = session.query(Movie)\
                    .filter(Movie.name == movie_data['name'])\
                    .first()
                
                if existing_movie:
                    # 更新现有电影信息
                    for key, value in movie_data.items():
                        setattr(existing_movie, key, value)
                    existing_movie.updated_at = datetime.now()
                    saved_movies.append(existing_movie)
                else:
                    # 创建新电影记录
                    new_movie = Movie(**movie_data)
                    session.add(new_movie)
                    saved_movies.append(new_movie)
            
            session.commit()
            self.logger.info(f"成功保存{len(saved_movies)}部电影信息")
            return saved_movies
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"保存电影数据失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_comments(self, comments: List[Dict[str, Any]], movie_id: int) -> List[Comment]:
        """
        保存评论数据
        :param comments: 评论数据列表
        :param movie_id: 电影ID
        :return: 保存的Comment对象列表
        """
        session = self.get_session()
        saved_comments = []
        
        try:
            for comment_data in comments:
                comment_data['movie_id'] = movie_id
                # 检查评论是否已存在
                existing_comment = session.query(Comment)\
                    .filter(
                        Comment.movie_id == movie_id,
                        Comment.user == comment_data['user'],
                        Comment.date == comment_data['date']
                    ).first()
                
                if not existing_comment:
                    # 创建新评论记录
                    new_comment = Comment(**comment_data)
                    session.add(new_comment)
                    saved_comments.append(new_comment)
            
            session.commit()
            self.logger.info(f"成功保存{len(saved_comments)}条评论")
            return saved_comments
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"保存评论数据失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        """获取指定ID的电影信息"""
        session = self.get_session()
        try:
            return session.query(Movie).filter(Movie.id == movie_id).first()
        finally:
            session.close()
    
    def get_movie_comments(self, movie_id: int) -> List[Comment]:
        """获取指定电影的所有评论"""
        session = self.get_session()
        try:
            return session.query(Comment)\
                .filter(Comment.movie_id == movie_id)\
                .order_by(Comment.date.desc())\
                .all()
        finally:
            session.close()
    
    def update_comment_sentiment(self, comment_id: int, sentiment: str):
        """更新评论的情感分析结果"""
        session = self.get_session()
        try:
            comment = session.query(Comment).filter(Comment.id == comment_id).first()
            if comment:
                comment.sentiment = sentiment
                session.commit()
                self.logger.info(f"成功更新评论{comment_id}的情感分析结果")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"更新评论情感分析结果失败: {str(e)}")
        finally:
            session.close()
    
    def get_all_movies(self) -> List[Dict[str, Any]]:
        """获取所有电影信息"""
        session = self.get_session()
        try:
            movies = session.query(Movie).all()
            # 转换为字典列表，包含所有需要的字段
            return [{
                'id': movie.id,
                'douban_id': movie.douban_id,
                'name': movie.name,
                'rating': movie.rating,
                'director': movie.director,
                'img': movie.img_url,  # 注意这里用 img 而不是 img_url
                'year': movie.year,
                'sub_title': movie.sub_title,
                'genre': movie.genre,  # 添加 genre 字段
                'analyzed': movie.analyzed
            } for movie in movies]
        except Exception as e:
            self.logger.error(f"获取电影列表失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_movies_by_genre(self, genre: str) -> List[Movie]:
        """获取指定类型的电影"""
        session = self.get_session()
        try:
            return session.query(Movie)\
                .filter(Movie.genre.like(f'%{genre}%'))\
                .all()
        finally:
            session.close()
    
    def get_movies_by_rating_range(self, min_rating: float, max_rating: float) -> List[Movie]:
        """获取指定评分范围的电影"""
        session = self.get_session()
        try:
            return session.query(Movie)\
                .filter(Movie.rating.between(min_rating, max_rating))\
                .all()
        finally:
            session.close()
    
    def check_movie_exists(self, douban_id: str) -> bool:
        """检查电影是否已存在"""
        session = self.get_session()
        try:
            exists = session.query(Movie).filter(Movie.douban_id == douban_id).first() is not None
            return exists
        finally:
            session.close()
    
    def save_movie(self, movie_data: Dict[str, Any]) -> Movie:
        """保存电影信息"""
        session = self.get_session()
        try:
            # 检查电影是否已存在
            existing_movie = session.query(Movie).filter(Movie.douban_id == movie_data['douban_id']).first()
            
            if existing_movie:
                # 更新现有电影信息
                for key, value in movie_data.items():
                    if hasattr(existing_movie, key):
                        setattr(existing_movie, key, value)
                movie = existing_movie
            else:
                # 创建新电影
                movie = Movie(**movie_data)
                session.add(movie)
            
            # 先提交以获取movie.id
            session.commit()
            
            # 检查是否有分析结果
            has_analysis = session.query(AnalysisResult).filter(
                AnalysisResult.movie_id == movie.id
            ).first() is not None
            
            # 更新分析状态并再次提交
            movie.analyzed = has_analysis
            session.commit()
            
            # 创建一个新的字典来返回电影信息
            movie_info = {
                'id': movie.id,
                'douban_id': movie.douban_id,
                'name': movie.name,
                'rating': movie.rating,
                'director': movie.director,
                'img_url': movie.img_url,
                'year': movie.year,
                'sub_title': movie.sub_title,
                'genre': movie.genre,
                'analyzed': movie.analyzed
            }
            
            return movie_info
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"保存电影失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_analysis_result(self, movie_id: str, result: Dict[str, Any]) -> AnalysisResult:
        """保存分析结果"""
        session = self.get_session()
        try:
            # 获取电影
            movie = session.query(Movie).filter(Movie.douban_id == movie_id).first()
            if not movie:
                raise ValueError(f"未找到电影: {movie_id}")
            
            # 检查���否已有分析结果
            existing_result = session.query(AnalysisResult).filter(
                AnalysisResult.movie_id == movie.id
            ).first()
            
            if existing_result:
                # 更新现有结果
                existing_result.wordcloud_path = result['wordcloud_path']
                existing_result.sentiment_chart_path = result['sentiment_chart_path']
                existing_result.time_dist_path = result['time_dist_path']
                existing_result.length_dist_path = result['length_dist_path']
                
                # 更新情感分析统计
                existing_result.positive_count = result['sentiment_stats']['positive']
                existing_result.neutral_count = result['sentiment_stats']['neutral']
                existing_result.negative_count = result['sentiment_stats']['negative']
                existing_result.total_comments = result['total_comments']
                existing_result.avg_sentiment_score = result['avg_sentiment_score']
                
                # 更新评论长度统计
                existing_result.short_comments = result['length_stats']['short']
                existing_result.medium_comments = result['length_stats']['medium']
                existing_result.long_comments = result['length_stats']['long']
                
                # 更新热门词统计
                existing_result.top_words = json.dumps(result['top_words'], ensure_ascii=False)
                
                analysis_result = existing_result
            else:
                # 创建新结果
                analysis_result = AnalysisResult(
                    movie_id=movie.id,
                    wordcloud_path=result['wordcloud_path'],
                    sentiment_chart_path=result['sentiment_chart_path'],
                    time_dist_path=result['time_dist_path'],
                    length_dist_path=result['length_dist_path'],
                    positive_count=result['sentiment_stats']['positive'],
                    neutral_count=result['sentiment_stats']['neutral'],
                    negative_count=result['sentiment_stats']['negative'],
                    total_comments=result['total_comments'],
                    avg_sentiment_score=result['avg_sentiment_score'],
                    short_comments=result['length_stats']['short'],
                    medium_comments=result['length_stats']['medium'],
                    long_comments=result['length_stats']['long'],
                    top_words=json.dumps(result['top_words'], ensure_ascii=False)
                )
                session.add(analysis_result)
            
            # 更新电影分析���态
            movie.analyzed = True
            
            session.commit()
            return analysis_result
        except Exception as e:
            session.rollback()
            self.logger.error(f"保存分析结果失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_analysis_result(self, douban_id: str) -> Optional[Dict[str, Any]]:
        """获取电影分析结果"""
        session = self.get_session()
        try:
            movie = session.query(Movie).filter(Movie.douban_id == douban_id).first()
            if not movie:
                self.logger.error(f"未找到电影: {douban_id}")
                return None
            
            result = session.query(AnalysisResult).filter(AnalysisResult.movie_id == movie.id).first()
            if not result:
                self.logger.error(f"未找到电影 {douban_id} 的分析结果")
                return None
            
            return {
                'wordcloud_path': result.wordcloud_path,
                'sentiment_chart_path': result.sentiment_chart_path,
                'time_dist_path': result.time_dist_path,
                'length_dist_path': result.length_dist_path,
                'sentiment_stats': {
                    'positive': result.positive_count,
                    'neutral': result.neutral_count,
                    'negative': result.negative_count,
                    'total': result.total_comments,
                    'avg_score': result.avg_sentiment_score
                },
                'length_stats': {
                    'short': result.short_comments,
                    'medium': result.medium_comments,
                    'long': result.long_comments
                },
                'top_words': json.loads(result.top_words) if result.top_words else [],
                'total_comments': result.total_comments,
                'avg_sentiment_score': result.avg_sentiment_score
            }
        except Exception as e:
            self.logger.error(f"获取分析结果失败: {str(e)}")
            return None
        finally:
            session.close() 
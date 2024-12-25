from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from .models import Base, Movie, Comment, ProxyPool, AnalysisResult
from config.config import Config

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # 创建MySQL数据库连接
        self.engine = create_engine(
            f'mysql+pymysql://{self.config.MYSQL_USER}:{self.config.MYSQL_PASSWORD}'
            f'@{self.config.MYSQL_HOST}:{self.config.MYSQL_PORT}/{self.config.MYSQL_DATABASE}',
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
                'name': movie.name,
                'rating': movie.rating,
                'director': movie.director,
                'img': movie.img_url,  # 注意这里用 img 而不是 img_url
                'year': movie.year,
                'sub_title': movie.sub_title,
                'analyzed': movie.analyzed,
                'douban_id': movie.douban_id
            } for movie in movies]
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
        """保存单部电影"""
        session = self.get_session()
        try:
            # 检查电影是否已存在
            existing_movie = session.query(Movie).filter(Movie.douban_id == movie_data['douban_id']).first()
            
            if existing_movie:
                session.refresh(existing_movie)  # 刷新现有对象
                return existing_movie
            
            # 创建新电影记录
            movie = Movie(
                douban_id=movie_data['douban_id'],
                name=movie_data['name'],
                rating=movie_data.get('rating'),
                director=movie_data.get('director', '未知'),
                actors=movie_data.get('actors', ''),
                genre=movie_data.get('genre', ''),
                release_date=movie_data.get('release_date'),
                img_url=movie_data.get('img_url'),  # 保存图片URL
                year=movie_data.get('year'),        # 保存年份
                sub_title=movie_data.get('sub_title')  # 保存副标题
            )
            session.add(movie)
            session.commit()
            session.refresh(movie)  # 刷新新对象
            return movie
        except Exception as e:
            session.rollback()
            self.logger.error(f"保存电影失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_analysis_result(self, movie_id: int, result: Dict[str, Any]) -> AnalysisResult:
        """保存分析结果"""
        session = self.get_session()
        try:
            # 检查是否已有分析结果
            existing_result = session.query(AnalysisResult).filter(AnalysisResult.movie_id == movie_id).first()
            
            if existing_result:
                # 更新现有结果
                for key, value in result.items():
                    setattr(existing_result, key, value)
                analysis_result = existing_result
            else:
                # 创建新结果
                result['movie_id'] = movie_id
                analysis_result = AnalysisResult(**result)
                session.add(analysis_result)
            
            # 更新电影分析状态
            movie = session.query(Movie).get(movie_id)
            if movie:
                movie.analyzed = True
            
            session.commit()
            return analysis_result
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close() 
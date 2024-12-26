from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    douban_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    rating = Column(Float)
    director = Column(String(100))
    actors = Column(Text)
    genre = Column(String(100))
    release_date = Column(Date)
    img_url = Column(String(255))
    year = Column(String(4))
    sub_title = Column(String(200))
    analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    comments = relationship('Comment', back_populates='movie')
    analysis_result = relationship('AnalysisResult', back_populates='movie', uselist=False)

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'))
    user = Column(String(100, collation='utf8mb4_unicode_ci'))
    comment_text = Column(Text(collation='utf8mb4_unicode_ci'))
    sentiment = Column(String(20))
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    movie = relationship('Movie', back_populates='comments')

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete='CASCADE'))
    wordcloud_path = Column(String(255))
    sentiment_chart_path = Column(String(255))
    time_dist_path = Column(String(255))
    length_dist_path = Column(String(255))
    
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    avg_sentiment_score = Column(Float)
    
    short_comments = Column(Integer, default=0)
    medium_comments = Column(Integer, default=0)
    long_comments = Column(Integer, default=0)
    
    top_words = Column(Text)
    
    created_at = Column(DateTime, default=datetime.now)
    
    movie = relationship('Movie', back_populates='analysis_result')

class ProxyPool(Base):
    __tablename__ = 'proxy_pool'
    
    id = Column(Integer, primary_key=True)
    proxy = Column(String(100), unique=True)
    protocol = Column(String(10))
    anonymity = Column(String(20))
    last_checked = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now) 
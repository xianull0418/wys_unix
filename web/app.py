from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
from database.db_manager import DatabaseManager
from crawler.movie_crawler import MovieCrawler
from analysis.sentiment import SentimentAnalyzer
import os

def create_app():
    app = Flask(__name__)
    CORS(app)  # 启用跨域支持
    
    # 配置静态文件目录
    app.static_folder = 'static'
    
    # 确保静态文件目录存在
    os.makedirs(os.path.join(app.root_path, 'static', 'images'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'analysis'), exist_ok=True)
    
    # 初始化数据库管理器
    db_manager = DatabaseManager()
    
    # 初始化爬虫和分析器，传入db_manager
    movie_crawler = MovieCrawler(db_manager)
    analyzer = SentimentAnalyzer(db_manager)
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    @app.route('/api/search')
    def search_movies():
        """搜索电影"""
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'movies': []})
            
        try:
            # 从豆瓣搜索电影
            movies = movie_crawler.search_movies(keyword)
            return jsonify({'movies': movies})
        except Exception as e:
            logger.error(f"搜索电影失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/movies')
    def get_movies():
        """获取已添加的电影列表"""
        try:
            movies = db_manager.get_all_movies()
            return jsonify({
                'movies': movies  # movies 已经是字典列表了，不需要再次转换
            })
        except Exception as e:
            logger.error(f"获取电影列表失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/movies/add', methods=['POST'])
    def add_movie():
        """添加电影到数据库"""
        try:
            data = request.get_json()
            douban_id = data.get('douban_id')
            if not douban_id:
                return jsonify({'error': '缺少douban_id参数'}), 400
            
            # 爬取电影详情信息
            movie_data = movie_crawler.get_movie_detail(douban_id)
            # 保存到数据库
            movie = db_manager.save_movie(movie_data)
            
            return jsonify({
                'message': '添加成功',
                'movie_id': movie.id
            })
        except Exception as e:
            logger.error(f"添加电影失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/movies/<string:douban_id>/analyze', methods=['POST'])
    def analyze_movie(douban_id):
        """分析电影评论"""
        try:
            # 获取评论并分析
            comments = movie_crawler.get_movie_comments(douban_id)
            db_manager.save_comments(comments, douban_id)
            analysis_result = analyzer.analyze_movie(douban_id)
            
            return jsonify(analysis_result)
        except Exception as e:
            logger.error(f"分析电影失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return app 
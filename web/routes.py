from flask import Blueprint, jsonify, request
from database.db_manager import DatabaseManager
from crawler.movie_crawler import MovieCrawler
from analysis.sentiment import SentimentAnalyzer

api = Blueprint('api', __name__)
db_manager = DatabaseManager()
movie_crawler = MovieCrawler()
analyzer = SentimentAnalyzer(db_manager)

@api.route('/api/search')
def search_movies():
    """搜索电影"""
    keyword = request.args.get('keyword', '')
    try:
        # 从豆瓣搜索电影
        movies = movie_crawler.search_movies(keyword)
        return jsonify({
            'movies': [{
                'douban_id': movie['douban_id'],
                'name': movie['name'],
                'rating': movie['rating'],
                'director': movie['director'],
                'is_added': db_manager.check_movie_exists(movie['douban_id'])
            } for movie in movies]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/movies/add', methods=['POST'])
def add_movie():
    """添加电影到数据库"""
    try:
        data = request.get_json()
        douban_id = data.get('douban_id')
        if not douban_id:
            return jsonify({'error': '缺少douban_id参数'}), 400
            
        # 爬取电影详细信息
        movie_data = movie_crawler.get_movie_detail(douban_id)
        # 保存到数据库
        movie = db_manager.save_movie(movie_data)
        
        return jsonify({
            'message': '添加成功',
            'movie_id': movie.id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/movies/analyze/<int:movie_id>', methods=['POST'])
def analyze_movie(movie_id):
    """分析电影评论"""
    try:
        # 爬取评论
        comments = movie_crawler.get_movie_comments(movie_id)
        # 保存评论
        db_manager.save_comments(comments, movie_id)
        # 分析评论
        analysis_result = analyzer.analyze_movie(movie_id)
        
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
# 豆瓣电影评论分析系统

## 项目简介
这是一个基于 Python 的豆瓣电影评论分析系统，可以爬取电影信息和评论，并进行情感分析和数据可视化。

## 技术栈
- 后端：Flask + SQLAlchemy
- 前端：Bootstrap + JavaScript
- 数据库：MySQL
- 爬虫：requests + BeautifulSoup4 + Selenium
- 数据分析：SnowNLP + jieba + wordcloud + matplotlib

## 项目结构
```txt
douban_movie/
├── config/ # 配置文件目录
│ └── config.py # 系统配置（数据库连接、爬虫参数等）
├── crawler/ # 爬虫模块
│ ├── init.py # 爬虫基类，定义通用爬虫方法
│ ├── movie_crawler.py # 电影信息爬虫（支持API和Selenium两种模式）
│ ├── comment_crawler.py # 评论爬虫（多线程爬取评论）
│ └── proxy_manager.py # 代理IP管理（维护代理池）
├── database/ # 数据库模块
│ ├── init.py # 数据库模块初始化
│ ├── models.py # 数据库模型（Movie、Comment、AnalysisResult等）
│ └── db_manager.py # 数据库操作管理（CRUD操作封装）
├── analysis/ # 数据分析模块
│ ├── init.py # 分析模块初始化
│ ├── data_cleaner.py # 数据清洗（处理文本、去重等）
│ ├── sentiment.py # 情感分析（使用SnowNLP）和可视化
│ └── visualizer.py # 数据可视化（matplotlib绘图）
├── web/ # Web应用模块
│ ├── init.py # Web模块初始化
│ ├── static/ # 静态文件（CSS、JS、分析结果图片）
│ ├── templates/ # HTML模板
│ ├── routes.py # API路由定义
│ └── app.py # Flask应用主文件
├── utils/ # 工具函数模块
│ ├── init.py # 工具模块初始化
│ └── helpers.py # 辅助函数
├── requirements.txt # 项目依赖
└── main.py # 主程序入口
```


## 核心功能实现

### 1. 电影爬虫模块 (crawler/)
- `BaseCrawler`: 基础爬虫类
  - 提供请求头管理
  - 处理请求限制
  - 统一的页面解析接口
- `MovieCrawler`: 电影信息爬虫
  - 支持豆瓣API搜索
  - 自动切换Selenium模式应对反爬
  - 详细电影信息获取
- `CommentCrawler`: 评论爬虫
  - 多线程并发爬取
  - 评论数据预处理
  - 时间信息标准化

### 2. 数据库模块 (database/)
- `models.py`: 数据模型定义
  - Movie: 电影基本信息
  - Comment: 用户评论
  - AnalysisResult: 分析结果存储
- `db_manager.py`: 数据库操作
  - 连接池管理
  - CRUD操作封装
  - 事务处理

### 3. 分析模块 (analysis/)
- `sentiment.py`: 情感分析和可视化
  - SnowNLP情感打分
  - 词云图生成
  - 评论时间分布分析
  - 评论长度统计
- `visualizer.py`: 数据可视化
  - matplotlib图表生成
  - 评分分布分析
  - 类型统计分析

### 4. Web应用模块 (web/)
- `app.py`: Flask应用
  - RESTful API实现
  - 静态文件管理
  - 错误处理
- `static/js/main.js`: 前端交互
  - 异步数据加载
  - 动态UI更新
  - 分析结果展示

## 主要功能
1. 电影搜索和添加
   - 支持模糊搜索
   - 自动获取详情
   - 防重复添加

2. 评论分析
   - 情感倾向分析
   - 词频统计
   - 时间分布分析
   - 评论长度分析

3. 可视化展示
   - 词云图
   - 情感分布饼图
   - 时间分布柱状图
   - 评论长度统计图


## 注意事项
1. 数据库配置
   - 确保MySQL服务已启动
   - 正确配置数据库连接信息
   - 使用UTF8MB4字符集支持emoji

2. 环境要求
   - Python 3.7+
   - Chrome浏览器（用于Selenium）
   - 中文字体支持（simhei.ttf）

3. 反爬处理
   - 注意请求频率限制
   - 适时切换代理IP
   - 必要时启用Selenium模式

## 开发建议
1. 代码规范
   - 遵循PEP 8规范
   - 添加适当的注释
   - 使用类型提示

2. 错误处理
   - 完善的异常处理
   - 详细的日志记录
   - 友好的错误提示

3. 性能优化
   - 使用数据库连接池
   - 合理的并发控制
   - 缓存机制应用

## API接口说明

### 1. 电影搜索
GET /api/search?keyword={keyword}
- 功能：搜索电影
- 参数：keyword - 搜索关键词
- 返回：电影列表

### 2. 添加电影
POST /api/movies/add
- 功能：添加电影到数据库
- 参数：douban_id - 豆瓣电影ID
- 返回：添加结果

### 3. 分析电影
POST /api/movies/{douban_id}/analyze
- 功能：分析电影评论
- 参数：douban_id - 豆瓣电影ID
- 返回：分析结果

### 4. 获取分析结果
GET /api/movies/{douban_id}/analysis
- 功能：获取分析结果
- 参数：douban_id - 豆瓣电影ID
- 返回：分析结果数据

// 搜索电影
async function searchMovies() {
    const keyword = document.getElementById('searchInput').value;
    if (!keyword) {
        showToast('请输入搜索关键词', 'error');
        return;
    }
    
    // 显示加载状态
    const searchBtn = document.getElementById('searchBtn');
    const originalText = searchBtn.innerHTML;
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 搜索中...';
    
    // 显示加载动画
    const container = document.getElementById('searchResults');
    container.innerHTML = `
        <div class="search-loading">
            <div class="spinner"></div>
            <p>正在搜索中...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`);
        if (!response.ok) {
            throw new Error('搜索请求失败');
        }
        const data = await response.json();
        
        // 显示搜索结果
        displaySearchResults(data.movies);
        
        // 显示搜索结果数量
        if (data.movies.length > 0) {
            showToast(`找到 ${data.movies.length} 部相关电影`, 'success');
        } else {
            showToast('未找到相关电影', 'info');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        showToast('搜索失败，请稍后重试', 'error');
        container.innerHTML = `
            <div class="search-error">
                <i class="fas fa-exclamation-circle"></i>
                <p>搜索失败，请稍后重试</p>
            </div>
        `;
    } finally {
        // 恢复按钮状态
        searchBtn.disabled = false;
        searchBtn.innerHTML = originalText;
    }
}

// 绑定搜索事件
document.addEventListener('DOMContentLoaded', function() {
    // 绑定搜索按钮点击事件
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchMovies);
    }
    
    // 绑定搜索框回车事件
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchMovies();
            }
        });
    }
});

// 显示搜索结果
function displaySearchResults(movies) {
    const container = document.getElementById('searchResults');
    container.innerHTML = '';
    
    if (movies.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <h5 class="text-muted">未找到相关电影</h5>
            </div>
        `;
        return;
    }
    
    movies.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <div class="card-img-container">
                <img src="${movie.img || ''}" 
                     class="card-img-top" 
                     alt="${movie.name}"
                     referrerpolicy="no-referrer"
                     onerror="this.onerror=null; this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22280%22><rect width=%22200%22 height=%22280%22 fill=%22%23f8f9fa%22/><text x=%22100%22 y=%22140%22 fill=%22%23dee2e6%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22 font-family=%22Arial%22 font-size=%2216%22>暂无图片</text></svg>';">
            </div>
            <div class="card-body">
                <h5 class="card-title" title="${movie.name}">${movie.name}</h5>
                <div class="movie-info d-flex justify-content-between align-items-center">
                    <span class="movie-rating">
                        ${typeof movie.rating === 'number' ? 
                          `<i class="fas fa-star"></i> ${movie.rating.toFixed(1)}` : 
                          movie.rating}
                    </span>
                    <span class="movie-year">${movie.year || '年份未知'}</span>
                </div>
                <p class="card-text">
                    导演：${movie.director || '未知'}<br>
                    ${movie.sub_title || ''}
                </p>
                ${movie.is_added ? 
                    '<button class="btn btn-add btn-added" disabled><i class="fas fa-check"></i> 已添加</button>' :
                    `<button class="btn btn-add" onclick="addMovie('${movie.douban_id}')">
                        <i class="fas fa-plus"></i> 添加到收藏
                     </button>`
                }
            </div>
        `;
        container.appendChild(card);
    });
}

// 添加电影
async function addMovie(doubanId) {
    const button = event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 添加中...';
    
    try {
        const response = await fetch('/api/movies/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ douban_id: doubanId })
        });
        
        if (!response.ok) {
            throw new Error('添加失败');
        }
        
        const data = await response.json();
        
        // 更新按钮状态
        button.className = 'btn btn-add btn-added';
        button.innerHTML = '<i class="fas fa-check"></i> 已添加';
        
        // 显示成功提示
        showToast('添加成功', 'success');
        
        // 如果在分析页面，刷新电影列表
        if (document.getElementById('analysisPage').style.display !== 'none') {
            loadMoviesList();
        }
        
    } catch (error) {
        console.error('添加电影失败:', error);
        button.disabled = false;
        button.innerHTML = originalText;
        showToast('添加失败，请稍后重试', 'error');
    }
}

// 显示提示信息
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    
    // 添加显示类
    setTimeout(() => toast.classList.add('show'), 10);
    
    // 3秒后移除
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 分析电影
async function analyzeMovie(doubanId) {
    try {
        const button = event.target;
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分析中...';
        
        const response = await fetch(`/api/movies/${doubanId}/analyze`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('分析失败');
        }
        
        const data = await response.json();
        
        // 更新按钮状态
        button.className = 'btn btn-analyze btn-analyzed';
        button.innerHTML = '<i class="fas fa-check"></i> 已分析';
        button.disabled = true;
        
        // 显示成功提示
        showToast('分析完成', 'success');
        
    } catch (error) {
        console.error('分析失败:', error);
        button.disabled = false;
        button.innerHTML = originalText;
        showToast('分析失败，请稍后重试', 'error');
    }
}

// 显示分析结果
function displayAnalysisResults(results) {
    const container = document.getElementById('analysisResults');
    container.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">评论词云</h5>
                        <img src="${results.wordcloud_path}" class="img-fluid">
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">情感分析</h5>
                        <img src="${results.sentiment_chart_path}" class="img-fluid">
                        <div class="mt-3">
                            <p>正面评论：${results.positive_count}</p>
                            <p>中性评论：${results.neutral_count}</p>
                            <p>负面评论：${results.negative_count}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 存储所有电影数据
let allMovies = [];

// 初始化筛选选项
async function initializeFilters(movies) {
    allMovies = movies;
    
    // 获取所有年份
    const years = [...new Set(movies.filter(m => m.year).map(m => m.year))].sort().reverse();
    const yearSelect = document.getElementById('yearFilter');
    yearSelect.innerHTML = '<option value="">全部年份</option>' + 
        years.map(year => `<option value="${year}">${year}</option>`).join('');
    
    // 获取所有类型
    const genres = [...new Set(movies.filter(m => m.genre).map(m => m.genre.split('/')).flat())];
    const genreSelect = document.getElementById('genreFilter');
    genreSelect.innerHTML = '<option value="">全部类型</option>' + 
        genres.map(genre => `<option value="${genre}">${genre}</option>`).join('');
}

// 应用筛选
function applyFilters() {
    const minRating = parseFloat(document.getElementById('minRating').value) || 0;
    const maxRating = parseFloat(document.getElementById('maxRating').value) || 10;
    const genre = document.getElementById('genreFilter').value;
    const year = document.getElementById('yearFilter').value;
    const sortBy = document.getElementById('sortBy').value;
    
    // 筛选电影
    let filteredMovies = allMovies.filter(movie => {
        const ratingMatch = (!movie.rating || (movie.rating >= minRating && movie.rating <= maxRating));
        const genreMatch = !genre || (movie.genre && movie.genre.includes(genre));
        const yearMatch = !year || movie.year === year;
        return ratingMatch && genreMatch && yearMatch;
    });
    
    // 排序
    filteredMovies.sort((a, b) => {
        switch(sortBy) {
            case 'rating':
                return (b.rating || 0) - (a.rating || 0);
            case 'year':
                return (b.year || '') > (a.year || '') ? -1 : 1;
            case 'name':
                return a.name.localeCompare(b.name, 'zh-CN');
            default:
                return 0;
        }
    });
    
    // 显示筛选结果
    displayMoviesList(filteredMovies);
}

// 重置筛选
function resetFilters() {
    document.getElementById('minRating').value = '';
    document.getElementById('maxRating').value = '';
    document.getElementById('genreFilter').value = '';
    document.getElementById('yearFilter').value = '';
    document.getElementById('sortBy').value = 'rating';
    
    displayMoviesList(allMovies);
}

// 修改 loadMoviesList 函数
async function loadMoviesList() {
    try {
        const container = document.getElementById('moviesList');
        container.innerHTML = `
            <div class="search-loading">
                <div class="spinner"></div>
                <p>正在加载电影列表...</p>
            </div>
        `;
        
        const response = await fetch('/api/movies');
        const data = await response.json();
        
        if (data.movies.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-film fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">还没有添加任何电影</h5>
                    <p class="text-muted">去搜索页面添加一些电影吧</p>
                </div>
            `;
            return;
        }
        
        // 初始化筛选选项
        await initializeFilters(data.movies);
        
        // 显示电影列表
        displayMoviesList(data.movies);
    } catch (error) {
        console.error('加载电影列表失败:', error);
        showToast('加载电影列表失败，请稍后重试', 'error');
    }
}

// 显示电影列表
function displayMoviesList(movies) {
    const container = document.getElementById('moviesList');
    container.innerHTML = '';
    
    movies.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <div class="card-img-container">
                <img src="${movie.img || ''}" 
                     class="card-img-top" 
                     alt="${movie.name}"
                     referrerpolicy="no-referrer"
                     onerror="this.onerror=null; this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22280%22><rect width=%22200%22 height=%22280%22 fill=%22%23f8f9fa%22/><text x=%22100%22 y=%22140%22 fill=%22%23dee2e6%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22 font-family=%22Arial%22 font-size=%2216%22>暂无图片</text></svg>';">
            </div>
            <div class="card-body">
                <h5 class="card-title" title="${movie.name}">${movie.name}</h5>
                <div class="movie-info d-flex justify-content-between align-items-center">
                    <span class="movie-rating">
                        ${typeof movie.rating === 'number' ? 
                          `<i class="fas fa-star"></i> ${movie.rating.toFixed(1)}` : 
                          '暂无评分'}
                    </span>
                    <span class="movie-year">${movie.year || '年份未知'}</span>
                </div>
                <p class="card-text">
                    导演：${movie.director || '未知'}<br>
                    ${movie.genre ? `类型：${movie.genre}` : ''}
                </p>
                <button class="btn ${movie.analyzed ? 'btn-analyze btn-analyzed' : 'btn-analyze'}" 
                        onclick="analyzeMovie('${movie.douban_id}')"
                        ${movie.analyzed ? 'disabled' : ''}>
                    <i class="fas ${movie.analyzed ? 'fa-check' : 'fa-chart-bar'}"></i>
                    ${movie.analyzed ? '已分析' : '分析评论'}
                </button>
            </div>
        `;
        container.appendChild(card);
    });
} 
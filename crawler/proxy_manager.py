import requests
import logging
from typing import Optional, List
from datetime import datetime
from database.models import ProxyPool
from sqlalchemy.orm import Session

class ProxyManager:
    def __init__(self, db_session: Session):
        self.session = db_session
        self.logger = logging.getLogger(__name__)
    
    def _validate_proxy(self, proxy: str) -> bool:
        """验证代理是否可用"""
        try:
            test_url = "https://www.douban.com"
            response = requests.get(
                test_url,
                proxies={'http': proxy, 'https': proxy},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_proxy(self) -> Optional[str]:
        """获取一个可用代理"""
        try:
            # 从数据库获取最近检查过的代理
            proxy = self.session.query(ProxyPool)\
                .order_by(ProxyPool.last_checked.desc())\
                .first()
            
            if proxy and self._validate_proxy(proxy.proxy):
                return proxy.proxy
                
            # 如果没有可用代理，则获取新代理
            return self._fetch_new_proxy()
            
        except Exception as e:
            self.logger.error(f"获取代理失败: {str(e)}")
            return None
    
    def _fetch_new_proxy(self) -> Optional[str]:
        """从代理API获取新代理"""
        try:
            if not self.config.PROXY_POOL_URL:
                return None
                
            response = requests.get(self.config.PROXY_POOL_URL)
            if response.status_code == 200:
                proxy = response.text.strip()
                if self._validate_proxy(proxy):
                    # 保存到数据库
                    new_proxy = ProxyPool(
                        proxy=proxy,
                        protocol='http',
                        last_checked=datetime.now()
                    )
                    self.session.add(new_proxy)
                    self.session.commit()
                    return proxy
            return None
            
        except Exception as e:
            self.logger.error(f"获取新代理失败: {str(e)}")
            return None
    
    def remove_proxy(self, proxy: str):
        """移除无效代理"""
        try:
            self.session.query(ProxyPool)\
                .filter(ProxyPool.proxy == proxy)\
                .delete()
            self.session.commit()
        except Exception as e:
            self.logger.error(f"移除代理失败: {str(e)}") 
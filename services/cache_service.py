import os
import hashlib
import json
from datetime import datetime

class CacheService:
    def __init__(self, cache_dir='cache'):
        """初始化缓存服务"""
        self.cache_dir = cache_dir
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
    
    def _generate_cache_key(self, video_urls):
        """生成缓存键（MD5）"""
        if isinstance(video_urls, str):
            video_urls = [video_urls]
        
        # 拼接所有视频URL
        combined_urls = '|'.join(sorted(video_urls))
        
        # 生成MD5哈希
        md5_hash = hashlib.md5(combined_urls.encode('utf-8')).hexdigest()
        return md5_hash
    
    def _get_cache_file_path(self, cache_key):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.md")
    
    def save_analysis_result(self, video_urls, report, metadata=None):
        """保存分析结果到Markdown文件"""
        cache_key = self._generate_cache_key(video_urls)
        cache_file = self._get_cache_file_path(cache_key)
        
        # 准备Markdown内容
        markdown_content = self._format_report_as_markdown(report, video_urls, metadata)
        
        # 保存到文件
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return cache_key
    
    def get_cached_result(self, video_urls):
        """获取缓存的分析结果"""
        cache_key = self._generate_cache_key(video_urls)
        cache_file = self._get_cache_file_path(cache_key)
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            return {
                'cache_key': cache_key,
                'markdown_content': markdown_content,
                'found': True
            }
        
        return {
            'cache_key': cache_key,
            'found': False
        }
    
    def _format_report_as_markdown(self, report, video_urls, metadata=None):
        """将报告格式化为Markdown"""
        if isinstance(video_urls, str):
            video_urls = [video_urls]
        
        markdown_content = f"""# YouTube视频分析报告

## 分析信息
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **视频数量**: {len(video_urls)}
- **分析类型**: {metadata.get('analysis_type', '未知') if metadata else '未知'}

## 视频链接
"""
        
        for i, url in enumerate(video_urls, 1):
            markdown_content += f"{i}. [{url}]({url})\n"
        
        markdown_content += f"\n## 分析报告\n\n{report}\n"
        
        if metadata:
            markdown_content += "\n## 额外信息\n\n"
            if metadata.get('stock_data'):
                markdown_content += "### 股票数据\n\n"
                stock_data = metadata['stock_data']
                if isinstance(stock_data, list):
                    for stock in stock_data:
                        markdown_content += f"- **{stock.get('symbol', 'N/A')}**: {stock.get('name', 'N/A')}\n"
                else:
                    markdown_content += f"- **{stock_data.get('symbol', 'N/A')}**: {stock_data.get('name', 'N/A')}\n"
            
            if metadata.get('extracted_stocks'):
                markdown_content += "\n### 提取的股票信息\n\n"
                for stock in metadata['extracted_stocks']:
                    markdown_content += f"- **{stock.get('symbol', 'N/A')}**: {stock.get('name', 'N/A')}\n"
        
        return markdown_content
    
    def get_markdown_file_path(self, cache_key):
        """获取Markdown文件路径"""
        return self._get_cache_file_path(cache_key)
    
    def cache_exists(self, video_urls):
        """检查缓存是否存在"""
        result = self.get_cached_result(video_urls)
        return result['found']
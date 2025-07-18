import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import os
import base64
import io
from services.stock_service import StockService

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ChartService:
    """图表生成服务"""
    
    def __init__(self):
        self.stock_service = StockService()
        self.chart_dir = 'web/static/charts'
        # 确保图表目录存在
        os.makedirs(self.chart_dir, exist_ok=True)
    
    def generate_stock_chart(self, symbol, days=30):
        """
        生成股票走势图
        
        Args:
            symbol: 股票代码
            days: 天数
            
        Returns:
            dict: 包含图表信息的字典
        """
        try:
            # 获取股票数据
            stock_data = self.stock_service.get_stock_data(symbol, days)
            
            # 创建图表
            chart_filename = self._create_price_chart(stock_data)
            
            return {
                'success': True,
                'symbol': symbol,
                'name': self._get_company_name(symbol),
                'period': f'最近{days}天',
                'current_price': stock_data['latest_price'],
                'price_change': stock_data['pct_change'],
                'chart_url': f'/static/charts/{chart_filename}',
                'chart_filename': chart_filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def generate_stock_chart_by_date_range(self, symbol, start_date, end_date):
        """
        按日期范围生成股票走势图
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            
        Returns:
            dict: 包含图表信息的字典
        """
        try:
            # 获取股票数据
            stock_data = self.stock_service.get_stock_data_by_date_range(symbol, start_date, end_date)
            
            # 创建图表
            chart_filename = self._create_price_chart(stock_data)
            
            return {
                'success': True,
                'symbol': symbol,
                'name': self._get_company_name(symbol),
                'period': f'{start_date} 至 {end_date}',
                'current_price': stock_data['latest_price'],
                'price_change': stock_data['pct_change'],
                'chart_url': f'/static/charts/{chart_filename}',
                'chart_filename': chart_filename,
                'start_date': start_date,
                'end_date': end_date
            }
            
        except Exception as e:
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def _create_price_chart(self, stock_data):
        """创建价格走势图"""
        # 准备数据
        df = pd.DataFrame(stock_data['historical_data'])
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df = df.sort_values('date')
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # 价格图
        ax1.plot(df['date'], df['close'], linewidth=2, color='#1f77b4', label='收盘价')
        ax1.fill_between(df['date'], df['low'], df['high'], alpha=0.3, color='#1f77b4', label='日内波动')
        
        ax1.set_title(f'{stock_data["symbol"]} 股价走势图', fontsize=16, fontweight='bold')
        ax1.set_ylabel('价格 ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 格式化日期轴
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df)//10)))
        
        # 成交量图
        colors = ['red' if close < open_price else 'green' 
                  for close, open_price in zip(df['close'], df['open'])]
        ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7)
        ax2.set_ylabel('成交量', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 格式化日期轴
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df)//10)))
        
        # 调整布局
        plt.tight_layout()
        
        # 添加统计信息
        self._add_stats_text(ax1, stock_data)
        
        # 保存图表
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{stock_data["symbol"]}_{timestamp}.png'
        filepath = os.path.join(self.chart_dir, filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filename
    
    def _add_stats_text(self, ax, stock_data):
        """添加统计信息文本"""
        stats_text = f'''当前价格: ${stock_data["latest_price"]:.2f}
涨跌幅: {stock_data["pct_change"]:+.2f}%
价格趋势: {stock_data["price_trend"]}
波动率: {stock_data["volatility"]}%'''
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    def _get_company_name(self, symbol):
        """获取公司名称（简化版）"""
        # 这里可以添加更复杂的逻辑来获取公司名称
        company_names = {
            'AAPL': 'Apple Inc.',
            'GOOGL': 'Alphabet Inc.',
            'MSFT': 'Microsoft Corporation',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
            'NFLX': 'Netflix Inc.',
            'CRM': 'Salesforce Inc.',
            'ADBE': 'Adobe Inc.'
        }
        return company_names.get(symbol, f'{symbol} Corporation')
    
    def generate_multiple_charts(self, symbols, days=30):
        """批量生成股票图表"""
        results = []
        for symbol in symbols:
            result = self.generate_stock_chart(symbol, days)
            results.append(result)
        return results
    
    def cleanup_old_charts(self, max_age_hours=24):
        """清理旧的图表文件"""
        try:
            current_time = datetime.now()
            for filename in os.listdir(self.chart_dir):
                if filename.endswith('.png'):
                    filepath = os.path.join(self.chart_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                        os.remove(filepath)
                        print(f"已清理旧图表: {filename}")
        except Exception as e:
            print(f"清理图表文件失败: {e}") 
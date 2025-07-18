import tushare as ts
from datetime import datetime, timedelta
from config.settings import Config

class StockService:
    """股票数据服务"""
    
    def __init__(self):
        # 初始化Tushare
        if Config.TUSHARE_TOKEN:
            ts.set_token(Config.TUSHARE_TOKEN)
            self.pro = ts.pro_api()
        else:
            raise Exception("未配置Tushare Token")
    
    def get_stock_data(self, symbol, days=30):
        """
        获取美股历史数据
        
        Args:
            symbol: 股票代码 (如: AAPL)
            days: 获取天数
        """
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        try:
            # 获取美股数据
            df = self.pro.us_daily(
                ts_code=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                raise Exception(f"未找到股票代码 {symbol} 的数据")
            
            # 转换为字典格式
            stock_data = {
                'symbol': symbol,
                'period': f"{days}天",
                'data_points': len(df),
                'latest_price': float(df.iloc[0]['close']),
                'price_change': float(df.iloc[0]['change']) if 'change' in df.columns else 0,
                'pct_change': float(df.iloc[0]['pct_change']),
                'volume': int(df.iloc[0]['vol']),
                'historical_data': self._format_historical_data(df),
                'price_trend': self._analyze_price_trend(df),
                'volatility': self._calculate_volatility(df)
            }
            
            return stock_data
            
        except Exception as e:
            error_msg = str(e)
            if "每天最多访问该接口" in error_msg or "权限" in error_msg:
                raise Exception("Tushare API 达到每日访问限制，请稍后再试")
            else:
                raise Exception(f"获取股票数据失败: {error_msg}")
    
    def _format_historical_data(self, df):
        """格式化历史数据"""
        data = []
        for _, row in df.iterrows():
            data.append({
                'date': row['trade_date'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['vol']),
                'pct_change': float(row['pct_change'])
            })
        return data
    
    def _analyze_price_trend(self, df):
        """分析价格趋势"""
        if len(df) < 2:
            return "数据不足"
        
        latest_price = df.iloc[0]['close']
        week_ago_price = df.iloc[min(7, len(df)-1)]['close']
        
        change_pct = ((latest_price - week_ago_price) / week_ago_price) * 100
        
        if change_pct > 5:
            return "强势上涨"
        elif change_pct > 2:
            return "温和上涨"
        elif change_pct > -2:
            return "横盘整理"
        elif change_pct > -5:
            return "温和下跌"
        else:
            return "大幅下跌"
    
    def _calculate_volatility(self, df):
        """计算波动率"""
        if len(df) < 2:
            return 0
        
        pct_changes = df['pct_change'].tolist()
        # 计算标准差作为波动率指标
        mean_change = sum(pct_changes) / len(pct_changes)
        variance = sum((x - mean_change) ** 2 for x in pct_changes) / len(pct_changes)
        volatility = variance ** 0.5
        
        return round(volatility, 2)
    
    def get_stock_data_by_date_range(self, symbol, start_date, end_date):
        """
        按日期范围获取美股历史数据
        
        Args:
            symbol: 股票代码 (如: AAPL)
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
        """
        try:
            # 转换日期格式为Tushare需要的格式 (YYYYMMDD)
            start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y%m%d')
            end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d')
            
            # 获取美股数据
            df = self.pro.us_daily(
                ts_code=symbol,
                start_date=start_date_formatted,
                end_date=end_date_formatted
            )
            
            if df.empty:
                raise Exception(f"未找到股票代码 {symbol} 在 {start_date} 到 {end_date} 期间的数据")
            
            # 计算天数
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days = (end_dt - start_dt).days
            
            # 转换为字典格式
            stock_data = {
                'symbol': symbol,
                'period': f"{start_date} 至 {end_date}",
                'days': days,
                'data_points': len(df),
                'latest_price': float(df.iloc[0]['close']),
                'price_change': float(df.iloc[0]['change']) if 'change' in df.columns else 0,
                'pct_change': float(df.iloc[0]['pct_change']),
                'volume': int(df.iloc[0]['vol']),
                'historical_data': self._format_historical_data(df),
                'price_trend': self._analyze_price_trend(df),
                'volatility': self._calculate_volatility(df),
                'start_date': start_date,
                'end_date': end_date
            }
            
            return stock_data
            
        except Exception as e:
            error_msg = str(e)
            if "每天最多访问该接口" in error_msg or "权限" in error_msg:
                raise Exception("Tushare API 达到每日访问限制，请稍后再试")
            else:
                raise Exception(f"获取股票数据失败: {error_msg}")

    def get_multiple_stocks(self, symbols, days=30):
        """获取多只股票数据"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_stock_data(symbol, days)
            except Exception as e:
                results[symbol] = {'error': str(e)}
        return results
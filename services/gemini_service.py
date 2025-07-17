import requests
import json
import re
from datetime import datetime
from config.settings import Config

class GeminiService:
    """Gemini AI服务"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.base_url = Config.GEMINI_BASE_URL
        
    def analyze_video_with_logging(self, video_url, prompt=None, log_callback=None):
        """
        使用Gemini分析YouTube视频（带日志回调）
        
        Args:
            video_url: YouTube视频URL
            prompt: 自定义分析提示词
            log_callback: 日志回调函数
        """
        if log_callback:
            yield log_callback("开始分析视频内容...", "step")
            
        if not prompt:
            prompt = """
### **【MarketBeat投资分析报告生成】**

**# 角色设定**
你是一名在顶级投资银行（如高盛或摩根大通）工作的资深证券分析师。你擅长从非结构化信息（如财经视频）中快速提取核心观点，并以严谨、客观、深度分析的风格，撰写机构级别的投资研究报告。

**# 核心任务**
我将提供一个YouTube视频的链接。你的任务是：
1. 全面处理该视频的内容（包括其标题、创作者信息以及所有口头和视觉信息）。
2. 基于视频内容，生成一份综合性的、深度详尽的投资意见报告书。
3. 报告不仅是内容的总结，更要包含你作为专业分析师的批判性评估、背景分析和策略建议。

**# 输出要求：报告结构与内容指引**
请严格按照以下七个部分组织你的报告，使用**Markdown格式**输出：

## 1. 执行摘要
- **核心投资观点:** 用2-3句话高度概括视频提出的核心投资论点或策略
- **主要投资建议:** 清晰列出视频推荐的核心投资标的（股票、行业等）和操作方向
- **预期收益与风险等级:** 总结视频中提及的潜在回报率和时间框架，并给出综合风险评级

## 2. 信息来源分析
- **视频创作者背景与可信度评估:** 对视频创作者进行背景评估，分析其观点倾向和可信度
- **内容发布时间的市场环境:** 结合视频发布日期，描述当时的市场宏观背景和投资者情绪
- **信息的时效性分析:** 评估报告中不同投资建议的时效性

## 3. 投资观点解析
对视频中提到的**每一个**投资标的或主题进行深入分析：
- **投资逻辑和理由:** 详细阐述视频作者看好该标的的核心原因
- **基本面/技术面分析要点:** 提取视频中提到的相关数据和技术信号
- **深度解读与批判性评估:** 基于专业知识，对视频观点进行延伸解读和评估
- **策略区分:** 将建议归类为不同的投资策略

## 4. 市场环境评估
- **宏观经济环境:** 分析当前宏观经济因素如何支持或挑战视频中的投资论点
- **相关行业/板块趋势:** 讨论标的所处行业的整体趋势、竞争格局和发展前景
- **政策环境影响:** 分析相关政策对投资标的的潜在影响

## 5. 风险评估
- **主要风险因素识别:** 全面识别每个投资建议面临的核心风险
- **风险等级评定:** 为每个投资组合或标的明确评定风险等级（低/中/高/投机级）
- **潜在损失预估:** 对风险发生时的潜在股价下行空间进行合理预估

## 6. 投资建议
- **具体操作建议:** 提供具体、可操作的投资执行建议
- **仓位配置建议:** 根据风险等级，提出合理的仓位管理建议
- **止盈止损策略:** 提出明确的退出策略

## 7. 补充说明
- **需要进一步验证的信息:** 指出投资者在采纳该策略前需要自行核实的关键信息
- **建议查阅的额外资料:** 推荐投资者可以查阅的额外信息源
- **与其他专业观点的对比:** 简要对比视频观点与市场主流观点

**# 分析准则与约束**
- **风格与语调:** 使用专业、严谨、客观的金融分析语调
- **深度要求:** 报告内容必须详尽，不少于3000中文字符
- **语言:** 使用**中文**进行回答
- **格式:** 严格使用Markdown格式，包含适当的标题、列表、加粗等格式

**重要声明：**
- 本报告基于YouTube视频内容整理，仅供参考
- 不构成正式投资建议，投资需谨慎
- 建议结合专业机构研报进行决策

**请开始分析视频内容。**
            """
        
        if log_callback:
            yield log_callback("正在连接LLM API...", "info")
            
        url = f"{self.base_url}/models/gemini-2.5-flash:generateContent"
        
        headers = {
            'x-goog-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'contents': [{
                'parts': [
                    {'text': prompt},
                    {
                        'file_data': {
                            'file_uri': video_url
                        }
                    }
                ]
            }]
        }
        
        try:
            if log_callback:
                yield log_callback("正在处理视频分析...", "info")
                
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            if log_callback:
                yield log_callback("正在解析分析结果...", "info")
            
            data = response.json()
            
            # 提取生成的内容
            if 'candidates' in data and len(data['candidates']) > 0:
                content = data['candidates'][0]['content']['parts'][0]['text']
                if log_callback:
                    yield log_callback("视频分析完成", "success")
                
                # 直接返回AI的原始Markdown内容，不进行字段提取处理
                yield {
                    'raw_content': content,
                    'summary': content  # 保持兼容性，前端可能还会用到summary字段
                }
            else:
                if log_callback:
                    yield log_callback("Gemini API返回了空的分析结果", "error")
                raise Exception("Gemini API返回了空的分析结果")
                
        except requests.RequestException as e:
            if log_callback:
                yield log_callback(f"Gemini API请求失败: {str(e)}", "error")
            raise Exception(f"Gemini视频分析失败: {str(e)}")
    
    def extract_stocks_from_video_with_logging(self, video_url, log_callback=None):
        """
        从视频中提取股票代码和相关信息（带日志回调）
        
        Args:
            video_url: YouTube视频URL
            log_callback: 日志回调函数
        """
        if log_callback:
            yield log_callback("开始提取视频中的股票信息...", "step")
            
        prompt = """
        请仔细分析这个YouTube视频，专门提取视频中提到的股票信息：

        1. 识别所有明确提到的股票代码（如AAPL、GOOGL、TSLA等）
        2. 识别提到的公司名称（如苹果、谷歌、特斯拉等）
        3. 评估每个股票/公司在视频中的重要性和讨论深度
        4. 判断对每个股票的观点倾向（积极/消极/中性）

        请以以下JSON格式返回结果：
        {
            "extracted_stocks": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "confidence": "high/medium/low",
                    "sentiment": "positive/negative/neutral",
                    "discussion_points": ["要点1", "要点2"]
                }
            ],
            "summary": "视频中股票讨论的总体摘要"
        }

        如果视频中没有明确提到具体股票，请返回空的extracted_stocks数组。
        """
        
        if log_callback:
            yield log_callback("正在连接Gemini API进行股票提取...", "info")
            
        url = f"{self.base_url}/models/gemini-2.5-flash:generateContent"
        
        headers = {
            'x-goog-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'contents': [{
                'parts': [
                    {'text': prompt},
                    {
                        'file_data': {
                            'file_uri': video_url
                        }
                    }
                ]
            }]
        }
        
        try:
            if log_callback:
                yield log_callback("正在处理股票提取...", "info")
                
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            if log_callback:
                yield log_callback("正在解析提取结果...", "info")
            
            data = response.json()
            
            # 提取生成的内容
            if 'candidates' in data and len(data['candidates']) > 0:
                content = data['candidates'][0]['content']['parts'][0]['text']
                if log_callback:
                    yield log_callback("股票提取完成", "success")
                yield self._parse_stock_extraction_result(content)
            else:
                if log_callback:
                    yield log_callback("Gemini API返回了空的股票提取结果", "error")
                raise Exception("Gemini API返回了空的股票提取结果")
                
        except requests.RequestException as e:
            if log_callback:
                yield log_callback(f"股票提取失败: {str(e)}", "error")
            raise Exception(f"Gemini股票提取失败: {str(e)}")

    def analyze_video(self, video_url, prompt=None):
        """
        使用Gemini分析YouTube视频（保持向后兼容）
        """
        # 使用带日志的方法，但不提供日志回调
        results = list(self.analyze_video_with_logging(video_url, prompt))
        # 返回最后一个非字符串结果（分析结果）
        for result in reversed(results):
            if not isinstance(result, str):
                return result
        return None
        
    def extract_stocks_from_video(self, video_url):
        """
        从视频中提取股票代码和相关信息（保持向后兼容）
        """
        # 使用带日志的方法，但不提供日志回调
        results = list(self.extract_stocks_from_video_with_logging(video_url))
        # 返回最后一个非字符串结果（提取结果）
        for result in reversed(results):
            if not isinstance(result, str):
                return result
        return None
    
    def _parse_stock_extraction_result(self, content):
        """解析股票提取结果"""
        try:
            # 尝试解析JSON格式的回复
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except:
            pass
        
        # 如果JSON解析失败，使用备用解析方法
        extracted_stocks = []
        lines = content.split('\n')
        
        for line in lines:
            # 简单的股票代码识别
            stock_symbols = re.findall(r'\b[A-Z]{1,5}\b', line)
            for symbol in stock_symbols:
                if len(symbol) >= 2 and symbol in ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']:
                    extracted_stocks.append({
                        'symbol': symbol,
                        'name': '',
                        'confidence': 'medium',
                        'sentiment': 'neutral',
                        'discussion_points': []
                    })
        
        return {
            'extracted_stocks': extracted_stocks,
            'summary': content[:200]
        }
    
    def _parse_analysis_result(self, content):
        """解析Gemini分析结果"""
        return {
            'raw_content': content,
            'summary': self._extract_summary(content),
            'companies': self._extract_companies(content),
            'market_events': self._extract_market_events(content),
            'investment_views': self._extract_investment_views(content),
            'risks': self._extract_risks(content)
        }
    
    def _extract_summary(self, content):
        """提取视频内容摘要"""
        # 简单的文本处理，实际可以用更复杂的NLP方法
        lines = content.split('\n')
        summary_lines = [line for line in lines if '总结' in line or '概述' in line]
        return '\n'.join(summary_lines[:3]) if summary_lines else content[:200]
    
    def _extract_companies(self, content):
        """提取提到的公司"""
        # 简化版本，实际可以用命名实体识别
        companies = []
        common_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META']
        for stock in common_stocks:
            if stock in content.upper():
                companies.append(stock)
        return companies
    
    def _extract_market_events(self, content):
        """提取市场事件"""
        events = []
        event_keywords = ['财报', '业绩', '发布', '收购', '合并', '新产品']
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line for keyword in event_keywords):
                events.append(line.strip())
        return events[:5]
    
    def _extract_investment_views(self, content):
        """提取投资观点"""
        views = []
        view_keywords = ['建议', '预测', '目标价', '评级', '看好', '看空']
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line for keyword in view_keywords):
                views.append(line.strip())
        return views[:3]
    

    def _parse_batch_analysis_result(self, content, videos):
        """解析批量分析结果"""
        try:
            # 尝试解析JSON格式的回复
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # 添加视频信息到结果中
                if 'individual_analyses' in result:
                    for i, analysis in enumerate(result['individual_analyses']):
                        if i < len(videos):
                            analysis['video_info'] = videos[i]
                return result
        except:
            pass
        
        # 如果JSON解析失败，使用备用解析方法
        return self._fallback_batch_analysis(content, videos)
    
    def _fallback_batch_analysis(self, content, videos):
        """备用的批量分析解析方法"""
        return {
            'batch_summary': {
                'total_videos': len(videos),
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'main_themes': ['投资分析', '市场观点'],
                'overall_sentiment': '中性',
                'key_insights': [content[:200] + '...' if len(content) > 200 else content]
            },
            'individual_analyses': [
                {
                    'video_index': i + 1,
                    'video_info': video,
                    'core_message': f'视频{i+1}的核心观点',
                    'investment_thesis': '待分析',
                    'mentioned_companies': [],
                    'key_points': ['内容分析中'],
                    'sentiment': '中性',
                    'confidence_level': '中'
                }
                for i, video in enumerate(videos)
            ],
            'consolidated_insights': {
                'common_themes': ['投资主题'],
                'consensus_views': ['市场观点'],
                'divergent_opinions': [],
                'investment_opportunities': [],
                'risk_factors': []
            },
            'raw_content': content
        }
    
    def analyze_batch_videos(self, video_urls, log_callback=None):
        """
        批量分析多个YouTube视频（最多10个）
        
        Args:
            video_urls: YouTube视频URL列表
            log_callback: 日志回调函数
        """
        if len(video_urls) > 10:
            raise ValueError("批量分析最多支持10个视频")
        
        if log_callback:
            yield log_callback("开始批量分析视频内容...", "step")
            
        # 适配批量分析的提示词
        prompt = f"""
### **【批量YouTube视频投资分析报告】**

**# 角色设定**
你是一名资深证券分析师，擅长从多个财经视频中提取核心投资观点，并进行综合分析。

**# 核心任务**
我将提供{len(video_urls)}个YouTube视频。你需要：
1. 分析每个视频的投资内容和观点
2. 识别共同主题和一致性观点
3. 生成一份综合性的投资观点报告

**# 输出要求**
请使用**Markdown格式**，按照以下结构输出：

## 1. 批量分析概览
- **视频数量**: {len(video_urls)}个
- **主要讨论主题**: 识别出的核心投资主题
- **整体投资情绪**: 积极/中性/消极

## 2. 各视频核心观点
对每个视频进行简要分析：
- **视频1**: 核心投资观点和建议
- **视频2**: 核心投资观点和建议
- [依此类推]

## 3. 综合投资洞察
- **共同观点**: 多个视频中的一致性观点
- **分歧观点**: 不同视频间的观点差异
- **投资机会**: 综合识别的投资机会

## 4. 综合投资建议
- **整体建议**: 基于多视频分析的综合建议
- **关注重点**: 需要重点关注的投资标的或主题
- **风险提示**: 综合风险评估

## 5. 行动建议
- **短期关注**: 近期需要关注的投资动向
- **中长期策略**: 基于分析的中长期投资思路
- **进一步研究**: 建议深入研究的方向

**# 分析要求**
- 使用中文回答
- 内容详尽，不少于2000字
- 保持客观和专业
- 重点关注投资逻辑和观点

**请开始分析这{len(video_urls)}个视频的内容。**
        """
        
        if log_callback:
            yield log_callback("正在连接Gemini API进行批量分析...", "info")
            
        url = f"{self.base_url}/models/gemini-2.5-flash:generateContent"
        
        headers = {
            'x-goog-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # 构建包含多个视频的请求
        parts = [{'text': prompt}]
        for i, video_url in enumerate(video_urls):
            parts.append({
                'file_data': {
                    'file_uri': video_url
                }
            })
        
        payload = {
            'contents': [{
                'parts': parts
            }]
        }
        
        try:
            if log_callback:
                yield log_callback("正在处理批量视频分析...", "info")
                
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            if log_callback:
                yield log_callback("正在解析批量分析结果...", "info")
            
            data = response.json()
            
            # 提取生成的内容
            if 'candidates' in data and len(data['candidates']) > 0:
                content = data['candidates'][0]['content']['parts'][0]['text']
                if log_callback:
                    yield log_callback("批量视频分析完成", "success")
                
                # 直接返回AI的原始Markdown内容
                yield {
                    'raw_content': content,
                    'summary': content,
                    'video_count': len(video_urls)
                }
            else:
                if log_callback:
                    yield log_callback("Gemini API返回了空的批量分析结果", "error")
                raise Exception("Gemini API返回了空的批量分析结果")
                
        except requests.RequestException as e:
            if log_callback:
                yield log_callback(f"批量分析失败: {str(e)}", "error")
            raise Exception(f"Gemini批量分析失败: {str(e)}")
    
    def _extract_risks(self, content):
        """提取风险因素"""
        risks = []
        risk_keywords = ['风险', '挑战', '不确定', '下跌', '波动']
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line for keyword in risk_keywords):
                risks.append(line.strip())
        return risks[:3]
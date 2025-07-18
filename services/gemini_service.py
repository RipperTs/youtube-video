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
            # 获取当前日期，用于报告日期
            current_date = datetime.now().strftime('%Y年%m月%d日')
            
            prompt = f"""
### **【MarketBeat投资分析报告生成】**

**# 重要说明**
当前分析时间：{current_date}
请在报告开头的日期中使用：{current_date}
不要推断或假设视频的发布时间，统一使用当前分析时间作为报告日期。

**# 角色设定**
你是一名在顶级投资银行（如高盛或摩根大通）工作的资深证券分析师。你擅长从非结构化信息（如财经视频）中快速提取核心观点，并以严谨、客观、深度分析的风格，撰写机构级别的投资研究报告。

**# 核心任务**
我将提供一个YouTube视频的链接。你的任务是：
1. 全面处理该视频的内容（包括其标题、创作者信息以及所有口头和视觉信息）。
2. 基于视频内容，生成一份综合性的、深度详尽的投资意见报告书。
3. 报告不仅是内容的总结，更要包含你作为专业分析师的批判性评估、背景分析和策略建议。

**# 输出要求：报告结构与内容指引**
请严格按照以下七个部分组织你的报告，使用**Markdown格式**输出：

**报告开头必须包含以下格式：**
```
# MarketBeat投资分析报告：[视频主题]

**报告日期：** {current_date}
**分析师：** [您的姓名]，资深证券分析师
```

## 1. 执行摘要
- **核心投资观点:** 用2-3句话高度概括视频提出的核心投资论点或策略
- **主要投资建议:** 清晰列出视频推荐的核心投资标的（股票、行业等）和操作方向
- **预期收益与风险等级:** 总结视频中提及的潜在回报率和时间框架，并给出综合风险评级

## 2. 信息来源分析
- **视频创作者背景与可信度评估:** 对视频创作者进行背景评估，分析其观点倾向和可信度
- **内容时效性与市场环境:** 基于当前市场环境({current_date})分析视频观点的时效性
- **信息的可靠性分析:** 评估报告中不同投资建议的可靠性

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
- **日期格式:** 报告开头的日期必须使用：{current_date}

**重要声明：**
- 本报告基于YouTube视频内容整理，仅供参考
- 不构成正式投资建议，投资需谨慎
- 建议结合专业机构研报进行决策

**请开始分析视频内容。**
            """
        
        if log_callback:
            yield log_callback("正在连接LLM API...", "info")
            
        url = f"{self.base_url}/models/gemini-2.5-pro:generateContent"
        
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
                
                # 返回完整的分析结果，同时提供原始内容和结构化数据
                analysis_result = {
                    'raw_content': content,
                    'summary': content  # 保持兼容性
                }
                
                # 解析出结构化数据以便后续处理
                try:
                    parsed_result = self._parse_analysis_result(content)
                    analysis_result.update(parsed_result)
                except Exception as e:
                    # 如果解析失败，至少保证基本字段存在
                    analysis_result.update({
                        'companies': [],
                        'market_events': [],
                        'investment_views': [],
                        'risks': []
                    })
                
                yield analysis_result
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
            
        url = f"{self.base_url}/models/gemini-2.5-pro:generateContent"
        
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
        # 首先尝试提取"执行摘要"部分
        lines = content.split('\n')
        summary_text = ""
        
        # 查找"执行摘要"或相关章节
        summary_section_started = False
        next_section_started = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否开始执行摘要部分
            if ('执行摘要' in line or '## 1.' in line or '核心投资观点' in line or 
                '主要投资建议' in line or line.startswith('## 1')):
                summary_section_started = True
                continue
            
            # 检查是否到达下一个章节
            if summary_section_started and (line.startswith('## 2') or 
                                          '信息来源分析' in line or 
                                          line.startswith('# 2') or
                                          ('##' in line and '执行摘要' not in line and '投资观点' not in line)):
                next_section_started = True
                break
            
            # 收集摘要内容
            if summary_section_started and not next_section_started:
                if line.startswith('*') or line.startswith('-') or line.startswith('•'):
                    summary_text += line + "\n"
                elif line and not line.startswith('#'):
                    summary_text += line + "\n"
        
        # 如果没有找到执行摘要，使用前面的内容
        if not summary_text:
            # 查找包含关键词的行作为摘要
            summary_lines = []
            for line in lines:
                if any(keyword in line for keyword in ['投资', '建议', '观点', '分析', '股票', '市场']):
                    summary_lines.append(line.strip())
                if len(summary_lines) >= 5:  # 限制长度
                    break
            
            if summary_lines:
                summary_text = '\n'.join(summary_lines)
            else:
                # 最后的备选方案：使用内容前200字符
                summary_text = content[:300]
        
        return summary_text.strip() if summary_text else '暂无摘要'
    
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
            
        # 根据视频数量生成动态的视频分析格式
        video_analysis_format = ""
        for i in range(len(video_urls)):
            video_analysis_format += f"- **视频{i+1}**: 核心投资观点和建议\n"
        
        # 获取当前日期，用于报告日期
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        # 适配批量分析的提示词
        prompt = f"""
### **【批量YouTube视频投资分析报告】**

**# 重要说明**
当前分析时间：{current_date}
请在报告开头的日期中使用：{current_date}
不要推断或假设视频的发布时间，统一使用当前分析时间作为报告日期。

**# 角色设定**
你是一名资深证券分析师，擅长从多个财经视频中提取核心投资观点，并进行综合分析。

**# 核心任务**
我将提供{len(video_urls)}个YouTube视频。你需要：
1. 分析每个视频的投资内容和观点
2. 识别共同主题和一致性观点
3. 生成一份综合性的投资观点报告

**# 输出要求**
请使用**Markdown格式**，按照以下结构输出一份完整的投资分析报告：

**报告开头必须包含以下格式：**
```
# MarketBeat批量投资分析报告

**报告日期：** {current_date}
**分析师：** [您的姓名]，资深证券分析师
**分析视频数量：** {len(video_urls)}个
```

## 📊 批量分析概览
- **视频数量**: {len(video_urls)}个
- **主要讨论主题**: 识别出的核心投资主题
- **整体投资情绪**: 积极/中性/消极

## 🎯 各视频核心观点
对每个视频进行简要分析：
{video_analysis_format}

## 💡 综合投资洞察
- **共同观点**: 多个视频中的一致性观点
- **分歧观点**: 不同视频间的观点差异
- **投资机会**: 综合识别的投资机会

## 📈 综合投资建议
- **整体建议**: 基于多视频分析的综合建议
- **关注重点**: 需要重点关注的投资标的或主题
- **风险提示**: 综合风险评估

## 🚀 行动建议
- **短期关注**: 近期需要关注的投资动向
- **中长期策略**: 基于分析的中长期投资思路
- **进一步研究**: 建议深入研究的方向

**# 分析要求**
- 使用中文回答
- 内容详尽，不少于2000字
- 保持客观和专业
- 重点关注投资逻辑和观点
- 请按照上述格式完整输出，你有能力自己做好排版
- **日期格式:** 报告开头的日期必须使用：{current_date}

**请开始分析这{len(video_urls)}个视频的内容。**
        """
        
        if log_callback:
            yield log_callback("正在连接Gemini API进行批量分析...", "info")
            
        url = f"{self.base_url}/models/gemini-2.5-pro:generateContent"
        
        headers = {
            'x-goog-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # 构建包含多个视频的请求
        parts = []
        parts.append({'text': prompt})
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

        print(payload)
        
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
    
    def generate_text(self, prompt):
        """
        使用Gemini生成文本内容
        
        Args:
            prompt: 文本生成提示词
            
        Returns:
            dict: 包含生成结果的字典
        """
        try:
            url = f"{self.base_url}/models/gemini-2.5-pro:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.api_key
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 8192,
                },
                "tools": [
                    {
                        "google_search": {}
                    }
                ]
            }
            
            print("📡 正在调用Gemini API (启用搜索工具)...")
            response = requests.post(url, headers=headers, json=data, timeout=180)  # 增加超时时间以支持搜索工具
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    content_parts = candidate['content']['parts']
                    
                    # 检查是否使用了搜索工具
                    used_search = False
                    if 'usageMetadata' in result and 'candidatesTokenCount' in result['usageMetadata']:
                        print(f"🔍 API响应包含 {len(content_parts)} 个部分")
                    
                    # 处理可能包含工具调用的响应
                    final_content = ""
                    for i, part in enumerate(content_parts):
                        if 'text' in part:
                            final_content += part['text']
                        elif 'functionCall' in part:
                            used_search = True
                            print(f"🔍 检测到搜索工具调用: {part.get('functionCall', {}).get('name', 'unknown')}")
                    
                    if used_search:
                        print("✅ AI使用了搜索工具获取实时信息")
                    else:
                        print("ℹ️ AI未使用搜索工具")
                    
                    # 如果没有文本内容，可能是因为只有工具调用
                    if not final_content and content_parts:
                        final_content = "AI正在使用搜索工具获取信息，请等待完整响应..."
                    
                    return {
                        'success': True,
                        'summary': final_content,
                        'raw_content': final_content,
                        'full_response': result  # 保留完整响应用于调试
                    }
                else:
                    return {
                        'success': False,
                        'error': '未获取到有效回复',
                        'summary': '生成失败'
                    }
            else:
                return {
                    'success': False,
                    'error': f'API请求失败: {response.status_code}',
                    'summary': '生成失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'summary': '生成失败'
            }
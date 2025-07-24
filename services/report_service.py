from datetime import datetime
import json
import os
import tempfile
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


class ReportService:
    """投资报告生成服务"""

    def __init__(self):
        self.font_config = FontConfiguration()

    def generate_pdf_report(self, cache_key, cached_data, video_urls):
        """
        生成PDF报告

        Args:
            cache_key: 缓存键
            cached_data: 缓存的分析数据
            video_urls: 视频URL列表

        Returns:
            str: PDF文件路径
        """
        try:
            # 创建PDF目录
            pdf_dir = 'cache/pdf'
            os.makedirs(pdf_dir, exist_ok=True)

            # 生成PDF文件路径
            pdf_file = os.path.join(pdf_dir, f'{cache_key}.pdf')

            # 生成HTML内容
            html_content = self._generate_html_content(cached_data, video_urls)

            # 生成CSS样式
            css_content = self._get_pdf_styles()

            # 使用WeasyPrint生成PDF
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=css_content, font_config=self.font_config)

            html_doc.write_pdf(pdf_file, stylesheets=[css_doc], font_config=self.font_config)

            return pdf_file

        except Exception as e:
            print(f"PDF生成失败: {e}")
            raise e

    def _generate_html_content(self, cached_data, video_urls):
        """生成HTML内容"""
        if isinstance(video_urls, str):
            video_urls = [video_urls]

        report = cached_data.get('report', {})
        video_analysis = cached_data.get('video_analysis', {})
        analysis_type = cached_data.get('analysis_type', 'content_only')

        # 开始构建HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>YouTube投资分析报告</title>
</head>
<body>
    <div class="header">
        <h1>YouTube投资分析报告</h1>
        <div class="meta-info">
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
            <p><strong>分析类型:</strong> {self._get_analysis_type_name(analysis_type)}</p>
            <p><strong>视频数量:</strong> {len(video_urls)}</p>
        </div>
    </div>

    <div class="video-links">
        <h2>分析视频</h2>
        """

        for i, url in enumerate(video_urls, 1):
            html += f'<p>{i}. <a href="{url}">{url}</a></p>\n'

        html += '</div>\n'

        # 添加报告内容
        html += '<div class="report-content">\n'

        if report.get('raw_markdown_content'):
            # 纯内容分析报告
            html += '<h2>分析报告</h2>\n'
            html += self._markdown_to_html(report['raw_markdown_content'])
        elif report.get('executive_summary'):
            # 有结构的报告
            html += '<h2>执行摘要</h2>\n'
            html += self._markdown_to_html(report['executive_summary'])

            if report.get('investment_recommendation'):
                html += '<h2>投资建议</h2>\n'
                rec = report['investment_recommendation']
                html += f"""
                <div class="recommendation-box">
                    <h3>建议: {rec.get('action', 'N/A')}</h3>
                    <p><strong>信心水平:</strong> {rec.get('confidence_level', 'N/A')}</p>
                    <p><strong>投资期限:</strong> {rec.get('time_horizon', 'N/A')}</p>
                    <p><strong>理由:</strong> {rec.get('reasoning', 'N/A')}</p>
                </div>
                """

            if report.get('risk_assessment'):
                html += '<h2>风险评估</h2>\n'
                if isinstance(report['risk_assessment'], dict):
                    risk = report['risk_assessment']
                    html += f'<p><strong>总体风险级别:</strong> {risk.get("overall_risk_level", "N/A")}</p>\n'
                else:
                    html += self._markdown_to_html(str(report['risk_assessment']))

            if report.get('price_targets'):
                html += '<h2>价格目标</h2>\n'
                targets = report['price_targets']
                html += f"""
                <div class="price-targets">
                    <p><strong>当前价格:</strong> ${targets.get('current_price', 'N/A')}</p>
                    <p><strong>12个月目标:</strong> ${targets.get('target_12m', 'N/A')}</p>
                    <p><strong>止损位:</strong> ${targets.get('stop_loss', 'N/A')}</p>
                    <p><strong>支撑位:</strong> ${targets.get('support_level', 'N/A')}</p>
                </div>
                """

        html += '</div>\n'

        # 添加视频分析部分
        if video_analysis:
            html += '<div class="video-analysis">\n'
            html += '<h2>视频内容分析</h2>\n'
            html += f'<h3>内容摘要</h3>\n'
            html += self._markdown_to_html(video_analysis.get('summary', '暂无摘要'))

            if video_analysis.get('companies'):
                html += '<h3>提及的公司</h3>\n<ul>\n'
                for company in video_analysis['companies']:
                    html += f'<li>{company}</li>\n'
                html += '</ul>\n'

            if video_analysis.get('market_events'):
                html += '<h3>市场事件</h3>\n<ul>\n'
                for event in video_analysis['market_events']:
                    html += f'<li>{event}</li>\n'
                html += '</ul>\n'

            if video_analysis.get('investment_views'):
                html += '<h3>投资观点</h3>\n<ul>\n'
                for view in video_analysis['investment_views']:
                    html += f'<li>{view}</li>\n'
                html += '</ul>\n'

            html += '</div>\n'

        # 添加股票数据（如果有）
        stock_data = cached_data.get('stock_data')
        if stock_data:
            html += '<div class="stock-data">\n'
            html += '<h2>股票数据分析</h2>\n'

            if isinstance(stock_data, list):
                for stock in stock_data:
                    html += self._format_stock_data_html(stock)
            else:
                html += self._format_stock_data_html(stock_data)

            html += '</div>\n'

        # 免责声明
        html += f"""
        <div class="disclaimer">
            <h2>免责声明</h2>
            <p>{self._get_disclaimer()}</p>
        </div>

        </body>
        </html>
        """

        return html

    def _format_stock_data_html(self, stock):
        """格式化单个股票数据为HTML"""
        return f"""
        <div class="stock-item">
            <h3>{stock.get('symbol', 'N/A')} - {stock.get('name', '未知公司')}</h3>
            <p><strong>当前价格:</strong> ${stock.get('latest_price', 'N/A')}</p>
            <p><strong>涨跌幅:</strong> {stock.get('pct_change', 'N/A')}%</p>
            <p><strong>价格趋势:</strong> {stock.get('price_trend', 'N/A')}</p>
            <p><strong>波动率:</strong> {stock.get('volatility', 'N/A')}%</p>
        </div>
        """

    def _markdown_to_html(self, markdown_text):
        """将Markdown转换为HTML"""
        if not markdown_text:
            return '<p>暂无内容</p>'

        try:
            html = markdown.markdown(markdown_text, extensions=['extra', 'codehilite'])
            return html
        except Exception as e:
            print(f"Markdown转换失败: {e}")
            return f'<p>{markdown_text}</p>'

    def _get_analysis_type_name(self, analysis_type):
        """获取分析类型中文名称"""
        type_names = {
            'content_only': '纯内容分析',
            'stock_extraction': '股票提取分析',
            'manual_stock': '手动股票分析',
            'batch_content': '批量内容分析',
            'batch_selected': '批量选择分析'
        }
        return type_names.get(analysis_type, '未知类型')

    def _get_pdf_styles(self):
        """获取PDF样式"""
        return """
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "YouTube投资分析报告";
                font-size: 12px;
                color: #666;
            }
            @bottom-center {
                content: counter(page) " / " counter(pages);
                font-size: 10px;
                color: #666;
            }
        }

        body {
            font-family: "SimHei", "Microsoft YaHei", "Arial", sans-serif;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007bff;
        }

        .header h1 {
            color: #007bff;
            font-size: 24px;
            margin-bottom: 10px;
        }

        .meta-info {
            font-size: 11px;
            color: #666;
        }

        .meta-info p {
            margin: 5px 0;
        }

        h2 {
            color: #007bff;
            font-size: 18px;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }

        h3 {
            color: #333;
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        p {
            margin: 8px 0;
            text-align: justify;
        }

        ul {
            margin: 10px 0;
            padding-left: 20px;
        }

        li {
            margin: 5px 0;
        }

        .video-links {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .video-links a {
            color: #007bff;
            text-decoration: none;
            word-break: break-all;
        }

        .recommendation-box {
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007bff;
            margin: 15px 0;
        }

        .recommendation-box h3 {
            color: #007bff;
            margin-top: 0;
        }

        .price-targets {
            background-color: #f0f8f0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
            margin: 15px 0;
        }

        .stock-item {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
        }

        .disclaimer {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin-top: 30px;
            font-size: 11px;
            line-height: 1.4;
        }

        .disclaimer h2 {
            color: #856404;
            font-size: 14px;
            margin-top: 0;
        }

        strong {
            font-weight: bold;
            color: #333;
        }

        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
            font-size: 11px;
        }

        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 11px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }

        blockquote {
            border-left: 4px solid #ddd;
            margin: 15px 0;
            padding-left: 15px;
            color: #666;
            font-style: italic;
        }

        .page-break {
            page-break-before: always;
        }
        """

    def generate_report(self, video_analysis, stock_data):
        """
        生成单个视频的投资分析报告

        Args:
            video_analysis: 视频分析结果
            stock_data: 股票数据
        """
        report = {
            'title': f'{stock_data["symbol"]} 投资分析报告',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'executive_summary': self._generate_executive_summary(video_analysis, stock_data),
            'video_insights': self._format_video_insights(video_analysis),
            'market_analysis': self._generate_market_analysis(stock_data),
            'investment_recommendation': self._generate_recommendation(video_analysis, stock_data),
            'risk_assessment': self._generate_risk_assessment(video_analysis, stock_data),
            'price_targets': self._generate_price_targets(stock_data),
            'disclaimer': self._get_disclaimer()
        }

        return report

    def generate_content_only_report(self, video_analysis):
        """
        生成纯内容分析报告（直接使用AI返回的Markdown内容）

        Args:
            video_analysis: 视频分析结果，包含AI的原始Markdown内容
        """
        # 直接使用AI返回的原始内容作为报告
        raw_content = video_analysis.get('raw_content', video_analysis.get('summary', ''))

        report = {
            'title': '视频内容投资逻辑分析报告',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'raw_markdown_content': raw_content,  # AI的原始Markdown内容
            'disclaimer': self._get_disclaimer()
        }

        return report

    def generate_stock_extraction_report(self, video_analysis, stock_data_list, extracted_stocks):
        """
        生成基于股票提取的综合分析报告

        Args:
            video_analysis: 视频分析结果
            stock_data_list: 提取股票的数据列表
            extracted_stocks: 提取的股票信息
        """
        report = {
            'title': '视频股票提取与数据分析报告',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stocks_analyzed': len(extracted_stocks),
            'executive_summary': self._generate_extraction_summary(video_analysis, stock_data_list, extracted_stocks),
            'video_insights': self._format_video_insights(video_analysis),
            'extracted_stocks_analysis': self._analyze_extracted_stocks(stock_data_list, extracted_stocks),
            'investment_recommendation': self._generate_multi_stock_recommendation(video_analysis, stock_data_list,
                                                                                   extracted_stocks),
            'risk_assessment': self._generate_extraction_risk_assessment(video_analysis, stock_data_list),
            'stock_comparison': self._compare_extracted_stocks(stock_data_list),
            'disclaimer': self._get_disclaimer()
        }

        return report

    def generate_batch_report(self, analysis_results, stock_data):
        """生成批量视频分析报告"""
        report = {
            'title': f'{stock_data["symbol"]} 综合投资分析报告',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'video_count': len(analysis_results),
            'executive_summary': self._generate_batch_summary(analysis_results, stock_data),
            'individual_analyses': analysis_results,
            'consolidated_insights': self._consolidate_insights(analysis_results),
            'market_analysis': self._generate_market_analysis(stock_data),
            'investment_recommendation': self._generate_batch_recommendation(analysis_results, stock_data),
            'risk_assessment': self._generate_batch_risk_assessment(analysis_results, stock_data),
            'disclaimer': self._get_disclaimer()
        }

        return report

    def _generate_executive_summary(self, video_analysis, stock_data):
        """生成执行摘要"""
        summary = f"""
        基于最新视频分析和{stock_data['symbol']}股票数据，本报告提供以下关键洞察：

        视频核心观点：{video_analysis.get('summary', '暂无摘要')}

        当前股价：${stock_data['latest_price']:.2f}
        近期表现：{stock_data['pct_change']:+.2f}% ({stock_data['price_trend']})
        市场波动率：{stock_data['volatility']}%

        综合分析显示该股票{self._get_overall_sentiment(video_analysis, stock_data)}。
        """

        return summary.strip()

    def _generate_batch_summary(self, analysis_results, stock_data):
        """生成批量分析执行摘要"""
        total_videos = len(analysis_results)

        summary = f"""
        基于{total_videos}个视频的综合分析和{stock_data['symbol']}股票数据：

        当前股价：${stock_data['latest_price']:.2f}
        近期表现：{stock_data['pct_change']:+.2f}% ({stock_data['price_trend']})

        视频分析显示市场对该股票的整体情绪{self._get_batch_sentiment(analysis_results)}。
        """

        return summary.strip()

    def _format_video_insights(self, video_analysis):
        """格式化视频洞察"""
        return {
            'content_summary': video_analysis.get('summary', ''),
            'mentioned_companies': video_analysis.get('companies', []),
            'market_events': video_analysis.get('market_events', []),
            'expert_opinions': video_analysis.get('investment_views', []),
            'identified_risks': video_analysis.get('risks', [])
        }

    def _generate_market_analysis(self, stock_data):
        """生成市场分析"""
        analysis = {
            'current_price': stock_data['latest_price'],
            'price_trend': stock_data['price_trend'],
            'volatility_assessment': self._assess_volatility(stock_data['volatility']),
            'volume_analysis': self._analyze_volume(stock_data['volume']),
            'technical_indicators': {
                'trend': stock_data['price_trend'],
                'volatility': f"{stock_data['volatility']}%",
                'momentum': '正面' if stock_data['pct_change'] > 0 else '负面'
            }
        }

        return analysis

    def _generate_recommendation(self, video_analysis, stock_data):
        """生成投资建议"""
        # 简化的评分逻辑
        score = 0

        # 基于价格趋势评分
        if stock_data['price_trend'] in ['强势上涨', '温和上涨']:
            score += 2
        elif stock_data['price_trend'] == '横盘整理':
            score += 1

        # 基于波动率评分
        if stock_data['volatility'] < 10:
            score += 1
        elif stock_data['volatility'] > 20:
            score -= 1

        # 基于视频情绪评分（简化）
        positive_words = ['看好', '上涨', '增长', '乐观']
        negative_words = ['风险', '下跌', '担忧', '悲观']

        content = video_analysis.get('raw_content', '').lower()
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)

        if positive_count > negative_count:
            score += 1
        elif negative_count > positive_count:
            score -= 1

        # 生成建议
        if score >= 3:
            recommendation = '买入'
            confidence = '高'
        elif score >= 1:
            recommendation = '持有'
            confidence = '中等'
        else:
            recommendation = '观望'
            confidence = '低'

        return {
            'action': recommendation,
            'confidence_level': confidence,
            'reasoning': f'基于技术分析评分({score}/4)和视频内容分析',
            'time_horizon': '1-3个月'
        }

    def _generate_batch_recommendation(self, analysis_results, stock_data):
        """生成批量分析投资建议"""
        # 综合多个视频的分析结果
        total_sentiment = 0

        for result in analysis_results:
            analysis = result.get('analysis', {})
            content = analysis.get('raw_content', '').lower()

            positive_words = ['看好', '上涨', '增长', '乐观']
            negative_words = ['风险', '下跌', '担忧', '悲观']

            positive_count = sum(1 for word in positive_words if word in content)
            negative_count = sum(1 for word in negative_words if word in content)

            if positive_count > negative_count:
                total_sentiment += 1
            elif negative_count > positive_count:
                total_sentiment -= 1

        # 结合股票表现
        stock_score = 1 if stock_data['pct_change'] > 0 else -1
        final_score = total_sentiment + stock_score

        if final_score > 0:
            action = '买入'
            confidence = '中等'
        elif final_score == 0:
            action = '持有'
            confidence = '中等'
        else:
            action = '观望'
            confidence = '中等'

        return {
            'action': action,
            'confidence_level': confidence,
            'reasoning': f'基于{len(analysis_results)}个视频的综合分析',
            'sentiment_score': total_sentiment,
            'time_horizon': '1-3个月'
        }

    def _generate_risk_assessment(self, video_analysis, stock_data):
        """生成风险评估"""
        risks = []

        # 波动率风险
        if stock_data['volatility'] > 15:
            risks.append('高波动率风险：股价波动较大，短期投资风险较高')

        # 从视频中提取的风险
        video_risks = video_analysis.get('risks', [])
        risks.extend(video_risks)

        # 市场风险
        if stock_data['pct_change'] < -5:
            risks.append('近期表现疲软：股价出现较大跌幅')

        return {
            'overall_risk_level': self._assess_overall_risk(stock_data['volatility'], stock_data['pct_change']),
            'specific_risks': risks,
            'mitigation_strategies': [
                '分散投资降低单一股票风险',
                '设置止损点控制下行风险',
                '关注公司基本面变化'
            ]
        }

    def _generate_batch_risk_assessment(self, analysis_results, stock_data):
        """生成批量分析风险评估"""
        all_risks = []

        for result in analysis_results:
            analysis = result.get('analysis', {})
            risks = analysis.get('risks', [])
            all_risks.extend(risks)

        # 去重
        unique_risks = list(set(all_risks))

        return {
            'overall_risk_level': self._assess_overall_risk(stock_data['volatility'], stock_data['pct_change']),
            'specific_risks': unique_risks,
            'risk_frequency': len(all_risks),
            'mitigation_strategies': [
                '基于多源信息进行投资决策',
                '持续监控市场动态',
                '适当的仓位管理'
            ]
        }

    def _generate_price_targets(self, stock_data):
        """生成价格目标"""
        current_price = stock_data['latest_price']

        return {
            'current_price': current_price,
            'target_12m': round(current_price * 1.15, 2),  # 15%上涨目标
            'stop_loss': round(current_price * 0.90, 2),  # 10%止损
            'support_level': round(current_price * 0.95, 2),
            'resistance_level': round(current_price * 1.10, 2)
        }

    def _consolidate_insights(self, analysis_results):
        """整合多个视频的洞察"""
        all_companies = []
        all_events = []
        all_views = []

        for result in analysis_results:
            analysis = result.get('analysis', {})
            all_companies.extend(analysis.get('companies', []))
            all_events.extend(analysis.get('market_events', []))
            all_views.extend(analysis.get('investment_views', []))

        return {
            'frequently_mentioned_companies': list(set(all_companies)),
            'key_market_events': list(set(all_events)),
            'expert_consensus': list(set(all_views))
        }

    def _get_overall_sentiment(self, video_analysis, stock_data):
        """获取整体情绪"""
        if stock_data['pct_change'] > 2:
            return '表现积极'
        elif stock_data['pct_change'] < -2:
            return '面临压力'
        else:
            return '表现平稳'

    def _get_batch_sentiment(self, analysis_results):
        """获取批量分析情绪"""
        return '相对积极'  # 简化实现

    def _assess_volatility(self, volatility):
        """评估波动率"""
        if volatility < 10:
            return '低波动'
        elif volatility < 20:
            return '中等波动'
        else:
            return '高波动'

    def _analyze_volume(self, volume):
        """分析成交量"""
        if volume > 1000000:
            return '成交活跃'
        else:
            return '成交清淡'

    def _assess_overall_risk(self, volatility, pct_change):
        """评估整体风险"""
        if volatility > 20 or abs(pct_change) > 10:
            return '高风险'
        elif volatility > 10 or abs(pct_change) > 5:
            return '中等风险'
        else:
            return '低风险'

    def _get_disclaimer(self):
        """获取免责声明"""
        return """
        免责声明：
        本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
        报告基于公开信息和AI分析生成，可能存在误差或偏差。
        投资者应当结合自身情况，独立做出投资决策。
        """

    # 新增的辅助方法
    def _generate_content_only_summary(self, video_analysis):
        """生成纯内容分析的执行摘要"""
        summary = f"""
        基于视频内容的投资逻辑分析：

        视频核心观点：{video_analysis.get('summary', '暂无摘要')}

        提到的公司：{', '.join(video_analysis.get('companies', [])) if video_analysis.get('companies') else '无具体公司'}
        关键市场事件：{len(video_analysis.get('market_events', []))}个
        投资观点：{len(video_analysis.get('investment_views', []))}个

        本分析专注于视频内容的投资逻辑，不涉及具体股价数据。
        """
        return summary.strip()

    def _extract_investment_logic(self, video_analysis):
        """提取投资逻辑"""
        core_thesis = video_analysis.get('summary', '暂无核心观点')
        supporting_arguments = video_analysis.get('investment_views', [])
        market_context = video_analysis.get('market_events', [])

        logic_text = f"""核心观点：{core_thesis}

投资论据：
{chr(10).join(['• ' + arg for arg in supporting_arguments[:3]]) if supporting_arguments else '• 暂无明确投资论据'}

市场背景：
{chr(10).join(['• ' + event for event in market_context[:3]]) if market_context else '• 暂无相关市场事件'}

分析框架：基于视频内容分析得出的投资逻辑，建议结合其他信息源进行验证。"""

        return logic_text.strip()

    def _extract_market_perspective(self, video_analysis):
        """提取市场观点"""
        return {
            'overall_sentiment': '市场情绪分析',
            'key_themes': video_analysis.get('companies', []),
            'expert_views': video_analysis.get('investment_views', []),
            'market_drivers': video_analysis.get('market_events', [])
        }

    def _generate_content_risk_assessment(self, video_analysis):
        """生成内容风险评估"""
        risks = video_analysis.get('risks', [])

        risk_text = f"""信息风险：
• 基于单一信息源
• 可能存在观点偏差

内容相关风险：
{chr(10).join(['• ' + risk for risk in risks]) if risks else '• 暂无识别到的具体风险'}

分析局限性：
• 未结合实时股价数据
• 仅基于视频内容分析
• 缺少基本面分析

风险缓解建议：
• 结合多个信息源进行分析
• 考虑市场实际表现
• 保持理性投资态度
• 定期更新分析结论"""

        return risk_text.strip()

    def _extract_key_takeaways(self, video_analysis):
        """提取关键要点"""
        main_insights = video_analysis.get('investment_views', [])[:3]

        takeaways_text = f"""主要洞察：
{chr(10).join(['• ' + insight for insight in main_insights]) if main_insights else '• 暂无明确投资洞察'}

行动建议：
• 关注提到的公司动态
• 监控相关市场事件
• 跟踪后续发展

后续研究：
• 验证视频中的观点
• 查看最新财务数据
• 对比其他分析师观点
• 关注相关新闻动态"""

        return takeaways_text.strip()

    def _generate_extraction_summary(self, video_analysis, stock_data_list, extracted_stocks):
        """生成股票提取分析的执行摘要"""
        stock_symbols = [stock['symbol'] for stock in extracted_stocks]
        avg_performance = sum([data.get('pct_change', 0) for data in stock_data_list]) / len(
            stock_data_list) if stock_data_list else 0

        summary = f"""
        从视频中提取并分析了{len(extracted_stocks)}只股票：{', '.join(stock_symbols)}

        视频核心观点：{video_analysis.get('summary', '暂无摘要')}

        股票平均表现：{avg_performance:+.2f}%
        分析数据完整性：{len(stock_data_list)}/{len(extracted_stocks)}只股票获得数据

        本分析基于视频内容提取的股票，结合实时市场数据进行综合评估。
        """
        return summary.strip()

    def _analyze_extracted_stocks(self, stock_data_list, extracted_stocks):
        """分析提取的股票"""
        analysis = []

        for i, stock_data in enumerate(stock_data_list):
            extracted_info = extracted_stocks[i] if i < len(extracted_stocks) else {}

            analysis.append({
                'symbol': stock_data['symbol'],
                'extraction_confidence': extracted_info.get('confidence', 'medium'),
                'video_sentiment': extracted_info.get('sentiment', 'neutral'),
                'current_performance': f"{stock_data.get('pct_change', 0):+.2f}%",
                'price_trend': stock_data.get('price_trend', '未知'),
                'volatility': f"{stock_data.get('volatility', 0)}%"
            })

        return analysis

    def _generate_multi_stock_recommendation(self, video_analysis, stock_data_list, extracted_stocks):
        """生成多股票投资建议"""
        if not stock_data_list:
            return {
                'overall_action': '无法分析',
                'reason': '未获取到股票数据',
                'individual_recommendations': []
            }

        positive_count = sum(1 for data in stock_data_list if data.get('pct_change', 0) > 0)
        total_count = len(stock_data_list)

        if positive_count / total_count > 0.6:
            overall_action = '积极关注'
        elif positive_count / total_count > 0.4:
            overall_action = '谨慎观察'
        else:
            overall_action = '保持警惕'

        individual_recs = []
        for i, stock_data in enumerate(stock_data_list):
            extracted_info = extracted_stocks[i] if i < len(extracted_stocks) else {}

            if stock_data.get('pct_change', 0) > 2:
                action = '关注'
            elif stock_data.get('pct_change', 0) < -2:
                action = '谨慎'
            else:
                action = '观察'

            individual_recs.append({
                'symbol': stock_data['symbol'],
                'action': action,
                'confidence': extracted_info.get('confidence', 'medium'),
                'reasoning': f"基于{stock_data.get('pct_change', 0):+.2f}%表现和视频讨论"
            })

        return {
            'overall_action': overall_action,
            'confidence_level': '中等',
            'reasoning': f'基于{total_count}只股票的综合表现分析',
            'individual_recommendations': individual_recs
        }

    def _generate_extraction_risk_assessment(self, video_analysis, stock_data_list):
        """生成提取分析的风险评估"""
        if not stock_data_list:
            return {
                'overall_risk_level': '高风险',
                'specific_risks': ['无股票数据支撑', '仅基于视频内容'],
                'mitigation_strategies': ['获取完整市场数据', '扩大信息源']
            }

        avg_volatility = sum([data.get('volatility', 0) for data in stock_data_list]) / len(stock_data_list)
        content_risks = video_analysis.get('risks', [])

        specific_risks = content_risks + [
            f'平均波动率{avg_volatility:.1f}%',
            '多股票组合风险',
            '基于单一视频源'
        ]

        if avg_volatility > 20:
            risk_level = '高风险'
        elif avg_volatility > 10:
            risk_level = '中等风险'
        else:
            risk_level = '低风险'

        return {
            'overall_risk_level': risk_level,
            'specific_risks': specific_risks,
            'portfolio_volatility': f"{avg_volatility:.1f}%",
            'mitigation_strategies': [
                '分散化投资组合',
                '设置合理止损位',
                '持续监控市场变化',
                '验证视频观点的准确性'
            ]
        }

    def _compare_extracted_stocks(self, stock_data_list):
        """比较提取的股票"""
        if not stock_data_list:
            return {'comparison': '无数据'}

        best_performer = max(stock_data_list, key=lambda x: x.get('pct_change', 0))
        worst_performer = min(stock_data_list, key=lambda x: x.get('pct_change', 0))

        return {
            'best_performer': {
                'symbol': best_performer['symbol'],
                'performance': f"{best_performer.get('pct_change', 0):+.2f}%"
            },
            'worst_performer': {
                'symbol': worst_performer['symbol'],
                'performance': f"{worst_performer.get('pct_change', 0):+.2f}%"
            },
            'performance_spread': f"{best_performer.get('pct_change', 0) - worst_performer.get('pct_change', 0):.2f}%",
            'average_performance': f"{sum([data.get('pct_change', 0) for data in stock_data_list]) / len(stock_data_list):+.2f}%"
        }

    def generate_batch_content_report(self, batch_analysis):
        """
        生成批量内容分析报告（直接使用AI返回的Markdown内容）

        Args:
            batch_analysis: 批量分析结果，包含AI的原始Markdown内容
        """
        # 直接使用AI返回的原始内容作为报告
        raw_content = batch_analysis.get('raw_content', batch_analysis.get('summary', ''))
        video_count = batch_analysis.get('video_count', 0)

        # 添加调试信息
        print(f"[DEBUG] 批量分析结果 - 视频数量: {video_count}")
        print(f"[DEBUG] raw_content 长度: {len(raw_content) if raw_content else 0}")

        if not raw_content:
            print("[DEBUG] 警告: 未获取到AI分析内容")
            raw_content = "批量分析已完成，但未获取到详细分析内容。"

        report = {
            'title': f'批量视频内容投资分析报告 ({video_count}个视频)',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'video_count': video_count,
            'raw_markdown_content': raw_content,  # AI的原始Markdown内容
            'executive_summary': f'本报告基于{video_count}个YouTube视频的内容分析，提取投资相关观点和逻辑。',
            'individual_analyses': self._extract_individual_analyses(raw_content),
            'consolidated_insights': self._extract_consolidated_insights(raw_content),
            'investment_recommendation': self._extract_batch_recommendation(raw_content),
            'risk_assessment': self._extract_batch_risk_assessment(raw_content),
            'disclaimer': self._get_disclaimer()
        }

        print(f"[DEBUG] 报告生成完成，包含的字段: {list(report.keys())}")
        return report

    def _extract_individual_analyses(self, content):
        """从内容中提取各个视频的分析"""
        analyses = []
        # 简化实现，实际可以用更复杂的解析
        lines = content.split('\n')
        current_analysis = {}

        for line in lines:
            if '视频' in line and ('核心观点' in line or '投资观点' in line):
                if current_analysis:
                    analyses.append(current_analysis)
                current_analysis = {
                    'analysis': line.strip(),
                    'summary': line.strip()
                }
            elif current_analysis and line.strip():
                current_analysis['analysis'] += '\n' + line.strip()

        if current_analysis:
            analyses.append(current_analysis)

        return analyses

    def _extract_consolidated_insights(self, content):
        """从内容中提取综合洞察"""
        return {
            'common_themes': self._extract_section_content(content, '共同观点'),
            'consensus_views': self._extract_section_content(content, '一致性观点'),
            'investment_opportunities': self._extract_section_content(content, '投资机会')
        }

    def _extract_batch_recommendation(self, content):
        """从内容中提取批量推荐"""
        return {
            'action': self._extract_section_content(content, '整体建议'),
            'confidence_level': '中等',
            'reasoning': '基于多个视频的综合分析',
            'time_horizon': '中长期'
        }

    def _extract_batch_risk_assessment(self, content):
        """从内容中提取批量风险评估"""
        return {
            'overall_risk_level': '中等风险',
            'specific_risks': [
                '基于视频内容分析，存在信息偏差风险',
                '需要结合其他信息源验证',
                '市场环境变化可能影响分析结果'
            ],
            'mitigation_strategies': [
                '多元化信息源',
                '定期更新分析',
                '结合专业研究报告'
            ]
        }

    def _extract_section_content(self, content, section_name):
        """提取特定章节的内容"""
        lines = content.split('\n')
        section_content = []
        in_section = False

        for line in lines:
            if section_name in line:
                in_section = True
                continue
            elif in_section:
                if line.startswith('#') or line.startswith('##'):
                    break
                if line.strip():
                    section_content.append(line.strip())

        return section_content[:3]  # 返回前3个要点

        # 统计公司提及频次
        company_counts = {}
        for company in all_companies:
            company_counts[company] = company_counts.get(company, 0) + 1

        # 获取最常提及的公司
        top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'total_videos_analyzed': total_videos,
            'sentiment_distribution': sentiment_counts,
            'most_mentioned_companies': [{'company': company, 'mentions': count} for company, count in top_companies],
            'total_unique_companies': len(set(all_companies)),
            'content_themes': self._extract_common_themes(individual_analyses)
        }

    def _extract_investment_themes(self, individual_analyses):
        """提取投资主题"""
        themes = []

        for analysis in individual_analyses:
            investment_thesis = analysis.get('investment_thesis', '')
            key_points = analysis.get('key_points', [])

            if investment_thesis:
                themes.append({
                    'video_index': analysis.get('video_index', 0),
                    'theme': investment_thesis,
                    'supporting_points': key_points
                })

        return themes

    def _generate_content_risk_assessment(self, individual_analyses):
        """生成内容风险评估"""
        risk_factors = []

        for analysis in individual_analyses:
            if analysis.get('sentiment') == '消极':
                risk_factors.append(f"视频{analysis.get('video_index', 0)}: {analysis.get('core_message', '')}")

        return {
            'identified_risks': risk_factors,
            'risk_level': '低' if len(risk_factors) < 2 else '中' if len(risk_factors) < 4 else '高',
            'risk_mitigation': [
                '多源信息验证',
                '关注市场实际表现',
                '持续监控相关动态',
                '保持理性分析态度'
            ]
        }

    def _generate_content_recommendations(self, individual_analyses):
        """生成内容建议"""
        positive_count = sum(1 for analysis in individual_analyses if analysis.get('sentiment') == '积极')
        total_count = len(individual_analyses)

        if positive_count / total_count > 0.6:
            overall_recommendation = '积极关注'
        elif positive_count / total_count > 0.4:
            overall_recommendation = '谨慎乐观'
        else:
            overall_recommendation = '保持观望'

        return {
            'overall_recommendation': overall_recommendation,
            'confidence_level': '中等',
            'reasoning': f'基于{total_count}个视频的内容分析，{positive_count}个视频表现积极观点',
            'action_items': [
                '关注提及频次较高的公司',
                '验证视频中的投资论点',
                '监控相关市场动态',
                '结合其他分析师观点'
            ]
        }

    def _extract_common_themes(self, individual_analyses):
        """提取共同主题"""
        all_themes = []

        for analysis in individual_analyses:
            themes = analysis.get('key_points', [])
            all_themes.extend(themes)

        # 简化版主题提取
        common_themes = list(set(all_themes))[:5]

        return common_themes
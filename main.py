from flask import Flask, render_template, request, jsonify, Response, send_file
from services.youtube_service import YouTubeService
from services.gemini_service import GeminiService
from services.stock_service import StockService
from services.report_service import ReportService
from services.cache_service import CacheService
from config.settings import Config
import os
import json
import time

app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')

app.config.from_object(Config)


youtube_service = YouTubeService()
gemini_service = GeminiService()
stock_service = StockService()
report_service = ReportService()
cache_service = CacheService()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """单视频分析"""
    if request.method == 'POST':
        return analyze_stream()
    
    return render_template('analyze.html')

@app.route('/analyze-stream', methods=['POST'])
def analyze_stream():
    """流式分析视频"""
    # 在请求上下文中获取数据
    data = request.get_json()
    video_url = data.get('video_url')
    analysis_type = data.get('analysis_type', 'content_only')
    date_range = data.get('date_range', 30)
    stock_symbol = data.get('stock_symbol', 'AAPL') if analysis_type == 'manual_stock' else None
    
    def generate_analysis():
        try:
            # 发送初始状态
            yield f"data: {json.dumps({'type': 'status', 'message': '开始分析...', 'progress': 0})}\n\n"
            time.sleep(0.1)
            
            # 创建日志回调函数
            def log_callback(message, log_type, streaming_text=None):
                log_data = {
                    'type': 'log',
                    'message': message,
                    'log_type': log_type,
                    'timestamp': int(time.time() * 1000)
                }
                if streaming_text:
                    log_data['streaming_text'] = streaming_text
                return f"data: {json.dumps(log_data)}\n\n"
            
            # 根据分析类型执行不同的逻辑
            if analysis_type == 'content_only':
                yield f"data: {json.dumps({'type': 'status', 'message': '仅分析视频内容和投资逻辑', 'progress': 10})}\n\n"
                
                # 流式分析视频
                for log_output in _analyze_content_only_stream(video_url, log_callback):
                    yield log_output
                    
            elif analysis_type == 'stock_extraction':
                yield f"data: {json.dumps({'type': 'status', 'message': '提取股票并分析数据', 'progress': 10})}\n\n"
                
                # 流式股票提取分析
                for log_output in _analyze_stock_extraction_stream(video_url, date_range, log_callback):
                    yield log_output
                    
            else:  # manual_stock
                yield f"data: {json.dumps({'type': 'status', 'message': '手动指定股票分析', 'progress': 10})}\n\n"
                
                for log_output in _analyze_manual_stock_stream(video_url, stock_symbol, date_range, log_callback):
                    yield log_output
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': str(e),
                'timestamp': int(time.time() * 1000)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return Response(generate_analysis(), mimetype='text/plain')

def _analyze_content_only_stream(video_url, log_callback):
    """流式分析纯内容"""
    try:
        # 检查缓存
        cache_result = cache_service.get_cached_analysis_result(video_url)
        if cache_result['found']:
            yield log_callback("发现缓存结果，直接返回", "info")
            yield f"data: {json.dumps({'type': 'status', 'message': '从缓存获取结果', 'progress': 100})}\n\n"
            
            # 从缓存获取完整的分析结果
            cached_analysis = cache_result['analysis_result']
            cached_analysis['from_cache'] = True
            yield f"data: {json.dumps(cached_analysis)}\n\n"
            return
        
        # 分析视频内容
        yield log_callback("开始分析视频内容...", "step")
        
        # 使用生成器处理分析（带日志）
        analysis_generator = gemini_service.analyze_video_with_logging(video_url, log_callback=log_callback)
        video_analysis = None
        
        for result in analysis_generator:
            if isinstance(result, str):  # 日志输出
                yield result
            else:  # 最终结果
                video_analysis = result
        
        yield f"data: {json.dumps({'type': 'status', 'message': '正在生成报告...', 'progress': 80})}\n\n"
        
        # 生成报告
        yield log_callback("生成内容分析报告...", "info")
        report = report_service.generate_content_only_report(video_analysis)
        
        yield f"data: {json.dumps({'type': 'status', 'message': '分析完成!', 'progress': 100})}\n\n"
        
        # 发送最终结果
        result = {
            'type': 'result',
            'success': True,
            'analysis_type': 'content_only',
            'report': report,
            'video_analysis': video_analysis,
            'from_cache': False
        }
        
        # 保存到缓存
        yield log_callback("保存分析结果到缓存...", "info")
        cache_key = cache_service.save_analysis_result(video_url, result)
        result['cache_key'] = cache_key
        
        # 保存下载用的Markdown报告
        metadata = {
            'analysis_type': 'content_only',
            'video_analysis': video_analysis
        }
        cache_service.save_download_report(cache_key, report, video_url, metadata)
        
        yield f"data: {json.dumps(result)}\n\n"
        
    except Exception as e:
        yield log_callback(f"分析失败: {str(e)}", "error")

def _analyze_stock_extraction_stream(video_url, date_range, log_callback):
    """流式股票提取分析"""
    try:
        # 检查缓存
        cache_result = cache_service.get_cached_analysis_result(video_url)
        if cache_result['found']:
            yield log_callback("发现缓存结果，直接返回", "info")
            yield f"data: {json.dumps({'type': 'status', 'message': '从缓存获取结果', 'progress': 100})}\n\n"
            
            # 从缓存获取完整的分析结果
            cached_analysis = cache_result['analysis_result']
            cached_analysis['from_cache'] = True
            yield f"data: {json.dumps(cached_analysis)}\n\n"
            return
        
        # 提取股票信息
        yield f"data: {json.dumps({'type': 'status', 'message': '正在提取股票信息...', 'progress': 20})}\n\n"
        
        # 使用生成器处理股票提取（带日志）
        extraction_generator = gemini_service.extract_stocks_from_video_with_logging(video_url, log_callback=log_callback)
        stock_extraction = None
        
        for result in extraction_generator:
            if isinstance(result, str):  # 日志输出
                yield result
            else:  # 最终结果
                stock_extraction = result
        
        if stock_extraction is None:
            yield log_callback("股票提取失败", "error")
            return
            
        extracted_stocks = stock_extraction.get('extracted_stocks', [])
        
        if not extracted_stocks:
            yield log_callback("视频中未检测到明确的股票信息", "error")
            return
        
        yield f"data: {json.dumps({'type': 'status', 'message': f'找到 {len(extracted_stocks)} 只股票', 'progress': 40})}\n\n"
        
        # 分析视频内容
        yield log_callback("分析视频内容...", "step")
        
        analysis_generator = gemini_service.analyze_video_with_logging(video_url, log_callback=log_callback)
        video_analysis = None
        
        for result in analysis_generator:
            if isinstance(result, str):  # 日志输出
                yield result
            else:  # 最终结果
                video_analysis = result
        
        yield f"data: {json.dumps({'type': 'status', 'message': '获取股票数据...', 'progress': 60})}\n\n"
        
        # 获取股票数据
        stock_data_list = []
        for i, stock in enumerate(extracted_stocks):
            try:
                yield log_callback(f"获取 {stock['symbol']} 股票数据...", "info")
                stock_data = stock_service.get_stock_data(stock['symbol'], date_range)
                stock_data['name'] = stock.get('name', '')
                stock_data_list.append(stock_data)
                progress = 60 + (i + 1) * 10 / len(extracted_stocks)
                yield f"data: {json.dumps({'type': 'status', 'message': f'已获取 {i+1}/{len(extracted_stocks)} 股票数据', 'progress': progress})}\n\n"
            except Exception as e:
                yield log_callback(f"获取股票 {stock['symbol']} 数据失败: {str(e)}", "warning")
        
        yield f"data: {json.dumps({'type': 'status', 'message': '生成综合分析报告...', 'progress': 80})}\n\n"
        
        # 生成报告
        report = report_service.generate_stock_extraction_report(
            video_analysis, stock_data_list, extracted_stocks
        )
        
        yield f"data: {json.dumps({'type': 'status', 'message': '分析完成!', 'progress': 100})}\n\n"
        
        # 发送最终结果
        result = {
            'type': 'result',
            'success': True,
            'analysis_type': 'stock_extraction',
            'report': report,
            'video_analysis': video_analysis,
            'extracted_stocks': extracted_stocks,
            'stock_data': stock_data_list,
            'from_cache': False
        }
        
        # 保存到缓存
        yield log_callback("保存分析结果到缓存...", "info")
        cache_key = cache_service.save_analysis_result(video_url, result)
        result['cache_key'] = cache_key
        
        # 保存下载用的Markdown报告
        metadata = {
            'analysis_type': 'stock_extraction',
            'video_analysis': video_analysis,
            'extracted_stocks': extracted_stocks,
            'stock_data': stock_data_list
        }
        cache_service.save_download_report(cache_key, report, video_url, metadata)
        
        yield f"data: {json.dumps(result)}\n\n"
        
    except Exception as e:
        yield log_callback(f"分析失败: {str(e)}", "error")

def _analyze_manual_stock_stream(video_url, stock_symbol, date_range, log_callback):
    """流式手动股票分析"""
    try:
        # 检查缓存（结合视频URL和股票代码）
        cache_urls = f"{video_url}|{stock_symbol}|{date_range}"
        cache_result = cache_service.get_cached_analysis_result(cache_urls)
        if cache_result['found']:
            yield log_callback("发现缓存结果，直接返回", "info")
            yield f"data: {json.dumps({'type': 'status', 'message': '从缓存获取结果', 'progress': 100})}\n\n"
            
            # 从缓存获取完整的分析结果
            cached_analysis = cache_result['analysis_result']
            cached_analysis['from_cache'] = True
            yield f"data: {json.dumps(cached_analysis)}\n\n"
            return
        
        # 分析视频
        yield f"data: {json.dumps({'type': 'status', 'message': '分析视频内容...', 'progress': 30})}\n\n"
        
        analysis_generator = gemini_service.analyze_video_with_logging(video_url, log_callback=log_callback)
        video_analysis = None
        
        for result in analysis_generator:
            if isinstance(result, str):  # 日志输出
                yield result
            else:  # 最终结果
                video_analysis = result
        
        yield f"data: {json.dumps({'type': 'status', 'message': f'获取 {stock_symbol} 股票数据...', 'progress': 60})}\n\n"
        
        # 获取股票数据
        yield log_callback(f"获取 {stock_symbol} 股票数据...", "info")
        stock_data = stock_service.get_stock_data(stock_symbol, date_range)
        
        yield f"data: {json.dumps({'type': 'status', 'message': '生成投资分析报告...', 'progress': 80})}\n\n"
        
        # 生成报告
        yield log_callback("生成投资分析报告...", "info")
        report = report_service.generate_report(video_analysis, stock_data)
        
        yield f"data: {json.dumps({'type': 'status', 'message': '分析完成!', 'progress': 100})}\n\n"
        
        # 发送最终结果
        result = {
            'type': 'result',
            'success': True,
            'analysis_type': 'manual_stock',
            'report': report,
            'video_analysis': video_analysis,
            'stock_data': stock_data,
            'from_cache': False
        }
        
        # 保存到缓存
        yield log_callback("保存分析结果到缓存...", "info")
        cache_key = cache_service.save_analysis_result(cache_urls, result)
        result['cache_key'] = cache_key
        
        # 保存下载用的Markdown报告
        metadata = {
            'analysis_type': 'manual_stock',
            'video_analysis': video_analysis,
            'stock_data': stock_data,
            'stock_symbol': stock_symbol,
            'date_range': date_range
        }
        cache_service.save_download_report(cache_key, report, cache_urls, metadata)
        
        yield f"data: {json.dumps(result)}\n\n"
        
    except Exception as e:
        yield log_callback(f"分析失败: {str(e)}", "error")

@app.route('/batch-analyze', methods=['GET', 'POST'])
def batch_analyze():
    """批量视频分析"""
    if request.method == 'POST':
        try:
            data = request.json
            if not data:
                return jsonify({
                    'success': False,
                    'error': '请求数据不能为空'
                }), 400
            
            channel_id = data.get('channel_id')
            video_count = min(data.get('video_count', 5), 10)  # 限制最多10个视频
            
            # 获取频道视频
            channel_result = youtube_service.get_channel_videos(channel_id, video_count)
            videos = channel_result['videos']
            
            # 限制视频数量为10个
            videos = videos[:10]
            
            # 提取视频URL列表
            video_urls = [video.get('url') for video in videos if video.get('url')]
            
            if not video_urls:
                raise Exception("未获取到有效的视频URL")
            
            # 检查缓存
            cache_result = cache_service.get_cached_analysis_result(video_urls)
            if cache_result['found']:
                cached_result = cache_result['analysis_result']
                cached_result['from_cache'] = True
                return jsonify(cached_result)
            
            # 使用Gemini批量分析视频
            batch_analysis_generator = gemini_service.analyze_batch_videos(video_urls)
            batch_analysis = None
            
            for result in batch_analysis_generator:
                if not isinstance(result, str):  # 最终结果
                    batch_analysis = result
                    break
            
            if not batch_analysis:
                raise Exception("批量分析失败")
            
            # 生成批量内容分析报告
            report = report_service.generate_batch_content_report(batch_analysis)
            
            # 构建返回结果
            result = {
                'success': True,
                'report': report,
                'video_count': len(videos),
                'from_cache': False
            }
            
            # 保存到缓存
            cache_key = cache_service.save_analysis_result(video_urls, result)
            result['cache_key'] = cache_key
            
            # 保存下载用的Markdown报告
            metadata = {
                'analysis_type': 'batch_content',
                'batch_analysis': batch_analysis,
                'video_count': len(videos)
            }
            cache_service.save_download_report(cache_key, report, video_urls, metadata)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return render_template('batch_analyze.html')

@app.route('/api/channel-videos')
def get_channel_videos():
    """获取频道视频API"""
    channel_id = request.args.get('channel_id')
    count = request.args.get('count', 20, type=int)
    next_token = request.args.get('next_token', '')
    
    try:
        result = youtube_service.get_channel_videos(channel_id, count, next_token)
        return jsonify({
            'success': True,
            'videos': result['videos'],
            'next_token': result['next_token'],
            'has_more': result['has_more'],
            'count': len(result['videos'])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch-analyze-selected', methods=['POST'])
def batch_analyze_selected():
    """批量分析选定的视频"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        selected_videos = data.get('selected_videos', [])
        
        if not selected_videos:
            return jsonify({
                'success': False,
                'error': '请选择要分析的视频'
            }), 400
        
        if len(selected_videos) > 10:
            return jsonify({
                'success': False,
                'error': '最多只能选择10个视频进行分析'
            }), 400
        
        # 提取视频URL列表
        video_urls = [video.get('url') for video in selected_videos if video.get('url')]

        print(video_urls)
        
        if not video_urls:
            raise Exception("未获取到有效的视频URL")
        
        # 检查缓存
        cache_result = cache_service.get_cached_analysis_result(video_urls)
        if cache_result['found']:
            cached_result = cache_result['analysis_result']
            cached_result['from_cache'] = True
            return jsonify(cached_result)
        
        # 使用Gemini批量分析视频
        batch_analysis_generator = gemini_service.analyze_batch_videos(video_urls)
        batch_analysis = None
        
        for result in batch_analysis_generator:
            if not isinstance(result, str):  # 最终结果
                batch_analysis = result
                break
        
        if not batch_analysis:
            raise Exception("批量分析失败")
        
        # 生成批量内容分析报告
        report = report_service.generate_batch_content_report(batch_analysis)
        
        # 构建返回结果
        result = {
            'success': True,
            'report': report,
            'video_count': len(selected_videos),
            'selected_videos': selected_videos,
            'from_cache': False
        }
        
        # 保存到缓存
        cache_key = cache_service.save_analysis_result(video_urls, result)
        result['cache_key'] = cache_key
        
        # 保存下载用的Markdown报告
        metadata = {
            'analysis_type': 'batch_selected',
            'batch_analysis': batch_analysis,
            'selected_videos': selected_videos,
            'video_count': len(selected_videos)
        }
        cache_service.save_download_report(cache_key, report, video_urls, metadata)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download-markdown/<cache_key>')
def download_markdown(cache_key):
    """下载Markdown报告"""
    try:
        # 获取Markdown文件路径
        markdown_file = cache_service.get_markdown_file_path(cache_key)
        
        if not os.path.exists(markdown_file):
            return jsonify({
                'success': False,
                'error': "缓存文件不存在"
            }), 404
        
        # 生成下载文件名
        filename = f"youtube_analysis_{cache_key[:8]}.md"
        
        return send_file(
            markdown_file,
            as_attachment=True,
            download_name=filename,
            mimetype='text/markdown'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Markdown下载失败: {str(e)}"
        }), 500

@app.route('/api/stock-data')
def get_stock_data():
    """获取股票数据API"""
    symbol = request.args.get('symbol', 'AAPL')
    days = request.args.get('days', 30, type=int)
    
    try:
        data = stock_service.get_stock_data(symbol, days)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=15000)
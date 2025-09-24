from flask import Flask, render_template, request, jsonify, Response, send_file
from services.youtube_service import YouTubeService
from services.gemini_service import GeminiService
from services.stock_service import StockService
from services.report_service import ReportService
from services.cache_service import CacheService
from services.record_service import RecordService
from services.chart_service import ChartService
from config.settings import Config
from utils.time_utils import utc_str_to_bj
import os
import json
import time
import re

app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')

app.config.from_object(Config)


youtube_service = YouTubeService()
gemini_service = GeminiService()
stock_service = StockService()
report_service = ReportService()
cache_service = CacheService()
chart_service = ChartService()
record_service = RecordService()

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
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    stock_symbol = data.get('stock_symbol', 'AAPL') if analysis_type == 'manual_stock' else None
    report_language = data.get('report_language', 'en')
    
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
                for log_output in _analyze_content_only_stream(video_url, start_date, end_date, log_callback, report_language):
                    yield log_output
                    
            elif analysis_type == 'stock_extraction':
                yield f"data: {json.dumps({'type': 'status', 'message': '提取股票并分析数据', 'progress': 10})}\n\n"
                
                # 流式股票提取分析
                for log_output in _analyze_stock_extraction_stream(video_url, start_date, end_date, log_callback, report_language):
                    yield log_output
                    
            else:  # manual_stock
                yield f"data: {json.dumps({'type': 'status', 'message': '手动指定股票分析', 'progress': 10})}\n\n"
                
                for log_output in _analyze_manual_stock_stream(video_url, stock_symbol, start_date, end_date, log_callback, report_language):
                    yield log_output
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': str(e),
                'timestamp': int(time.time() * 1000)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return Response(generate_analysis(), mimetype='text/plain')

def _analyze_content_only_stream(video_url,start_date, end_date,  log_callback, report_language='en'):
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
            
            # 重要：设置cache_key
            cache_key = cache_service._generate_cache_key(video_url)
            cached_analysis['cache_key'] = cache_key
            print(f"从缓存返回结果，设置cache_key: {cache_key}")
            
            yield f"data: {json.dumps(cached_analysis)}\n\n"
            return
        
        # 分析视频内容
        yield log_callback("开始分析视频内容...", "step")
        
        # 使用生成器处理分析（带日志）
        analysis_generator = gemini_service.analyze_video_with_logging(video_url, log_callback=log_callback, language=report_language)
        video_analysis = None
        
        for result in analysis_generator:
            if isinstance(result, str):  # 日志输出
                yield result
            else:  # 最终结果
                video_analysis = result
        
        yield f"data: {json.dumps({'type': 'status', 'message': '正在生成报告...', 'progress': 80})}\n\n"
        
        # 生成报告
        yield log_callback("生成内容分析报告...", "info")
        report = report_service.generate_content_only_report(video_analysis, language=report_language)
        
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
        
        # 写入分析记录（单视频分析）
        try:
            record_service.add_record(
                video_url=video_url,
                channel_name=None,
                cache_key=cache_key,
                analysis_type='单视频分析',
                start_date=start_date,
                end_date=end_date,
                report_language=report_language,
            )
        except Exception as _:
            # 忽略记录失败，避免影响主流程
            pass
        
        yield f"data: {json.dumps(result)}\n\n"
        
    except Exception as e:
        yield log_callback(f"分析失败: {str(e)}", "error")

def _analyze_stock_extraction_stream(video_url, start_date, end_date, log_callback, report_language='en'):
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
            
            # 重要：设置cache_key
            cache_key = cache_service._generate_cache_key(video_url)
            cached_analysis['cache_key'] = cache_key
            print(f"从缓存返回结果，设置cache_key: {cache_key}")
            
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
        
        analysis_generator = gemini_service.analyze_video_with_logging(video_url, log_callback=log_callback, language=report_language)
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
                stock_data = stock_service.get_stock_data_by_date_range(stock['symbol'], start_date, end_date)
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
        
        # 写入分析记录（单视频分析-股票提取）
        try:
            record_service.add_record(
                video_url=video_url,
                channel_name=None,
                cache_key=cache_key,
                analysis_type='单视频分析',
                start_date=start_date,
                end_date=end_date,
                report_language=report_language,
            )
        except Exception as _:
            pass

        yield f"data: {json.dumps(result)}\n\n"
        
    except Exception as e:
        yield log_callback(f"分析失败: {str(e)}", "error")

def _analyze_manual_stock_stream(video_url, stock_symbol, start_date, end_date, log_callback, report_language='en'):
    """流式手动股票分析"""
    try:
        # 检查缓存（结合视频URL和股票代码）
        cache_urls = f"{video_url}|{stock_symbol}|{start_date}|{end_date}"
        cache_result = cache_service.get_cached_analysis_result(cache_urls)
        if cache_result['found']:
            yield log_callback("发现缓存结果，直接返回", "info")
            yield f"data: {json.dumps({'type': 'status', 'message': '从缓存获取结果', 'progress': 100})}\n\n"
            
            # 从缓存获取完整的分析结果
            cached_analysis = cache_result['analysis_result']
            cached_analysis['from_cache'] = True
            
            # 重要：设置cache_key
            cache_key = cache_service._generate_cache_key(cache_urls)
            cached_analysis['cache_key'] = cache_key
            print(f"从缓存返回结果，设置cache_key: {cache_key}")
            
            yield f"data: {json.dumps(cached_analysis)}\n\n"
            return
        
        # 分析视频
        yield f"data: {json.dumps({'type': 'status', 'message': '分析视频内容...', 'progress': 30})}\n\n"
        
        analysis_generator = gemini_service.analyze_video_with_logging(video_url, log_callback=log_callback, language=report_language)
        video_analysis = None
        
        for result in analysis_generator:
            if isinstance(result, str):  # 日志输出
                yield result
            else:  # 最终结果
                video_analysis = result
        
        yield f"data: {json.dumps({'type': 'status', 'message': f'获取 {stock_symbol} 股票数据...', 'progress': 60})}\n\n"
        
        # 获取股票数据
        yield log_callback(f"获取 {stock_symbol} 股票数据...", "info")
        stock_data = stock_service.get_stock_data_by_date_range(stock_symbol, start_date, end_date)
        
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
            'start_date': start_date,
            'end_date': end_date
        }
        cache_service.save_download_report(cache_key, report, cache_urls, metadata)
        
        # 写入分析记录（单视频分析）
        try:
            record_service.add_record(
                video_url=video_url,
                channel_name=None,
                cache_key=cache_key,
                analysis_type='单视频分析',
                start_date=start_date,
                end_date=end_date,
                report_language=report_language,
            )
        except Exception as _:
            pass
        
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
            report_language = data.get('report_language', 'en')
            
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
            report = report_service.generate_batch_content_report(batch_analysis, language=report_language)
            
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
            
            # 批量分析不写入记录（按需保留缓存与报告）
            
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

@app.route('/api/analysis-history')
def analysis_history():
    """查询分析历史（倒序）。支持参数：limit（默认50）。"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        records = record_service.list_records(limit=limit)
        # 将UTC时间转换为北京时间
        for rec in records:
            if isinstance(rec, dict) and 'created_at' in rec:
                rec['created_at'] = utc_str_to_bj(rec.get('created_at'))
        return jsonify({
            'success': True,
            'data': records,
            'count': len(records)
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
        report_language = data.get('report_language', 'en')
        
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
        batch_analysis_generator = gemini_service.analyze_batch_videos(video_urls, language=report_language)
        batch_analysis = None
        
        for result in batch_analysis_generator:
            if not isinstance(result, str):  # 最终结果
                batch_analysis = result
                break
        
        if not batch_analysis:
            raise Exception("批量分析失败")
        
        # 生成批量内容分析报告
        report = report_service.generate_batch_content_report(batch_analysis, language=report_language)
        
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
        
        # 批量分析（选定）不写入记录（按需保留缓存与报告）

        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download-pdf/<cache_key>')
def download_pdf(cache_key):
    """下载PDF报告"""
    try:
        # 从缓存获取分析结果
        cached_data = cache_service.get_analysis_result_by_key(cache_key)
        if not cached_data:
            return jsonify({
                'success': False,
                'error': "缓存文件不存在"
            }), 404
        
        # 获取视频URL列表
        video_urls = cache_service.get_video_urls_by_cache_key(cache_key)
        if not video_urls:
            # 如果无法获取URL，使用占位符
            video_urls = ["视频URL获取失败"]
        
        # 生成PDF文件
        pdf_file = report_service.generate_pdf_report(cache_key, cached_data, video_urls)
        
        if not os.path.exists(pdf_file):
            return jsonify({
                'success': False,
                'error': "PDF生成失败"
            }), 500
        
        # 生成下载文件名
        filename = f"youtube_analysis_{cache_key[:8]}.pdf"
        
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"PDF下载失败: {str(e)}"
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

@app.route('/api/extract-stocks-chart', methods=['POST'])
def extract_stocks_chart():
    """提取股票信息并生成走势图分析"""
    try:
        data = request.get_json()
        cache_key = data.get('cache_key')
        # 新增：从请求中获取日期范围
        request_start_date = data.get('start_date')
        request_end_date = data.get('end_date')
        
        print(f"收到股票提取请求，cache_key: {cache_key}")
        print(f"请求的日期范围: {request_start_date} 到 {request_end_date}")
        
        if not cache_key:
            print("错误：缺少cache_key参数")
            return jsonify({
                'success': False,
                'error': '缺少cache_key参数'
            }), 400
        
        # 从缓存获取分析结果
        print(f"尝试从缓存获取数据，cache_key: {cache_key}")
        cached_data = cache_service.get_analysis_result_by_key(cache_key)
        print(f"缓存数据获取结果: {cached_data is not None}")
        if not cached_data:
            print(f"错误：未找到cache_key {cache_key} 对应的分析结果")
            # 列出所有可用的缓存文件进行调试
            import os
            cache_dir = cache_service.analysis_cache_dir
            if os.path.exists(cache_dir):
                cache_files = os.listdir(cache_dir)
                print(f"可用的缓存文件: {cache_files}")
            else:
                print(f"缓存目录不存在: {cache_dir}")
            
            return jsonify({
                'success': False,
                'error': '未找到对应的分析结果'
            }), 404
        
        # 提取股票信息
        extracted_stocks = extract_stocks_from_report(cached_data)
        
        if not extracted_stocks:
            return jsonify({
                'success': False,
                'error': '未能从报告中提取到有效的股票信息'
            }), 400
        
        # 确定使用的日期范围：优先使用请求中的日期，然后是缓存中的日期，最后使用默认值
        start_date = request_start_date
        end_date = request_end_date
        
        # 如果请求中没有日期范围，尝试从缓存的股票数据中获取
        if not start_date or not end_date:
            stock_data = cached_data.get('stock_data')
            if stock_data:
                if isinstance(stock_data, list) and len(stock_data) > 0:
                    # 多股票数据
                    first_stock = stock_data[0]
                    start_date = first_stock.get('start_date')
                    end_date = first_stock.get('end_date')
                elif isinstance(stock_data, dict):
                    # 单股票数据
                    start_date = stock_data.get('start_date')
                    end_date = stock_data.get('end_date')
        
        # 如果仍然没有找到日期范围，使用默认的30天前到今天
        if not start_date or not end_date:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            print(f"🔧 使用默认日期范围: {start_date} 到 {end_date}")
        else:
            print(f"📅 使用的日期范围: {start_date} 到 {end_date}")
            if request_start_date and request_end_date:
                print("   (来源: 用户请求)")
            else:
                print("   (来源: 缓存数据)")
        
        # 生成股票图表
        stock_charts = []
        for stock in extracted_stocks:
            chart_result = chart_service.generate_stock_chart_by_date_range(stock['symbol'], start_date, end_date)
            # 包含所有结果，不论成功还是失败
            stock_charts.append(chart_result)
            
            # 打印调试信息
            if chart_result.get('success'):
                print(f"✅ 成功生成 {stock['symbol']} 的图表")
            else:
                print(f"❌ 生成 {stock['symbol']} 图表失败: {chart_result.get('error', '未知错误')}")
        
        # 生成准确性分析
        accuracy_analysis = generate_accuracy_analysis(extracted_stocks, stock_charts, cached_data)
        
        # 清理旧图表
        chart_service.cleanup_old_charts()
        
        return jsonify({
            'success': True,
            'data': {
                'extracted_stocks': extracted_stocks,
                'stock_charts': stock_charts,
                'accuracy_analysis': accuracy_analysis
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'股票提取和图表生成失败: {str(e)}'
        }), 500

def extract_stocks_from_report(cached_data):
    """使用AI智能分析从分析报告中提取股票信息"""
    try:
        print(f"🤖 开始使用AI智能提取股票信息")
        
        # 获取报告内容
        report = cached_data.get('report', {})
        video_analysis = cached_data.get('video_analysis', {})
        
        # 构建完整的分析内容
        analysis_content = ""
        
        if report.get('raw_markdown_content'):
            analysis_content = report['raw_markdown_content']
        elif video_analysis.get('summary'):
            analysis_content = video_analysis['summary']
        elif report.get('executive_summary'):
            analysis_content = report['executive_summary']
        else:
            print("❌ 未找到可分析的内容")
            return []
        
        print(f"📊 准备分析的内容长度: {len(analysis_content)}")
        
        # 限制内容长度，避免超过API限制
        if len(analysis_content) > 10000:
            analysis_content = analysis_content[:10000] + "..."
            print(f"📊 内容过长，截取前10000字符")
        
        # 使用Gemini AI分析提取股票信息
        extracted_stocks = analyze_stocks_with_ai(analysis_content)
        
        if extracted_stocks:
            print(f"✅ AI成功提取到 {len(extracted_stocks)} 只股票")
            for stock in extracted_stocks:
                print(f"  📈 {stock['symbol']} - {stock['name']} ({stock['confidence']})")
        else:
            print("❌ AI未能提取到有效的股票信息")
        
        return extracted_stocks
        
    except Exception as e:
        print(f"❌ AI股票提取失败: {e}")
        return []


def analyze_stocks_with_ai(content):
    """使用AI分析内容并提取股票信息"""
    try:
        from services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        # 构建AI分析提示词
        prompt = f"""
作为专业的金融分析师，请仔细分析以下投资报告内容，提取其中提到的所有美股股票信息。

**分析内容：**
{content}

**请按照以下JSON格式返回结果，只返回JSON，不要添加任何其他文字：**

{{
    "stocks": [
        {{
            "symbol": "股票代码(如AAPL)",
            "name": "公司全名(如Apple Inc.)",
            "confidence": "提取置信度(high/medium/low)",
            "recommendation": "投资建议(买入/卖出/持有/无明确建议)",
            "context": "在报告中的相关描述(不超过100字)"
        }}
    ]
}}

**重要要求：**
1. 只提取在美国交易所(NYSE, NASDAQ)交易的股票
2. 股票代码必须是标准的1-5位大写字母格式
3. confidence根据在报告中的重要程度设置：详细分析的为high，简单提及的为medium，模糊提及的为low
4. recommendation根据报告的实际建议设置，如果没有明确建议就写"无明确建议"
5. 如果没有找到任何股票，返回空的stocks数组
6. 最多返回10只股票
"""

        # 调用AI服务
        response = gemini_service.generate_text(prompt)
        
        if not response or not response.get('success') or not response.get('summary'):
            print("❌ AI返回空响应")
            return []
        
        response_text = response['summary'].strip()
        print(f"🤖 AI原始响应: {response_text[:200]}...")
        
        # 提取JSON部分
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            print("❌ AI响应中未找到JSON格式")
            return []
        
        json_str = response_text[json_start:json_end]
        
        try:
            result = json.loads(json_str)
            stocks = result.get('stocks', [])
            
            # 验证和清理结果
            valid_stocks = []
            for stock in stocks:
                if (stock.get('symbol') and stock.get('name') and 
                    isinstance(stock.get('symbol'), str) and 
                    stock['symbol'].isupper() and 
                    len(stock['symbol']) <= 5):
                    valid_stocks.append({
                        'symbol': stock['symbol'],
                        'name': stock['name'],
                        'confidence': stock.get('confidence', 'medium'),
                        'recommendation': stock.get('recommendation', '无明确建议')
                    })
            
            return valid_stocks[:10]  # 最多返回10只股票
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"尝试解析的内容: {json_str}")
            return []
            
    except Exception as e:
        print(f"❌ AI分析异常: {e}")
        return []

def generate_accuracy_analysis(extracted_stocks, stock_charts, cached_data):
    """生成准确性分析"""
    try:
        # 从不同字段获取报告摘要
        report = cached_data.get('report', {})
        video_analysis = cached_data.get('video_analysis', {})
        
        # 尝试获取最相关的报告内容
        report_summary = ""
        
        # 优先级：executive_summary -> raw_markdown_content -> video_analysis.summary
        if report.get('executive_summary'):
            report_summary = report['executive_summary']
        elif report.get('raw_markdown_content'):
            # 如果是Markdown内容，提取前4000字符作为摘要
            raw_content = report['raw_markdown_content']
            report_summary = raw_content[:4000] + "..." if len(raw_content) > 4000 else raw_content
        elif video_analysis.get('summary'):
            report_summary = video_analysis['summary'][:4000] + "..." if len(video_analysis.get('summary', '')) > 4000 else video_analysis.get('summary', '')
        else:
            report_summary = "无可用的报告摘要"
        
        # 构建分析提示词，优化搜索工具使用
        analysis_prompt = f"""
作为专业的投资分析师，请分析以下YouTube视频投资建议的准确性。

**重要提示：你拥有实时搜索功能，请主动使用搜索工具获取以下信息：**
1. 搜索每只股票的最新财务数据、新闻和分析师评级
2. 搜索相关行业的最新趋势和市场动态
3. 搜索宏观经济环境对这些股票的影响
4. 搜索近期相关的重大新闻事件

## 待分析的股票信息：
{json.dumps(extracted_stocks, ensure_ascii=False, indent=2)}

## 当前股票表现数据：
{json.dumps([{
    'symbol': chart['symbol'],
    'current_price': chart.get('current_price'),
    'price_change': chart.get('price_change')
} for chart in stock_charts if chart.get('success')], ensure_ascii=False, indent=2)}

## 原始投资建议摘要：
{report_summary}

**分析任务：**
请使用搜索工具获取实时信息，然后从以下维度进行专业分析：

1. **股票选择合理性** - 基于最新市场数据和分析师观点评估选股逻辑
2. **投资建议准确性** - 对比建议与最新市场表现和专业分析
3. **市场时机判断** - 评估建议的时机是否符合当前市场环境
4. **风险评估准确性** - 分析风险预警是否充分和准确
5. **整体准确性评分** - 综合以上因素给出1-10分评分

**输出要求：**
- 开头直接给出评分："综合准确性评分: X.X/10"
- 详细说明评分依据，引用搜索到的最新信息
- 提供基于最新数据的改进建议
- 使用简洁专业的中文表述

请开始分析，记住要充分利用搜索工具获取最新、最准确的市场信息。
        """
        
        print("开始调用Gemini进行准确性分析...")
        print(f"使用的报告摘要长度: {len(report_summary)}")
        
        # 调用Gemini进行分析
        gemini_result = gemini_service.generate_text(analysis_prompt)
        
        if gemini_result.get('success'):
            analysis_content = gemini_result.get('summary', '')
            
            # 尝试从结果中提取评分
            score_match = re.search(r'(\d+(?:\.\d+)?)/10', analysis_content)
            overall_score = f"{score_match.group(1)}/10" if score_match else "7.0/10"
            
            # 提取关键发现（简化版）
            key_findings = []
            if '股票选择' in analysis_content:
                key_findings.append('已分析股票选择合理性')
            if '投资建议' in analysis_content:
                key_findings.append('已评估投资建议准确性')
            if '分析逻辑' in analysis_content:
                key_findings.append('已审查分析逻辑严谨性')
            
            return {
                'overall_score': overall_score,
                'analysis_summary': analysis_content,
                'key_findings': key_findings if key_findings else ['综合分析已完成'],
                'market_context': '基于当前市场数据进行分析'
            }
        else:
            print(f"Gemini分析失败: {gemini_result.get('error')}")
            return generate_fallback_accuracy_analysis(extracted_stocks, stock_charts)
        
    except Exception as e:
        print(f"准确性分析失败: {e}")
        return generate_fallback_accuracy_analysis(extracted_stocks, stock_charts)

def generate_fallback_accuracy_analysis(extracted_stocks, stock_charts):
    """生成备用的准确性分析"""
    try:
        total_stocks = len(extracted_stocks)
        positive_performance = sum(1 for chart in stock_charts 
                                 if chart.get('success') and chart.get('price_change', 0) > 0)
        
        # 基于股票表现计算简单评分
        if total_stocks > 0:
            performance_ratio = positive_performance / total_stocks
            base_score = 5.0 + (performance_ratio * 3.0)  # 5-8分区间
        else:
            base_score = 6.0
            
        return {
            'overall_score': f"{base_score:.1f}/10",
            'analysis_summary': f"""
基于数据分析的准确性评估：

**股票选择分析：**
- 共提取到 {total_stocks} 只股票进行分析
- 其中 {positive_performance} 只股票表现为正收益

**投资建议准确性：**
- 正收益比例: {positive_performance}/{total_stocks} ({performance_ratio*100:.1f}%)
- 整体投资建议{('较为准确' if performance_ratio > 0.6 else '有待改进')}

**综合评估：**
投资建议在当前市场环境下表现{'良好' if performance_ratio > 0.5 else '一般'}，
建议投资者结合个人风险承受能力和市场环境做出决策。
            """.strip(),
            'key_findings': [
                f'分析了{total_stocks}只股票的表现',
                f'{positive_performance}只股票获得正收益',
                '提供了基于数据的客观评估'
            ],
            'market_context': '基于实际股票价格数据进行分析'
        }
        
    except Exception as e:
        return {
            'overall_score': 'N/A',
            'analysis_summary': f'无法生成准确性分析: {str(e)}',
            'key_findings': ['分析生成失败'],
            'market_context': '数据不足'
        }

@app.route('/api/analyze-channel-first-video', methods=['POST'])
def analyze_channel_first_video():
    """外部API: 分析指定频道的第一个视频"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        channel_name = data.get('channel_name')
        report_language = data.get('report_language', 'en')
        
        if not channel_name:
            return jsonify({
                'success': False,
                'error': '缺少channel_name参数'
            }), 400
        
        # 获取频道的第一个视频
        channel_result = youtube_service.get_channel_videos(channel_name, 1)
        videos = channel_result['videos']
        
        if not videos:
            return jsonify({
                'success': False,
                'error': f'频道 {channel_name} 未找到视频'
            }), 404
        
        first_video = videos[0]
        video_url = first_video.get('url')
        
        if not video_url:
            return jsonify({
                'success': False,
                'error': '获取到的视频URL无效'
            }), 400
        
        # 检查缓存，如果已有分析结果则直接返回成功
        cache_result = cache_service.get_cached_analysis_result(video_url)
        if cache_result['found']:
            return jsonify({
                'success': True,
                'message': f'频道 {channel_name} 的第一个视频已分析过',
                'video_title': first_video.get('title', ''),
                'video_url': video_url,
                'from_cache': True,
                'cache_key': cache_service._generate_cache_key(video_url)
            })
        
        # 进行视频分析（仅内容分析）
        analysis_generator = gemini_service.analyze_video_with_logging(video_url, language=report_language)
        video_analysis = None
        
        for result in analysis_generator:
            if not isinstance(result, str):  # 最终结果
                video_analysis = result
                break
        
        if not video_analysis:
            return jsonify({
                'success': False,
                'error': '视频分析失败'
            }), 500
        
        # 生成报告
        report = report_service.generate_content_only_report(video_analysis, language=report_language)
        
        # 构建分析结果
        result = {
            'type': 'result',
            'success': True,
            'analysis_type': 'content_only',
            'report': report,
            'video_analysis': video_analysis,
            'from_cache': False
        }
        
        # 保存到缓存
        cache_key = cache_service.save_analysis_result(video_url, result)
        
        # 保存下载用的Markdown报告
        metadata = {
            'analysis_type': 'content_only',
            'video_analysis': video_analysis
        }
        cache_service.save_download_report(cache_key, report, video_url, metadata)
        
        # 写入分析记录（单视频分析-频道首个视频）
        try:
            record_service.add_record(
                video_url=video_url,
                channel_name=channel_name,
                cache_key=cache_key,
                analysis_type='单视频分析',
                start_date=None,
                end_date=None,
                report_language=report_language,
            )
        except Exception as _:
            pass

        return jsonify({
            'success': True,
            'message': f'频道 {channel_name} 的第一个视频分析完成',
            'video_title': first_video.get('title', ''),
            'video_url': video_url,
            'from_cache': False,
            'cache_key': cache_key
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'分析失败: {str(e)}'
        }), 500

@app.route('/api/clear-cache/<cache_key>', methods=['DELETE'])
def clear_cache(cache_key):
    """清理指定cache_key的缓存文件"""
    try:
        # 定义各种缓存文件路径
        analysis_cache_file = os.path.join('cache', 'analysis', f'{cache_key}.json')
        pdf_cache_file = os.path.join('cache', 'pdf', f'{cache_key}.pdf')
        download_cache_file = os.path.join('cache', 'download', f'{cache_key}.md')
        
        # 记录删除的文件
        deleted_files = []
        
        # 删除分析缓存文件
        if os.path.exists(analysis_cache_file):
            os.remove(analysis_cache_file)
            deleted_files.append('分析缓存')
        
        # 删除PDF文件
        if os.path.exists(pdf_cache_file):
            os.remove(pdf_cache_file)
            deleted_files.append('PDF报告')
        
        # 删除下载缓存文件
        if os.path.exists(download_cache_file):
            os.remove(download_cache_file)
            deleted_files.append('下载缓存')
        # 同步删除数据库记录
        deleted_db = 0
        try:
            deleted_db = record_service.delete_by_cache_key(cache_key)
        except Exception as _:
            pass
        
        # 组装响应
        if deleted_files or deleted_db:
            details = []
            if deleted_files:
                details.append(f"文件: {', '.join(deleted_files)}")
            if deleted_db:
                details.append(f"数据库记录: {deleted_db} 条")
            return jsonify({
                'success': True,
                'message': f"成功清理 { '；'.join(details) }" if details else '已完成清理',
                'deleted_files': deleted_files,
                'deleted_db': deleted_db
            })
        else:
            return jsonify({
                'success': False,
                'message': '未找到相关缓存文件或数据库记录'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'清理缓存失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=15000)

from flask import Flask, render_template, request, jsonify
from services.youtube_service import YouTubeService
from services.gemini_service import GeminiService
from services.stock_service import StockService
from services.report_service import ReportService
from config.settings import Config
import os

app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')

app.config.from_object(Config)


youtube_service = YouTubeService()
gemini_service = GeminiService()
stock_service = StockService()
report_service = ReportService()

@app.route('/')
def index():
    """;u"""
    return render_template('index.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Ƒ�ub"""
    if request.method == 'POST':
        try:
            data = request.json
            video_url = data.get('video_url')
            stock_symbol = data.get('stock_symbol', 'AAPL')
            date_range = data.get('date_range', 30)
            
            # �Ƒ
            video_analysis = gemini_service.analyze_video(video_url)
            
            # �֡hpn
            stock_data = stock_service.get_stock_data(stock_symbol, date_range)
            
            # �J
            report = report_service.generate_report(video_analysis, stock_data)
            
            return jsonify({
                'success': True,
                'report': report,
                'video_analysis': video_analysis,
                'stock_data': stock_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return render_template('analyze.html')

@app.route('/batch-analyze', methods=['GET', 'POST'])
def batch_analyze():
    """y��ub"""
    if request.method == 'POST':
        try:
            data = request.json
            channel_id = data.get('channel_id')
            video_count = data.get('video_count', 5)
            stock_symbol = data.get('stock_symbol', 'AAPL')
            
            # �֑SƑh
            videos = youtube_service.get_channel_videos(channel_id, video_count)
            
            # y��Ƒ
            analysis_results = []
            for video in videos:
                analysis = gemini_service.analyze_video(video['url'])
                analysis_results.append({
                    'video': video,
                    'analysis': analysis
                })
            
            # �֡hpn
            stock_data = stock_service.get_stock_data(stock_symbol, 30)
            
            # ��J
            report = report_service.generate_batch_report(analysis_results, stock_data)
            
            return jsonify({
                'success': True,
                'report': report,
                'analysis_results': analysis_results,
                'stock_data': stock_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return render_template('batch_analyze.html')

@app.route('/api/channel-videos')
def get_channel_videos():
    """�֑SƑhAPI"""
    channel_id = request.args.get('channel_id')
    count = request.args.get('count', 10, type=int)
    
    try:
        videos = youtube_service.get_channel_videos(channel_id, count)
        return jsonify({
            'success': True,
            'videos': videos
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock-data')
def get_stock_data():
    """�֡hpnAPI"""
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
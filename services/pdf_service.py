import os
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile

class PDFService:
    def __init__(self):
        """初始化PDF服务"""
        self.font_config = FontConfiguration()
        
        # CSS样式
        self.css_content = """
        @page {
            margin: 2cm;
            size: A4;
        }
        
        body {
            font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 14px;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            font-size: 28px;
            margin-top: 0;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #bdc3c7;
            padding-bottom: 8px;
            font-size: 22px;
            margin-top: 30px;
        }
        
        h3 {
            color: #2c3e50;
            font-size: 18px;
            margin-top: 25px;
        }
        
        h4 {
            color: #34495e;
            font-size: 16px;
            margin-top: 20px;
        }
        
        p {
            margin-bottom: 15px;
            text-align: justify;
        }
        
        ul, ol {
            margin-bottom: 15px;
            padding-left: 25px;
        }
        
        li {
            margin-bottom: 8px;
        }
        
        strong {
            color: #2c3e50;
            font-weight: bold;
        }
        
        em {
            color: #7f8c8d;
            font-style: italic;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 13px;
        }
        
        pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
            overflow-x: auto;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 13px;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #5a6c7d;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        table th,
        table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        table th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #2c3e50;
        }
        
        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .highlight {
            background-color: #fff3cd;
            padding: 15px;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            margin: 15px 0;
        }
        
        .warning {
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            margin: 15px 0;
        }
        
        .info {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 15px;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            margin: 15px 0;
        }
        """
    
    def markdown_to_pdf(self, markdown_content, output_path=None):
        """将Markdown内容转换为PDF"""
        try:
            # 将Markdown转换为HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['extra', 'codehilite', 'toc'],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight'
                    }
                }
            )
            
            # 包装HTML内容
            full_html = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>YouTube视频分析报告</title>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # 创建CSS对象
            css = CSS(string=self.css_content, font_config=self.font_config)
            
            # 生成PDF
            if output_path is None:
                # 如果没有指定输出路径，使用临时文件
                temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            # 生成PDF
            HTML(string=full_html).write_pdf(
                output_path,
                stylesheets=[css],
                font_config=self.font_config
            )
            
            return output_path
            
        except Exception as e:
            raise Exception(f"PDF生成失败: {str(e)}")
    
    def markdown_file_to_pdf(self, markdown_file_path, output_path=None):
        """将Markdown文件转换为PDF"""
        try:
            with open(markdown_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            return self.markdown_to_pdf(markdown_content, output_path)
            
        except Exception as e:
            raise Exception(f"读取Markdown文件失败: {str(e)}")
    
    def generate_pdf_from_cache(self, cache_key, cache_service):
        """从缓存生成PDF"""
        try:
            # 获取Markdown文件路径
            markdown_file = cache_service.get_markdown_file_path(cache_key)
            
            if not os.path.exists(markdown_file):
                raise Exception("缓存文件不存在")
            
            # 生成PDF文件路径
            pdf_filename = f"{cache_key}.pdf"
            pdf_path = os.path.join(os.path.dirname(markdown_file), pdf_filename)
            
            # 转换为PDF
            self.markdown_file_to_pdf(markdown_file, pdf_path)
            
            return pdf_path
            
        except Exception as e:
            raise Exception(f"从缓存生成PDF失败: {str(e)}")
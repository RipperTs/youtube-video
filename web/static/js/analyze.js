// 单视频分析页面JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // 配置marked.js选项
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: false, // 允许HTML，但我们会手动清理
            smartLists: true,
            smartypants: true
        });
    }
    
    const form = document.getElementById('videoAnalysisForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('analysisResults');
    const errorMessage = document.getElementById('errorMessage');
    const analysisTypeSelect = document.getElementById('analysisType');
    const stockSymbolGroup = document.getElementById('stockSymbolGroup');
    const stockSymbolInput = document.getElementById('stockSymbol');
    const videoUrlInput = document.getElementById('videoUrl');
    
    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const videoUrlFromParam = urlParams.get('video_url');
    if (videoUrlFromParam) {
        videoUrlInput.value = decodeURIComponent(videoUrlFromParam);
    }
    
    // 分析类型切换处理
    const dateRangeGroup = document.getElementById('dateRangeGroup');
    
    analysisTypeSelect.addEventListener('change', function() {
        const analysisType = this.value;
        if (analysisType === 'content_only') {
            stockSymbolGroup.style.display = 'none';
            stockSymbolInput.required = false;
            dateRangeGroup.style.display = 'none';
        } else if (analysisType === 'stock_extraction') {
            stockSymbolGroup.style.display = 'none';
            stockSymbolInput.required = false;
            dateRangeGroup.style.display = 'block';
        } else { // manual_stock
            stockSymbolGroup.style.display = 'block';
            stockSymbolInput.required = true;
            dateRangeGroup.style.display = 'block';
        }
    });
    
    // 初始化显示状态
    analysisTypeSelect.dispatchEvent(new Event('change'));
    
    // 表单提交处理
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            video_url: formData.get('video_url'),
            analysis_type: formData.get('analysis_type'),
            date_range: parseInt(formData.get('date_range'))
        };
        
        // 根据分析类型添加股票代码
        if (data.analysis_type === 'manual_stock') {
            data.stock_symbol = formData.get('stock_symbol');
        }
        
        // 验证YouTube URL
        if (!isValidYouTubeUrl(data.video_url)) {
            showError('请输入有效的YouTube视频链接');
            return;
        }
        
        // 开始流式分析
        startStreamAnalysis(data);
    });
    
    async function startStreamAnalysis(data) {
        // 显示日志区域
        const logsSection = document.getElementById('analysisLogs');
        const logContent = document.getElementById('logContent');
        const progressFill = document.getElementById('progressFill');
        
        logsSection.style.display = 'block';
        logContent.innerHTML = '';
        progressFill.style.width = '0%';
        
        // 隐藏结果和错误
        hideResults();
        hideError();
        
        // 开始分析状态
        startAnalysis();
        
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // 处理完整的数据行
                const lines = buffer.split('\n');
                buffer = lines.pop(); // 保留不完整的行
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonData = JSON.parse(line.substring(6));
                            handleStreamData(jsonData);
                        } catch (e) {
                            console.warn('解析流数据失败:', e);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('流式分析错误:', error);
            addLogEntry(`网络错误: ${error.message}`, 'error');
            showError('网络连接失败，请检查后重试');
        } finally {
            stopAnalysis();
        }
    }
    
    function handleStreamData(data) {
        console.log('收到流数据:', data); // 添加调试日志
        switch (data.type) {
            case 'status':
                updateProgress(data.progress, data.message);
                break;
            case 'log':
                addLogEntry(data.message, data.log_type, data.streaming_text);
                break;
            case 'result':
                console.log('收到最终结果:', data); // 添加调试日志
                handleFinalResult(data);
                break;
            case 'error':
                addLogEntry(data.message, 'error');
                showError(data.message);
                break;
        }
    }
    
    function updateProgress(progress, message) {
        const progressFill = document.getElementById('progressFill');
        progressFill.style.width = `${progress}%`;
        
        if (message) {
            addLogEntry(message, 'info');
        }
    }
    
    function addLogEntry(message, type, streamingText = null) {
        const logContent = document.getElementById('logContent');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        if (streamingText && type === 'streaming') {
            // 显示流式文本
            logEntry.innerHTML = `
                <div class="log-timestamp">[${timestamp}] ${message}</div>
                <div class="streaming-content">
                    <span class="text-chunk">${streamingText}</span>
                </div>
            `;
        } else {
            logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;
        }
        
        logContent.appendChild(logEntry);
        
        // 自动滚动到底部
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    function handleFinalResult(data) {
        addLogEntry('分析完成，显示结果...', 'success');
        
        // 隐藏日志区域
        setTimeout(() => {
            document.getElementById('analysisLogs').style.display = 'none';
        }, 2000);
        
        // 保存cache_key到全局变量
        window.currentCacheKey = data.cache_key;
        
        // 显示分析结果
        displayResults(data);
        
        // 显示PDF下载按钮
        showMarkdownDownloadButton();
    }
    
    function startAnalysis() {
        analyzeBtn.disabled = true;
        analyzeBtn.querySelector('.btn-text').style.display = 'none';
        analyzeBtn.querySelector('.loading-spinner').style.display = 'inline-block';
        
        // 防止表单重复提交
        form.style.pointerEvents = 'none';
        form.style.opacity = '0.6';
        
        // 禁用表单中的其他控件
        const formControls = form.querySelectorAll('input, select, textarea');
        formControls.forEach(control => control.disabled = true);
        
        hideError();
        hideResults();
    }
    
    function stopAnalysis() {
        analyzeBtn.disabled = false;
        analyzeBtn.querySelector('.btn-text').style.display = 'inline-block';
        analyzeBtn.querySelector('.loading-spinner').style.display = 'none';
        
        // 恢复表单状态
        form.style.pointerEvents = 'auto';
        form.style.opacity = '1';
        
        // 恢复表单中的其他控件
        const formControls = form.querySelectorAll('input, select, textarea');
        formControls.forEach(control => control.disabled = false);
    }
    
    function displayResults(result) {
        console.log('displayResults 接收到的数据:', result); // 添加调试日志
        
        const { report, video_analysis, stock_data, analysis_type, extracted_stocks } = result;
        
        console.log('解构后的数据:', { report, video_analysis, stock_data, analysis_type, extracted_stocks }); // 调试日志
        
        if (!report) {
            console.error('报告数据缺失');
            showError('分析结果数据不完整，请重试');
            return;
        }
        
        // 显示投资报告
        displayReport(report);
        
        // 显示视频分析
        displayVideoAnalysis(video_analysis, analysis_type, extracted_stocks);
        
        // 显示股票数据（如果有）
        if (stock_data && (analysis_type === 'manual_stock' || analysis_type === 'stock_extraction')) {
            displayStockData(stock_data, analysis_type);
        } else {
            // 隐藏股票数据标签
            const stockTab = document.querySelector('.tab-btn[onclick="showTab(\'stock\')"]');
            if (stockTab) {
                stockTab.style.display = 'none';
            }
        }
        
        // 显示结果区域
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        if (typeof showNotification === 'function') {
            showNotification('分析完成！', 'success');
        } else {
            console.log('分析完成！');
        }
    }
    
    function displayReport(report) {
        console.log('displayReport 接收到的报告:', report); // 添加调试日志
        
        // 显示报告标题
        document.getElementById('reportTitle').innerHTML = `<h2>${report.title}</h2><p><small>生成时间: ${report.generated_at}</small></p>`;
        
        // 根据报告类型显示不同的内容
        if (report.raw_markdown_content) {
            // 新的纯内容分析报告 - 直接显示AI的Markdown内容
            document.getElementById('executiveSummary').innerHTML = `
                <div class="full-report-content">
                    ${formatContent(report.raw_markdown_content)}
                </div>
            `;
            
            // 隐藏其他不需要的部分
            document.getElementById('recommendation').innerHTML = '';
            document.getElementById('riskAssessment').innerHTML = '';
            document.getElementById('priceTargets').innerHTML = '';
            
        } else if (report.investment_recommendation) {
            // 有股票数据的报告 - 保持原有逻辑
            document.getElementById('executiveSummary').innerHTML = `
                <h3>执行摘要</h3>
                <div class="content-block">${formatContent(report.executive_summary)}</div>
            `;
            
            document.getElementById('recommendation').innerHTML = `
                <h3>投资建议</h3>
                <div class="recommendation-box">
                    <h4>建议: ${report.investment_recommendation.action}</h4>
                    <p><strong>信心水平:</strong> ${report.investment_recommendation.confidence_level}</p>
                    <p><strong>投资期限:</strong> ${report.investment_recommendation.time_horizon}</p>
                    <p><strong>理由:</strong> ${report.investment_recommendation.reasoning}</p>
                </div>
            `;
            
            // 风险评估和价格目标处理...
            // (保持原有逻辑)
            
        } else if (report.investment_logic) {
            // 兼容旧格式的报告
            document.getElementById('executiveSummary').innerHTML = `
                <h3>执行摘要</h3>
                <div class="content-block">${formatContent(report.executive_summary || '暂无执行摘要')}</div>
            `;
            
            document.getElementById('recommendation').innerHTML = `
                <h3>投资逻辑</h3>
                <div class="recommendation-box">
                    <div class="content-block">${formatContent(report.investment_logic)}</div>
                </div>
                ${report.key_takeaways ? `
                    <h3>关键要点</h3>
                    <div class="key-takeaways-box">
                        <div class="content-block">${formatContent(report.key_takeaways)}</div>
                    </div>
                ` : ''}
            `;
        } else {
            document.getElementById('recommendation').innerHTML = `
                <h3>分析内容</h3>
                <p>报告内容正在处理中...</p>
            `;
        }
        
        // 风险评估处理（为新格式简化）
        if (report.raw_markdown_content) {
            // 新格式已经包含所有内容，不需要额外处理
        } else if (report.risk_assessment) {
            if (typeof report.risk_assessment === 'object' && report.risk_assessment.overall_risk_level) {
                document.getElementById('riskAssessment').innerHTML = `
                    <h3>风险评估</h3>
                    <p><strong>总体风险级别:</strong> ${report.risk_assessment.overall_risk_level}</p>
                    ${report.risk_assessment.specific_risks ? `
                        <h4>具体风险:</h4>
                        <ul>
                            ${report.risk_assessment.specific_risks.map(risk => `<li>${risk}</li>`).join('')}
                        </ul>
                    ` : ''}
                    ${report.risk_assessment.mitigation_strategies ? `
                        <h4>缓解策略:</h4>
                        <ul>
                            ${report.risk_assessment.mitigation_strategies.map(strategy => `<li>${strategy}</li>`).join('')}
                        </ul>
                    ` : ''}
                `;
            } else {
                document.getElementById('riskAssessment').innerHTML = `
                    <h3>风险评估</h3>
                    <div class="content-block">${formatContent(report.risk_assessment)}</div>
                `;
            }
        } else {
            document.getElementById('riskAssessment').innerHTML = `
                <h3>风险评估</h3>
                <p>暂无风险评估数据</p>
            `;
        }
        
        // 价格目标（新格式不需要单独处理）
        if (report.raw_markdown_content) {
            document.getElementById('priceTargets').innerHTML = '';
        } else if (report.price_targets) {
            document.getElementById('priceTargets').innerHTML = `
                <h3>价格目标</h3>
                <div class="price-targets-grid">
                    <div class="price-item">
                        <span class="price-label">当前价格</span>
                        <span class="price-value">$${report.price_targets.current_price}</span>
                    </div>
                    <div class="price-item">
                        <span class="price-label">12个月目标</span>
                        <span class="price-value">$${report.price_targets.target_12m}</span>
                    </div>
                    <div class="price-item">
                        <span class="price-label">止损位</span>
                        <span class="price-value">$${report.price_targets.stop_loss}</span>
                    </div>
                    <div class="price-item">
                        <span class="price-label">支撑位</span>
                        <span class="price-value">$${report.price_targets.support_level}</span>
                    </div>
                </div>
            `;
        } else {
            document.getElementById('priceTargets').innerHTML = '';
        }
    }
    
    function displayVideoAnalysis(analysis, analysisType, extractedStocks) {
        document.getElementById('videoSummary').innerHTML = `
            <h3>视频内容摘要</h3>
            <div class="content-block">${formatContent(analysis.summary || '暂无摘要')}</div>
        `;
        
        // 根据分析类型显示不同的内容
        let companiesHtml = '';
        if (analysisType === 'stock_extraction' && extractedStocks && extractedStocks.length > 0) {
            companiesHtml = `
                <h3>提取到的股票</h3>
                <div class="extracted-stocks">
                    ${extractedStocks.map(stock => `
                        <div class="stock-item">
                            <span class="stock-symbol">${stock.symbol}</span>
                            <span class="stock-name">${stock.name || ''}</span>
                            <span class="confidence">置信度: ${stock.confidence || 'N/A'}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            companiesHtml = `
                <h3>提到的公司</h3>
                ${analysis.companies && analysis.companies.length > 0 
                    ? `<div class="tag-list">${analysis.companies.map(company => `<span class="tag">${company}</span>`).join('')}</div>`
                    : '<p>未识别到具体公司</p>'
                }
            `;
        }
        
        document.getElementById('mentionedCompanies').innerHTML = companiesHtml;
        
        document.getElementById('marketEvents').innerHTML = `
            <h3>市场事件</h3>
            ${analysis.market_events && analysis.market_events.length > 0
                ? `<ul>${analysis.market_events.map(event => `<li>${event}</li>`).join('')}</ul>`
                : '<p>未识别到重要市场事件</p>'
            }
        `;
        
        document.getElementById('expertOpinions').innerHTML = `
            <h3>专家观点</h3>
            ${analysis.investment_views && analysis.investment_views.length > 0
                ? `<ul>${analysis.investment_views.map(view => `<li>${view}</li>`).join('')}</ul>`
                : '<p>未识别到明确投资观点</p>'
            }
        `;
    }
    
    function displayStockData(stockData, analysisType) {
        // 支持单个股票或多个股票显示
        if (Array.isArray(stockData)) {
            // 多个股票的情况
            let stocksHtml = '<h3>股票数据分析</h3>';
            stockData.forEach((stock, index) => {
                stocksHtml += `
                    <div class="stock-analysis-item">
                        <h4>${stock.symbol} - ${stock.name || '未知公司'}</h4>
                        <div class="stock-overview-grid">
                            <div class="stock-metric">
                                <span class="metric-label">当前价格</span>
                                <span class="metric-value">$${stock.latest_price}</span>
                            </div>
                            <div class="stock-metric">
                                <span class="metric-label">涨跌幅</span>
                                <span class="metric-value ${stock.pct_change >= 0 ? 'positive' : 'negative'}">
                                    ${stock.pct_change >= 0 ? '+' : ''}${stock.pct_change.toFixed(2)}%
                                </span>
                            </div>
                            <div class="stock-metric">
                                <span class="metric-label">价格趋势</span>
                                <span class="metric-value">${stock.price_trend}</span>
                            </div>
                            <div class="stock-metric">
                                <span class="metric-label">波动率</span>
                                <span class="metric-value">${stock.volatility}%</span>
                            </div>
                        </div>
                        ${index < stockData.length - 1 ? '<hr>' : ''}
                    </div>
                `;
            });
            document.getElementById('stockOverview').innerHTML = stocksHtml;
            
            document.getElementById('technicalIndicators').innerHTML = `
                <h3>整体分析总结</h3>
                <p>共分析了 ${stockData.length} 只股票</p>
                <p>分析时间范围: ${stockData[0]?.period || '未知'}</p>
            `;
        } else {
            // 单个股票的情况
            document.getElementById('stockOverview').innerHTML = `
                <h3>${stockData.symbol} 股票概览</h3>
                <div class="stock-overview-grid">
                    <div class="stock-metric">
                        <span class="metric-label">当前价格</span>
                        <span class="metric-value">$${stockData.latest_price}</span>
                    </div>
                    <div class="stock-metric">
                        <span class="metric-label">涨跌幅</span>
                        <span class="metric-value ${stockData.pct_change >= 0 ? 'positive' : 'negative'}">
                            ${stockData.pct_change >= 0 ? '+' : ''}${stockData.pct_change.toFixed(2)}%
                        </span>
                    </div>
                    <div class="stock-metric">
                        <span class="metric-label">价格趋势</span>
                        <span class="metric-value">${stockData.price_trend}</span>
                    </div>
                    <div class="stock-metric">
                        <span class="metric-label">波动率</span>
                        <span class="metric-value">${stockData.volatility}%</span>
                    </div>
                </div>
            `;
            
            document.getElementById('technicalIndicators').innerHTML = `
                <h3>技术指标</h3>
                <p><strong>数据期间:</strong> ${stockData.period}</p>
                <p><strong>数据点数:</strong> ${stockData.data_points}</p>
                <p><strong>成交量:</strong> ${stockData.volume.toLocaleString()}</p>
            `;
        }
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth' });
    }
    
    function hideError() {
        errorMessage.style.display = 'none';
    }
    
    function hideResults() {
        resultsSection.style.display = 'none';
    }
    
    function isValidYouTubeUrl(url) {
        const regex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
        return regex.test(url);
    }
});

// 安全的Markdown解析函数
function parseMarkdown(text) {
    if (typeof marked === 'undefined') {
        // 如果marked.js未加载，返回原始文本
        console.warn('marked.js未加载，使用纯文本显示');
        return text.replace(/\n/g, '<br>');
    }
    
    try {
        // 基本的HTML清理，移除potentially危险的标签
        const cleanText = text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                             .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
                             .replace(/<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi, '')
                             .replace(/<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>/gi, '');
        
        return marked.parse(cleanText);
    } catch (error) {
        console.error('Markdown解析失败:', error);
        return text.replace(/\n/g, '<br>');
    }
}

// 格式化文本内容（支持Markdown）
function formatContent(content, useMarkdown = true) {
    if (!content) return '';
    
    if (useMarkdown) {
        return parseMarkdown(content);
    } else {
        return content.replace(/\n/g, '<br>');
    }
}

// 标签页切换功能
function showTab(tabName) {
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 移除所有标签按钮的活动状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 显示选中的标签内容
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // 激活对应的标签按钮
    event.target.classList.add('active');
}

// PDF下载相关函数
function showMarkdownDownloadButton() {
    // 检查是否有cache_key
    if (!window.currentCacheKey) {
        console.warn('没有找到cache_key，无法下载Markdown');
        return;
    }
    
    // 查找或创建Markdown下载按钮
    let markdownButton = document.getElementById('markdownDownloadBtn');
    if (!markdownButton) {
        markdownButton = document.createElement('button');
        markdownButton.id = 'markdownDownloadBtn';
        markdownButton.className = 'btn btn-secondary';
        markdownButton.innerHTML = `
            <i class="fas fa-download"></i>
            <span class="btn-text">下载Markdown报告</span>
            <span class="loading-spinner" style="display: none;">
                <i class="fas fa-spinner fa-spin"></i>
            </span>
        `;
        
        // 添加点击事件
        markdownButton.addEventListener('click', downloadMarkdownReport);
        
        // 插入到结果区域的开头
        const resultsSection = document.getElementById('analysisResults');
        if (resultsSection) {
            resultsSection.insertBefore(markdownButton, resultsSection.firstChild);
        }
    }
    
    // 显示按钮
    markdownButton.style.display = 'inline-block';
    markdownButton.style.marginBottom = '20px';
}

function downloadMarkdownReport() {
    if (!window.currentCacheKey) {
        alert('没有找到分析结果，请先进行分析');
        return;
    }
    
    const markdownButton = document.getElementById('markdownDownloadBtn');
    
    // 显示加载状态
    markdownButton.disabled = true;
    markdownButton.querySelector('.btn-text').style.display = 'none';
    markdownButton.querySelector('.loading-spinner').style.display = 'inline-block';
    
    // 创建下载链接
    const downloadUrl = `/api/download-markdown/${window.currentCacheKey}`;
    
    // 创建隐藏的a标签进行下载
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `youtube_analysis_${window.currentCacheKey.substring(0, 8)}.md`;
    
    // 添加到DOM并触发点击
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
    
    // 恢复按钮状态
    setTimeout(() => {
        markdownButton.disabled = false;
        markdownButton.querySelector('.btn-text').style.display = 'inline-block';
        markdownButton.querySelector('.loading-spinner').style.display = 'none';
        
        // 显示成功提示
        if (typeof showNotification === 'function') {
            showNotification('Markdown下载已开始', 'success');
        }
    }, 1000);
}
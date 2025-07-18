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
    const encodedUrlFromParam = urlParams.get('encoded_url');
    
    if (encodedUrlFromParam) {
        // 处理base64编码的URL
        try {
            const decodedUrl = decodeURIComponent(atob(encodedUrlFromParam));
            videoUrlInput.value = decodedUrl;
        } catch (error) {
            console.error('解码URL失败:', error);
            if (videoUrlFromParam) {
                videoUrlInput.value = decodeURIComponent(videoUrlFromParam);
            }
        }
    } else if (videoUrlFromParam) {
        // 处理普通URL编码的URL（向后兼容）
        videoUrlInput.value = decodeURIComponent(videoUrlFromParam);
    }
    
    // 设置日期选择器的默认值
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    // 设置默认时间范围（最近30天）
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 30);
    
    // 格式化日期为 YYYY-MM-DD
    endDateInput.value = endDate.toISOString().split('T')[0];
    startDateInput.value = startDate.toISOString().split('T')[0];
    
    // 日期验证
    function validateDateRange() {
        const start = new Date(startDateInput.value);
        const end = new Date(endDateInput.value);
        
        if (start >= end) {
            showError('开始日期必须早于结束日期');
            return false;
        }
        
        // 检查时间范围不超过1年
        const maxDays = 365;
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays > maxDays) {
            showError('时间范围不能超过1年');
            return false;
        }
        
        return true;
    }
    
    // 添加日期变化监听器
    startDateInput.addEventListener('change', validateDateRange);
    endDateInput.addEventListener('change', validateDateRange);
    
    // 分析类型切换处理
    const dateRangeGroup = document.getElementById('dateRangeGroup');
    
    analysisTypeSelect.addEventListener('change', function() {
        const analysisType = this.value;
        if (analysisType === 'content_only') {
            stockSymbolGroup.style.display = 'none';
            stockSymbolInput.required = false;
            dateRangeGroup.style.display = 'block';
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
        
        // 验证日期范围
        if (!validateDateRange()) {
            return;
        }
        
        const formData = new FormData(form);
        const data = {
            video_url: formData.get('video_url'),
            analysis_type: formData.get('analysis_type'),
            start_date: formData.get('start_date'),
            end_date: formData.get('end_date')
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
        
        // 验证必填字段
        if ((data.analysis_type === 'stock_extraction' || data.analysis_type === 'manual_stock') && 
            (!data.start_date || !data.end_date)) {
            showError('请选择有效的时间范围');
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
        showPdfDownloadButton();
        
        // 显示股票提取按钮（仅在有分析结果时）
        showStockExtractButton();
    }
    
    function startAnalysis() {
        analyzeBtn.disabled = true;
        analyzeBtn.querySelector('.btn-text').style.display = 'none';
        analyzeBtn.querySelector('.loading-spinner').style.display = 'inline-block';
        
        // 启动计时器
        startTimer();
        
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
        
        // 停止计时器
        stopTimer();
        
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
        
        // 确保按钮容器也显示
        const actionButtons = document.querySelector('.action-buttons');
        if (actionButtons) {
            actionButtons.style.display = 'block';
            console.log('Action buttons container shown');
        }
        
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
        console.log('displayVideoAnalysis 收到的参数:', { analysis, analysisType, extractedStocks }); // 调试日志
        console.log('analysis.summary:', analysis?.summary); // 调试日志
        console.log('analysis类型:', typeof analysis); // 调试日志
        
        if (!analysis) {
            console.warn('analysis 为空或未定义');
            analysis = { summary: '暂无摘要' };
        }
        
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
                                <span class="metric-value ${stock.pct_change !== undefined ? (stock.pct_change >= 0 ? 'positive' : 'negative') : 'neutral'}">
                                    ${stock.pct_change !== undefined ? 
                                        `${stock.pct_change >= 0 ? '+' : ''}${stock.pct_change.toFixed(2)}%` : 
                                        '数据获取失败'
                                    }
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
                        <span class="metric-value ${stockData.pct_change !== undefined ? (stockData.pct_change >= 0 ? 'positive' : 'negative') : 'neutral'}">
                            ${stockData.pct_change !== undefined ? 
                                `${stockData.pct_change >= 0 ? '+' : ''}${stockData.pct_change.toFixed(2)}%` : 
                                '数据获取失败'
                            }
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
    
    // 计时器相关变量和函数
    let timerInterval = null;
    let startTime = null;
    
    function startTimer() {
        startTime = Date.now();
        const timerDisplay = document.getElementById('timerDisplay');
        
        if (timerDisplay) {
            timerInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                
                if (minutes > 0) {
                    timerDisplay.textContent = `${minutes}m ${seconds}s`;
                } else {
                    timerDisplay.textContent = `${seconds}s`;
                }
            }, 1000);
        }
    }
    
    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        
        const timerDisplay = document.getElementById('timerDisplay');
        if (timerDisplay) {
            timerDisplay.textContent = '0s';
        }
    }
    
    // 股票提取按钮相关功能
    function initStockExtractButton() {
        const stockExtractBtn = document.getElementById('stockExtractBtn');
        if (stockExtractBtn) {
            stockExtractBtn.addEventListener('click', handleStockExtraction);
        }
    }
    
    function showStockExtractButton() {
        console.log('showStockExtractButton called');
        
        // 使用setTimeout确保DOM已经更新
        setTimeout(() => {
            const stockExtractBtn = document.getElementById('stockExtractBtn');
            console.log('Looking for button:', stockExtractBtn);
            
            if (stockExtractBtn) {
                stockExtractBtn.style.display = 'inline-block';
                stockExtractBtn.style.visibility = 'visible';
                console.log('Stock extract button shown, cache_key:', window.currentCacheKey);
            } else {
                console.error('Stock extract button not found in DOM');
                // 打印所有按钮，看看发生了什么
                const allButtons = document.querySelectorAll('button');
                console.log('All buttons found:', allButtons);
            }
        }, 100);
    }
    
    function hideStockExtractButton() {
        const stockExtractBtn = document.getElementById('stockExtractBtn');
        if (stockExtractBtn) {
            stockExtractBtn.style.display = 'none';
        }
    }
    
    async function handleStockExtraction() {
        console.log('handleStockExtraction called, cache_key:', window.currentCacheKey);
        
        if (!window.currentCacheKey) {
            alert('没有找到分析结果，请先进行分析');
            return;
        }
        
        // 获取当前选择的日期范围
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        const startDate = startDateInput ? startDateInput.value : null;
        const endDate = endDateInput ? endDateInput.value : null;
        
        console.log('Current date range:', startDate, 'to', endDate);
        
        const stockExtractBtn = document.getElementById('stockExtractBtn');
        
        // 显示加载状态
        setStockExtractButtonLoading(true);
        
        try {
            console.log('Sending request to API with cache_key:', window.currentCacheKey);
            
            // 构建请求数据
            const requestData = {
                cache_key: window.currentCacheKey
            };
            
            // 如果有日期范围，添加到请求中
            if (startDate && endDate) {
                requestData.start_date = startDate;
                requestData.end_date = endDate;
                console.log('Including date range in request:', startDate, 'to', endDate);
            }
            
            // 调用API提取股票信息并生成图表
            const response = await fetch('/api/extract-stocks-chart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            console.log('API response status:', response.status);
            
            const result = await response.json();
            console.log('API response result:', result);
            
            if (result.success) {
                // 显示结果
                displayStockChartAnalysis(result.data);
                
                // 显示走势图分析标签页
                showChartTab();
                
                // 自动切换到走势图标签
                showTab('chart');
                
                if (typeof showNotification === 'function') {
                    showNotification('股票提取和图表分析完成！', 'success');
                }
            } else {
                throw new Error(result.error || '股票提取失败');
            }
            
        } catch (error) {
            console.error('股票提取错误:', error);
            showError(`股票提取失败: ${error.message}`);
        } finally {
            setStockExtractButtonLoading(false);
        }
    }
    
    function setStockExtractButtonLoading(loading) {
        const stockExtractBtn = document.getElementById('stockExtractBtn');
        if (stockExtractBtn) {
            stockExtractBtn.disabled = loading;
            stockExtractBtn.querySelector('.btn-text').style.display = loading ? 'none' : 'inline-block';
            stockExtractBtn.querySelector('.loading-spinner').style.display = loading ? 'inline-block' : 'none';
        }
    }
    
    function showChartTab() {
        const chartTabBtn = document.getElementById('chartTabBtn');
        if (chartTabBtn) {
            chartTabBtn.style.display = 'inline-block';
        }
    }
    
    function hideChartTab() {
        const chartTabBtn = document.getElementById('chartTabBtn');
        if (chartTabBtn) {
            chartTabBtn.style.display = 'none';
        }
    }
    
    function displayStockChartAnalysis(data) {
        console.log('显示股票图表分析:', data);
        
        const { extracted_stocks, stock_charts, accuracy_analysis } = data;
        
        // 显示提取的股票信息
        displayExtractedStocks(extracted_stocks);
        
        // 显示股票图表
        displayStockCharts(stock_charts);
        
        // 显示准确性分析
        displayAccuracyAnalysis(accuracy_analysis);
    }
    
    function displayExtractedStocks(extractedStocks) {
        const container = document.getElementById('extractedStocksInfo');
        
        if (!extractedStocks || extractedStocks.length === 0) {
            container.innerHTML = `
                <h3>提取的股票信息</h3>
                <p>未能从报告中提取到有效的股票信息</p>
            `;
            return;
        }
        
        let stocksHtml = `
            <h3>提取的股票信息 (${extractedStocks.length}只)</h3>
            <div class="extracted-stocks-grid">
        `;
        
        extractedStocks.forEach(stock => {
            const recommendationClass = getRecommendationClass(stock.recommendation);
            stocksHtml += `
                <div class="stock-item-card">
                    <span class="stock-symbol-large">${stock.symbol}</span>
                    <div class="stock-name">${stock.name || '未知公司'}</div>
                    <div class="stock-recommendation ${recommendationClass}">
                        ${stock.recommendation || '无建议'}
                    </div>
                    <div style="margin-top: 8px; font-size: 12px; color: #7f8c8d;">
                        提取置信度: ${stock.confidence || 'N/A'}
                    </div>
                </div>
            `;
        });
        
        stocksHtml += '</div>';
        container.innerHTML = stocksHtml;
    }
    
    function getRecommendationClass(recommendation) {
        if (!recommendation) return 'neutral';
        
        const rec = recommendation.toLowerCase();
        if (rec.includes('买入') || rec.includes('增仓') || rec.includes('看多')) {
            return 'positive';
        } else if (rec.includes('卖出') || rec.includes('减仓') || rec.includes('看空')) {
            return 'negative';
        } else {
            return 'neutral';
        }
    }
    
    function displayStockCharts(stockCharts) {
        const container = document.getElementById('stockChartContainer');
        
        if (!stockCharts || stockCharts.length === 0) {
            container.innerHTML = `
                <h3>股票走势图</h3>
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>未能生成股票走势图</p>
                </div>
            `;
            return;
        }
        
        let chartsHtml = '<h3>股票走势图分析</h3>';
        
        stockCharts.forEach(chart => {
            chartsHtml += `
                <div class="chart-container">
                    <div class="chart-info">
                        <h4>${chart.symbol} - ${chart.name || '未知公司'}</h4>
                        <p><strong>分析期间:</strong> ${chart.period || '未知'}</p>
                        ${chart.current_price ? `<p><strong>当前价格:</strong> $${chart.current_price}</p>` : ''}
                        ${chart.price_change !== undefined ? `
                            <p><strong>期间涨跌:</strong> 
                                <span class="${chart.price_change >= 0 ? 'positive' : 'negative'}">
                                    ${chart.price_change >= 0 ? '+' : ''}${chart.price_change.toFixed(2)}%
                                </span>
                            </p>
                        ` : `
                            <p><strong>期间涨跌:</strong> 
                                <span class="neutral">数据获取失败</span>
                            </p>
                        `}
                    </div>
                    ${chart.chart_url ? `
                        <img src="${chart.chart_url}" alt="${chart.symbol}走势图" class="chart-image">
                    ` : `
                        <div class="chart-error">
                            <i class="fas fa-exclamation-triangle"></i>
                            <p>图表生成失败</p>
                            ${chart.error ? `<small>${chart.error}</small>` : ''}
                        </div>
                    `}
                </div>
            `;
        });
        
        container.innerHTML = chartsHtml;
    }
    
    function displayAccuracyAnalysis(accuracyAnalysis) {
        const container = document.getElementById('accuracyAnalysis');
        
        if (!accuracyAnalysis) {
            container.innerHTML = `
                <h3>准确性分析</h3>
                <div class="chart-error">
                    <p>准确性分析暂时不可用</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="accuracy-analysis">
                <h3>AI投资建议准确性分析</h3>
                
                <div class="accuracy-score">
                    <div>综合准确性评分</div>
                    <div style="font-size: 36px; margin: 10px 0;">
                        ${accuracyAnalysis.overall_score || 'N/A'}
                    </div>
                </div>
                
                <div class="accuracy-details">
                    <h4>分析详情</h4>
                    <div style="white-space: pre-line;">
                        ${accuracyAnalysis.analysis_summary || '暂无详细分析'}
                    </div>
                </div>
                
                ${accuracyAnalysis.key_findings ? `
                    <div class="accuracy-details">
                        <h4>关键发现</h4>
                        <ul>
                            ${accuracyAnalysis.key_findings.map(finding => `<li>${finding}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${accuracyAnalysis.market_context ? `
                    <div class="accuracy-details">
                        <h4>市场背景</h4>
                        <div>${accuracyAnalysis.market_context}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // 初始化股票提取按钮
    initStockExtractButton();
    
    // 添加全局测试函数
    window.testShowButton = function() {
        console.log('Manual test: showing stock extract button');
        showStockExtractButton();
    };
    
    window.debugButton = function() {
        const btn = document.getElementById('stockExtractBtn');
        const container = document.querySelector('.action-buttons');
        const results = document.getElementById('analysisResults');
        
        console.log('Debug info:');
        console.log('Button element:', btn);
        console.log('Button computed styles:', btn ? window.getComputedStyle(btn) : 'N/A');
        console.log('Container element:', container);
        console.log('Results section:', results);
        console.log('Results section display:', results ? results.style.display : 'N/A');
        console.log('Current cache key:', window.currentCacheKey);
    };
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
function showTab(tabName, clickedElement = null) {
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
    if (clickedElement) {
        // 如果传入了点击的元素，直接使用
        clickedElement.classList.add('active');
    } else if (typeof event !== 'undefined' && event.target) {
        // 如果是通过点击触发的，使用event.target
        event.target.classList.add('active');
    } else {
        // 如果是通过代码调用的，查找对应的标签按钮
        const targetButton = document.querySelector(`[onclick="showTab('${tabName}')"]`) || 
                           document.querySelector(`#${tabName}TabBtn`) ||
                           document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        if (targetButton) {
            targetButton.classList.add('active');
        }
    }
}

// PDF下载相关函数
function showPdfDownloadButton() {
    // 检查是否有cache_key
    if (!window.currentCacheKey) {
        console.warn('没有找到cache_key，无法下载PDF');
        return;
    }
    
    // 查找或创建PDF下载按钮
    let pdfButton = document.getElementById('pdfDownloadBtn');
    if (!pdfButton) {
        pdfButton = document.createElement('button');
        pdfButton.id = 'pdfDownloadBtn';
        pdfButton.className = 'btn btn-secondary';
        pdfButton.innerHTML = `
            <i class="fas fa-file-pdf"></i>
            <span class="btn-text">下载PDF报告</span>
            <span class="loading-spinner" style="display: none;">
                <i class="fas fa-spinner fa-spin"></i>
                正在生成PDF...
            </span>
        `;
        
        // 添加点击事件
        pdfButton.addEventListener('click', downloadPdfReport);
        
        // 插入到结果区域的开头
        const resultsSection = document.getElementById('analysisResults');
        if (resultsSection) {
            resultsSection.insertBefore(pdfButton, resultsSection.firstChild);
        }
    }
    
    // 显示按钮
    pdfButton.style.display = 'inline-block';
    pdfButton.style.marginBottom = '20px';
}

function downloadPdfReport() {
    if (!window.currentCacheKey) {
        alert('没有找到分析结果，请先进行分析');
        return;
    }
    
    const pdfButton = document.getElementById('pdfDownloadBtn');
    
    // 显示加载状态
    pdfButton.disabled = true;
    pdfButton.querySelector('.btn-text').style.display = 'none';
    pdfButton.querySelector('.loading-spinner').style.display = 'inline-block';
    
    // 创建下载链接
    const downloadUrl = `/api/download-pdf/${window.currentCacheKey}`;
    
    // 创建隐藏的a标签进行下载
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `youtube_analysis_${window.currentCacheKey.substring(0, 8)}.pdf`;
    
    // 添加到DOM并触发点击
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
    
    // 恢复按钮状态
    setTimeout(() => {
        pdfButton.disabled = false;
        pdfButton.querySelector('.btn-text').style.display = 'inline-block';
        pdfButton.querySelector('.loading-spinner').style.display = 'none';
        
        // 显示成功提示
        if (typeof showNotification === 'function') {
            showNotification('PDF下载已开始', 'success');
        }
    }, 2000);
}
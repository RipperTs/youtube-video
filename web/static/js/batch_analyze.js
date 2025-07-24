// 批量分析页面JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // 配置marked.js选项
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: false,
            smartLists: true,
            smartypants: true
        });
    }
    
    // 页面元素
    const channelSearchForm = document.getElementById('channelSearchForm');
    const searchChannelBtn = document.getElementById('searchChannelBtn');
    const videoListSection = document.getElementById('videoListSection');
    const videoList = document.getElementById('videoList');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const batchAnalyzeBtn = document.getElementById('batchAnalyzeBtn');
    const selectedCountSpan = document.getElementById('selectedCount');
    const batchAnalyzeSection = document.querySelector('.batch-analyze-section');
    const progressSection = document.getElementById('progressSection');
    const resultsSection = document.getElementById('batchResults');
    const errorMessage = document.getElementById('errorMessage');
    
    // 状态变量
    let currentChannelId = '';
    let selectedVideos = [];
    let allVideos = [];
    let currentNextToken = '';
    const PAGE_SIZE = 20;
    
    // 频道搜索表单提交
    channelSearchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const channelId = document.getElementById('channelId').value.trim();
        if (!channelId) {
            showError('请输入YouTube频道ID或名称');
            return;
        }
        
        currentChannelId = channelId;
        currentNextToken = '';
        allVideos = [];
        selectedVideos = [];
        
        // 重置加载按钮状态
        loadMoreBtn.style.display = 'none';
        
        await searchChannelVideos();
    });
    
    // 搜索频道视频
    async function searchChannelVideos() {
        try {
            setSearchLoading(true);
            hideError();
            
            const url = new URL('/api/channel-videos', window.location.origin);
            url.searchParams.append('channel_id', currentChannelId);
            url.searchParams.append('count', PAGE_SIZE);
            if (currentNextToken) {
                url.searchParams.append('next_token', currentNextToken);
            }
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                const videos = result.videos || [];
                const isFirstPage = !currentNextToken;
                
                if (isFirstPage) {
                    // 第一页，重置列表
                    allVideos = videos;
                    displayVideoList(videos);
                    videoListSection.style.display = 'block';
                } else {
                    // 后续页面，追加到现有列表
                    allVideos = allVideos.concat(videos);
                    appendVideoList(videos);
                }
                
                // 更新分页状态
                currentNextToken = result.next_token || '';
                
                // 如果没有更多视频，隐藏加载更多按钮
                if (!result.has_more) {
                    loadMoreBtn.style.display = 'none';
                } else {
                    loadMoreBtn.style.display = 'inline-block';
                }
                
                updateSelectionCount();
            } else {
                showError(result.error || '获取频道视频失败');
            }
        } catch (error) {
            showError('网络错误，请重试');
            console.error('Search error:', error);
        } finally {
            setSearchLoading(false);
        }
    }
    
    // 显示视频列表
    function displayVideoList(videos) {
        videoList.innerHTML = '';
        appendVideoList(videos);
    }
    
    // 追加视频列表
    function appendVideoList(videos) {
        videos.forEach(video => {
            const videoItem = createVideoItem(video);
            videoList.appendChild(videoItem);
        });
    }
    
    // 创建视频项元素
    function createVideoItem(video) {
        const videoItem = document.createElement('div');
        videoItem.className = 'video-item';
        videoItem.dataset.videoId = video.id || video.url;
        
        const thumbnail = video.thumbnail || '/static/images/video-placeholder.svg';
        const title = video.title || '无标题';
        const description = video.description || '暂无描述';
        const publishedAt = video.published_at || '未知时间';
        const duration = video.duration || '未知时长';
        const viewCount = video.view_count || '';
        
        videoItem.innerHTML = `
            <input type="checkbox" class="video-checkbox" data-video='${JSON.stringify(video)}'>
            <div class="video-thumbnail">
                <img src="${thumbnail}" alt="视频缩略图" onerror="this.src='/static/images/video-placeholder.svg'">
            </div>
            <div class="video-title">${title}</div>
            <div class="video-description">${description}</div>
            <div class="video-meta">
                <span>${publishedAt}</span>
                <span>${duration}</span>
                ${viewCount ? `<span>${viewCount}</span>` : ''}
            </div>
            <div class="video-actions">
                <button class="btn btn-secondary btn-sm" onclick="openVideoUrl('${video.url}')">观看</button>
                <button class="btn btn-primary btn-sm" onclick="analyzeVideoSingle('${video.url}')">单独分析</button>
            </div>
        `;
        
        // 添加复选框事件监听
        const checkbox = videoItem.querySelector('.video-checkbox');
        checkbox.addEventListener('change', function() {
            handleVideoSelection(this, video);
        });
        
        // 添加点击选择事件
        videoItem.addEventListener('click', function(e) {
            if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
        
        return videoItem;
    }
    
    // 处理视频选择
    function handleVideoSelection(checkbox, video) {
        const videoItem = checkbox.closest('.video-item');
        
        if (checkbox.checked) {
            if (selectedVideos.length >= 10) {
                checkbox.checked = false;
                showError('最多只能选择10个视频');
                return;
            }
            selectedVideos.push(video);
            videoItem.classList.add('selected');
        } else {
            selectedVideos = selectedVideos.filter(v => (v.id || v.url) !== (video.id || video.url));
            videoItem.classList.remove('selected');
        }
        
        updateSelectionCount();
        updateBatchAnalyzeButton();
    }
    
    // 更新选择计数
    function updateSelectionCount() {
        selectedCountSpan.textContent = selectedVideos.length;
    }
    
    // 更新批量分析按钮显示
    function updateBatchAnalyzeButton() {
        if (selectedVideos.length > 0) {
            batchAnalyzeSection.style.display = 'block';
        } else {
            batchAnalyzeSection.style.display = 'none';
        }
    }
    
    // 全选按钮
    selectAllBtn.addEventListener('click', function() {
        const checkboxes = videoList.querySelectorAll('.video-checkbox');
        const maxSelect = Math.min(10, checkboxes.length);
        
        // 清除当前选择
        selectedVideos = [];
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.closest('.video-item').classList.remove('selected');
        });
        
        // 选择前10个
        for (let i = 0; i < maxSelect; i++) {
            const checkbox = checkboxes[i];
            const video = JSON.parse(checkbox.dataset.video);
            checkbox.checked = true;
            checkbox.closest('.video-item').classList.add('selected');
            selectedVideos.push(video);
        }
        
        updateSelectionCount();
        updateBatchAnalyzeButton();
    });
    
    // 清除选择按钮
    clearSelectionBtn.addEventListener('click', function() {
        selectedVideos = [];
        const checkboxes = videoList.querySelectorAll('.video-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.closest('.video-item').classList.remove('selected');
        });
        
        updateSelectionCount();
        updateBatchAnalyzeButton();
    });
    
    // 加载更多按钮
    loadMoreBtn.addEventListener('click', function() {
        searchChannelVideos();
    });
    
    // 批量分析按钮
    batchAnalyzeBtn.addEventListener('click', async function() {
        if (selectedVideos.length === 0) {
            showError('请选择要分析的视频');
            return;
        }
        
        try {
            setBatchAnalyzeLoading(true);
            hideError();
            hideResults();
            
            // 显示进度
            progressSection.style.display = 'block';
            updateProgress(10, '正在开始批量分析...');
            
            const response = await fetch('/api/batch-analyze-selected', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_videos: selectedVideos,
                    report_language: document.getElementById('reportLanguage').value || 'en'
                })
            });
            
            updateProgress(50, '正在分析视频内容...');
            
            const result = await response.json();
            
            console.log('API响应:', result); // 调试日志
            
            if (result.success) {
                updateProgress(90, '正在生成报告...');
                setTimeout(() => {
                    updateProgress(100, '分析完成！');
                    setTimeout(() => {
                        displayBatchResults(result);
                    }, 1000);
                }, 500);
            } else {
                console.error('分析失败:', result.error); // 调试日志
                showError(result.error || '批量分析失败，请重试');
            }
        } catch (error) {
            showError('网络错误，请检查连接后重试');
            console.error('Batch analysis error:', error);
        } finally {
            setBatchAnalyzeLoading(false);
        }
    });
    
    // 设置搜索按钮加载状态
    function setSearchLoading(isLoading) {
        searchChannelBtn.disabled = isLoading;
        const btnText = searchChannelBtn.querySelector('.btn-text');
        const spinner = searchChannelBtn.querySelector('.loading-spinner');
        
        if (isLoading) {
            btnText.style.display = 'none';
            spinner.style.display = 'inline-block';
            // 启动搜索计时器
            startSearchTimer();
            // 防止表单重复提交
            channelSearchForm.style.pointerEvents = 'none';
            channelSearchForm.style.opacity = '0.6';
        } else {
            btnText.style.display = 'inline-block';
            spinner.style.display = 'none';
            // 停止搜索计时器
            stopSearchTimer();
            // 恢复表单状态
            channelSearchForm.style.pointerEvents = 'auto';
            channelSearchForm.style.opacity = '1';
        }
    }
    
    // 设置批量分析按钮加载状态
    function setBatchAnalyzeLoading(isLoading) {
        batchAnalyzeBtn.disabled = isLoading;
        const btnText = batchAnalyzeBtn.querySelector('.btn-text');
        const spinner = batchAnalyzeBtn.querySelector('.loading-spinner');
        
        if (isLoading) {
            btnText.style.display = 'none';
            spinner.style.display = 'inline-block';
            // 启动批量分析计时器
            startBatchTimer();
            
            // 在批量分析过程中禁用其他按钮
            searchChannelBtn.disabled = true;
            selectAllBtn.disabled = true;
            clearSelectionBtn.disabled = true;
            loadMoreBtn.disabled = true;
            
            // 禁用视频列表中的按钮
            const videoButtons = videoList.querySelectorAll('button');
            videoButtons.forEach(btn => btn.disabled = true);
            
            // 禁用视频选择
            const checkboxes = videoList.querySelectorAll('.video-checkbox');
            checkboxes.forEach(checkbox => checkbox.disabled = true);
            
        } else {
            btnText.style.display = 'inline-block';
            spinner.style.display = 'none';
            // 停止批量分析计时器
            stopBatchTimer();
            
            // 恢复其他按钮状态
            searchChannelBtn.disabled = false;
            selectAllBtn.disabled = false;
            clearSelectionBtn.disabled = false;
            loadMoreBtn.disabled = false;
            
            // 恢复视频列表中的按钮
            const videoButtons = videoList.querySelectorAll('button');
            videoButtons.forEach(btn => btn.disabled = false);
            
            // 恢复视频选择
            const checkboxes = videoList.querySelectorAll('.video-checkbox');
            checkboxes.forEach(checkbox => checkbox.disabled = false);
        }
    }
    
    // 更新进度
    function updateProgress(percentage, text) {
        document.getElementById('progressFill').style.width = percentage + '%';
        document.getElementById('progressText').textContent = text;
        
        if (percentage === 100) {
            setTimeout(() => {
                progressSection.style.display = 'none';
            }, 2000);
        }
    }
    
    // 显示批量分析结果
    function displayBatchResults(result) {
        console.log('批量分析结果:', result); // 调试日志
        
        const { report, cache_key } = result;
        
        // 保存cache_key到全局变量
        window.currentCacheKey = cache_key;
        
        if (!report) {
            showError('未收到分析报告数据');
            return;
        }
        
        console.log('报告数据:', report); // 调试日志
        console.log('raw_markdown_content 类型:', typeof report.raw_markdown_content); // 调试日志
        console.log('raw_markdown_content 内容:', report.raw_markdown_content); // 调试日志
        
        // 显示分析概览 - 使用AI返回的原始内容
        if (report.raw_markdown_content) {
            try {
                const formattedContent = formatContent(report.raw_markdown_content);
                console.log('格式化后的内容:', formattedContent); // 调试日志
                
                document.getElementById('overviewSummary').innerHTML = `
                    <h3>批量分析报告</h3>
                    <div class="full-report-content">
                        ${formattedContent}
                    </div>
                `;
                console.log('已设置overviewSummary内容'); // 调试日志
            } catch (error) {
                console.error('内容格式化失败:', error);
                document.getElementById('overviewSummary').innerHTML = `
                    <h3>批量分析报告</h3>
                    <div class="full-report-content">
                        <p>报告内容格式化失败，但分析已完成。请检查控制台获取原始数据。</p>
                    </div>
                `;
            }
        } else {
            document.getElementById('overviewSummary').innerHTML = `
                <h3>分析概览</h3>
                <div class="overview-stats">
                    <div class="stat-item">
                        <span class="stat-label">分析视频数量</span>
                        <span class="stat-value">${report.video_count || selectedVideos.length}个</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">生成时间</span>
                        <span class="stat-value">${report.generated_at || new Date().toLocaleString()}</span>
                    </div>
                </div>
                <div class="content-block">
                    <p>批量分析已完成，但未收到详细报告内容。</p>
                </div>
            `;
        }
        
        // 简化其他标签页的显示
        document.getElementById('overviewThemes').innerHTML = `
            <h3>分析说明</h3>
            <div class="content-block">
                <p>本次分析涵盖了${selectedVideos.length}个视频的内容，AI已对所有视频进行了综合分析。</p>
            </div>
        `;
        
        document.getElementById('overviewSentiment').innerHTML = `
            <h3>使用说明</h3>
            <div class="content-block">
                <p>所有分析结果基于AI对视频内容的理解，仅供参考。建议结合其他信息源进行投资决策。</p>
            </div>
        `;
        
        // 显示各视频分析 - 如果有的话
        displayIndividualAnalyses(report.individual_analyses || []);
        
        // 显示综合洞察 - 如果有的话
        displayConsolidatedInsights(report.consolidated_insights || {});
        
        // 显示投资建议 - 如果有的话
        displayRecommendations(report.investment_recommendation || {}, report.risk_assessment || {});
        
        // 显示结果区域
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        // 显示PDF下载按钮
                    showBatchPdfDownloadButton();
        
        if (typeof showNotification === 'function') {
            showNotification('批量内容分析完成！', 'success');
        }
    }
    
    function displayIndividualAnalyses(analyses) {
        const container = document.getElementById('individualAnalyses');
        
        if (!analyses || analyses.length === 0) {
            container.innerHTML = '<p>暂无单个视频分析数据</p>';
            return;
        }
        
        container.innerHTML = analyses.map((analysis, index) => `
            <div class="individual-analysis">
                <h4>视频 ${index + 1}: ${selectedVideos[index]?.title || '未知标题'}</h4>
                <div class="analysis-content">
                    <div class="content-block">
                        ${formatContent(analysis.analysis || analysis.summary || '暂无分析内容')}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    function displayConsolidatedInsights(insights) {
        document.getElementById('commonThemes').innerHTML = `
            <h3>综合洞察</h3>
            <div class="content-block">
                ${formatContent(insights.common_themes || '基于多个视频的综合分析，提取共同观点和投资逻辑。')}
            </div>
        `;
        
        document.getElementById('consensusViews').innerHTML = `
            <h3>共识观点</h3>
            <div class="content-block">
                ${formatContent(insights.consensus_views || '通过对比多个视频内容，识别出的一致性观点和投资建议。')}
            </div>
        `;
        
        document.getElementById('investmentOpportunities').innerHTML = `
            <h3>投资机会</h3>
            <div class="content-block">
                ${formatContent(insights.investment_opportunities || '从视频内容中识别出的潜在投资机会和关注点。')}
            </div>
        `;
    }
    
    function displayRecommendations(recommendations, riskAssessment) {
        document.getElementById('overallRecommendation').innerHTML = `
            <h3>整体建议</h3>
            <div class="recommendation-box">
                <div class="content-block">
                    ${formatContent(recommendations.overall || '基于多视频综合分析的投资建议')}
                </div>
            </div>
        `;
        
        document.getElementById('actionItems').innerHTML = `
            <h3>行动建议</h3>
            <div class="content-block">
                ${formatContent(recommendations.action_items || `
                <ul>
                    <li>持续关注视频中提到的投资主题</li>
                    <li>验证视频观点的准确性</li>
                    <li>结合其他信息源做出投资决策</li>
                </ul>
                `)}
            </div>
        `;
        
        document.getElementById('riskAssessment').innerHTML = `
            <h3>风险评估</h3>
            <div class="content-block">
                ${formatContent(riskAssessment.assessment || `
                <p><strong>风险等级:</strong> 中等风险</p>
                <p><strong>主要风险:</strong> 基于单一信息源，可能存在观点偏差</p>
                <p><strong>风险缓解:</strong> 建议结合多个信息源和专业分析</p>
                `)}
            </div>
        `;
    }
    
    // 工具函数
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
    
    // 全局函数供HTML调用
    window.openVideoUrl = function(url) {
        window.open(url, '_blank');
    };
    
    window.analyzeVideoSingle = function(url) {
        // 使用base64编码URL来避免502错误
        const encodedUrl = btoa(encodeURIComponent(url));
        const analyzeUrl = `/analyze?encoded_url=${encodedUrl}`;
        window.open(analyzeUrl, '_blank');
    };
    
    // 计时器相关变量和函数
    let searchTimerInterval = null;
    let batchTimerInterval = null;
    let searchStartTime = null;
    let batchStartTime = null;
    
    function startSearchTimer() {
        searchStartTime = Date.now();
        const timerDisplay = document.getElementById('searchTimerDisplay');
        
        if (timerDisplay) {
            searchTimerInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - searchStartTime) / 1000);
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
    
    function stopSearchTimer() {
        if (searchTimerInterval) {
            clearInterval(searchTimerInterval);
            searchTimerInterval = null;
        }
        
        const timerDisplay = document.getElementById('searchTimerDisplay');
        if (timerDisplay) {
            timerDisplay.textContent = '0s';
        }
    }
    
    function startBatchTimer() {
        batchStartTime = Date.now();
        const timerDisplay = document.getElementById('batchTimerDisplay');
        
        if (timerDisplay) {
            batchTimerInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - batchStartTime) / 1000);
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
    
    function stopBatchTimer() {
        if (batchTimerInterval) {
            clearInterval(batchTimerInterval);
            batchTimerInterval = null;
        }
        
        const timerDisplay = document.getElementById('batchTimerDisplay');
        if (timerDisplay) {
            timerDisplay.textContent = '0s';
        }
    }
});

// 格式化文本内容（支持Markdown）
function formatContent(content, useMarkdown = true) {
    if (!content) return '';
    
    // 如果content是数组，转换为字符串
    if (Array.isArray(content)) {
        content = content.join('\n');
    }
    
    // 确保content是字符串
    if (typeof content !== 'string') {
        content = String(content);
    }
    
    if (useMarkdown && typeof marked !== 'undefined') {
        try {
            return marked.parse(content);
        } catch (error) {
            console.error('Markdown解析失败:', error);
            return content.replace(/\n/g, '<br>');
        }
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

// 批量分析PDF下载相关函数
function showBatchPdfDownloadButton() {
    // 检查是否有cache_key
    if (!window.currentCacheKey) {
        console.warn('没有找到cache_key，无法下载PDF');
        return;
    }
    
    // 查找或创建PDF下载按钮
    let pdfButton = document.getElementById('batchPdfDownloadBtn');
    if (!pdfButton) {
        pdfButton = document.createElement('button');
        pdfButton.id = 'batchPdfDownloadBtn';
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
        pdfButton.addEventListener('click', downloadBatchPdfReport);
        
        // 插入到结果区域的开头
        const resultsSection = document.getElementById('batchResults');
        if (resultsSection) {
            resultsSection.insertBefore(pdfButton, resultsSection.firstChild);
        }
    }
    
    // 显示按钮
    pdfButton.style.display = 'inline-block';
    pdfButton.style.marginBottom = '20px';
}

function downloadBatchPdfReport() {
    if (!window.currentCacheKey) {
        alert('没有找到分析结果，请先进行分析');
        return;
    }
    
    const pdfButton = document.getElementById('batchPdfDownloadBtn');
    
    // 显示加载状态
    pdfButton.disabled = true;
    pdfButton.querySelector('.btn-text').style.display = 'none';
    pdfButton.querySelector('.loading-spinner').style.display = 'inline-block';
    
    // 创建下载链接
    const downloadUrl = `/api/download-pdf/${window.currentCacheKey}`;
    
    // 创建隐藏的a标签进行下载
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `batch_analysis_${window.currentCacheKey.substring(0, 8)}.pdf`;
    
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
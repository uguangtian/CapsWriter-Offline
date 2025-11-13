// CapsWriter-Offline 网页版主要JavaScript文件

// 全局变量
let socket = null;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recordingStartTime = null;
let recordingTimer = null;
let audioContext = null;
let analyser = null;
let microphone = null;
let dataArray = null;

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 初始化Socket.IO连接
    initializeSocket();
    
    // 初始化事件监听器
    initializeEventListeners();
    
    // 检查系统状态
    checkSystemStatus();
    
    // 定期更新系统状态
    setInterval(checkSystemStatus, 30000); // 每30秒检查一次
    
    // 将必要的函数和变量暴露到全局作用域
    window.socket = socket;
    window.isRecording = isRecording;
    window.startRecording = startRecording;
    window.stopRecording = stopRecording;
    window.pauseRecording = pauseRecording;
    window.handleFileSelect = handleFileSelect;
    window.displayFileInfo = displayFileInfo;
    window.clearSelectedFile = clearSelectedFile;
    window.showAlert = showAlert;
    window.isValidAudioFile = isValidAudioFile;
}

// 初始化Socket.IO连接
function initializeSocket() {
    socket = io();
    
    // 连接事件
    socket.on('connect', function() {
        console.log('Socket.IO连接已建立');
        showMessage('已连接到服务器', 'success');
    });
    
    socket.on('disconnect', function() {
        console.log('Socket.IO连接已断开');
        showMessage('与服务器连接断开', 'warning');
    });
    
    // 转录相关事件
    socket.on('transcription_start', function(data) {
        console.log('转录开始:', data);
        showMessage(`开始转录文件: ${data.filename}`, 'info');
        updateTranscriptionStatus('转录中...', 'info');
    });
    
    socket.on('transcription_result', function(data) {
        console.log('转录结果:', data);
        showMessage('转录完成', 'success');
        displayTranscriptionResult(data.text, data.filename);
        updateTranscriptionStatus('转录完成', 'success');
        addToHistory(data.text, data.filename);
    });
    
    socket.on('transcription_error', function(data) {
        console.log('转录错误:', data);
        showMessage(`转录失败: ${data.error}`, 'danger');
        updateTranscriptionStatus('转录失败', 'danger');
    });
    
    // 系统状态事件
    socket.on('system_status', function(data) {
        updateSystemStatus(data);
    });
}

// 初始化事件监听器
function initializeEventListeners() {
    // 录音控制按钮
    const startBtn = document.getElementById('start-recording-btn');
    const stopBtn = document.getElementById('stop-recording-btn');
    const pauseBtn = document.getElementById('pause-recording-btn');
    
    if (startBtn) {
        startBtn.addEventListener('click', startRecording);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopRecording);
    }
    
    if (pauseBtn) {
        pauseBtn.addEventListener('click', pauseRecording);
    }
    
    // 文件上传
    const fileInput = document.getElementById('audio-file');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // 拖拽上传
    const dropArea = document.querySelector('.drag-drop-area');
    if (dropArea) {
        dropArea.addEventListener('dragover', handleDragOver);
        dropArea.addEventListener('dragleave', handleDragLeave);
        dropArea.addEventListener('drop', handleFileDrop);
        dropArea.addEventListener('click', function() {
            if (fileInput) fileInput.click();
        });
    }
    
    // 转录按钮
    const transcribeBtn = document.getElementById('transcribe-btn');
    if (transcribeBtn) {
        transcribeBtn.addEventListener('click', transcribeFile);
    }
    
    // 本地文件路径输入
    const localPathInput = document.getElementById('local-file-path');
    if (localPathInput) {
        localPathInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                transcribeLocalFile();
            }
        });
    }
    
    // 本地文件转录按钮
    const transcribeLocalBtn = document.getElementById('transcribe-local-btn');
    if (transcribeLocalBtn) {
        transcribeLocalBtn.addEventListener('click', transcribeLocalFile);
    }
}

// 录音功能
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // 初始化音频上下文和分析器
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);
        
        analyser.fftSize = 256;
        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);
        
        // 开始音量监测
        updateVolumeBar();
        
        // 初始化MediaRecorder
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = function(event) {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = function() {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            
            // 如果启用了自动转录，则自动上传并转录
            const autoTranscribe = document.getElementById('auto-transcribe');
            if (autoTranscribe && autoTranscribe.checked) {
                uploadAndTranscribe(audioBlob);
            }
        };
        
        mediaRecorder.start();
        isRecording = true;
        recordingStartTime = Date.now();
        
        // 更新UI
        updateRecordingUI(true);
        updateRecordingStatus('录音中', 'danger');
        
        // 开始计时
        startRecordingTimer();
        
        showMessage('录音已开始', 'success');
        
    } catch (error) {
        console.error('录音启动失败:', error);
        showMessage('录音启动失败: ' + error.message, 'danger');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // 停止音频流
        if (mediaRecorder.stream) {
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        // 关闭音频上下文
        if (audioContext) {
            audioContext.close();
        }
        
        // 更新UI
        updateRecordingUI(false);
        updateRecordingStatus('录音完成', 'success');
        
        // 停止计时
        stopRecordingTimer();
        
        showMessage('录音已停止', 'info');
    }
}

function pauseRecording() {
    if (mediaRecorder && isRecording) {
        if (mediaRecorder.state === 'recording') {
            mediaRecorder.pause();
            updateRecordingStatus('录音暂停', 'warning');
            showMessage('录音已暂停', 'warning');
        } else if (mediaRecorder.state === 'paused') {
            mediaRecorder.resume();
            updateRecordingStatus('录音中', 'danger');
            showMessage('录音已恢复', 'info');
        }
    }
}

// 更新录音UI状态
function updateRecordingUI(recording) {
    const startBtn = document.getElementById('start-recording-btn');
    const stopBtn = document.getElementById('stop-recording-btn');
    const pauseBtn = document.getElementById('pause-recording-btn');
    
    if (startBtn) startBtn.disabled = recording;
    if (stopBtn) stopBtn.disabled = !recording;
    if (pauseBtn) pauseBtn.disabled = !recording;
}

// 更新录音状态显示
function updateRecordingStatus(status, type) {
    const statusElement = document.getElementById('recording-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `badge bg-${type}`;
    }
}

// 录音计时器
function startRecordingTimer() {
    recordingTimer = setInterval(function() {
        if (recordingStartTime) {
            const elapsed = Date.now() - recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            const timeElement = document.getElementById('recording-time');
            if (timeElement) {
                timeElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }
    }, 1000);
}

function stopRecordingTimer() {
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }
}

// 音量条更新
function updateVolumeBar() {
    if (analyser && dataArray) {
        analyser.getByteFrequencyData(dataArray);
        
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        
        const average = sum / dataArray.length;
        const volume = (average / 255) * 100;
        
        const volumeBar = document.getElementById('volume-bar');
        if (volumeBar) {
            volumeBar.style.width = volume + '%';
        }
        
        if (isRecording) {
            requestAnimationFrame(updateVolumeBar);
        }
    }
}

// 文件处理
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        displayFileInfo(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');
}

function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        displayFileInfo(file);
        
        // 更新文件输入
        const fileInput = document.getElementById('audio-file');
        if (fileInput) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
        }
    }
}

function displayFileInfo(file) {
    const fileInfoDiv = document.getElementById('file-info');
    if (fileInfoDiv) {
        fileInfoDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    <i class="fas fa-file-audio text-primary me-3" style="font-size: 1.5rem;"></i>
                    <div>
                        <div class="fw-bold">${file.name}</div>
                        <div class="text-muted small">${formatFileSize(file.size)}</div>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-secondary" onclick="clearFile()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        fileInfoDiv.style.display = 'block';
    }
}

function clearFile() {
    const fileInput = document.getElementById('audio-file');
    const fileInfoDiv = document.getElementById('file-info');
    
    if (fileInput) fileInput.value = '';
    if (fileInfoDiv) fileInfoDiv.style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 转录功能
function transcribeFile() {
    const fileInput = document.getElementById('audio-file');
    const file = fileInput ? fileInput.files[0] : null;
    
    if (!file) {
        showMessage('请先选择音频文件', 'warning');
        return;
    }
    
    uploadAndTranscribe(file);
}

function transcribeLocalFile() {
    const localPathInput = document.getElementById('local-file-path');
    const localPath = localPathInput ? localPathInput.value.trim() : '';
    
    if (!localPath) {
        showMessage('请输入本地文件路径', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('use_local_path', 'true');
    formData.append('local_path', localPath);
    formData.append('language', getSelectedLanguage());
    formData.append('model', getSelectedModel());
    
    fetch('/api/transcribe', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
        } else {
            showMessage(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('转录请求失败:', error);
        showMessage('转录请求失败: ' + error.message, 'danger');
    });
}

function uploadAndTranscribe(file) {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('use_local_path', 'false');
    formData.append('language', getSelectedLanguage());
    formData.append('model', getSelectedModel());
    
    fetch('/api/transcribe', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
        } else {
            showMessage(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('上传失败:', error);
        showMessage('上传失败: ' + error.message, 'danger');
    });
}

function getSelectedLanguage() {
    const languageSelect = document.getElementById('language-select');
    return languageSelect ? languageSelect.value : 'auto';
}

function getSelectedModel() {
    const modelSelect = document.getElementById('model-select');
    return modelSelect ? modelSelect.value : 'default';
}

// 转录结果显示
function displayTranscriptionResult(text, filename) {
    const resultDiv = document.getElementById('transcription-result');
    if (resultDiv) {
        resultDiv.textContent = text;
        resultDiv.style.display = 'block';
    }
    
    // 显示文件名
    const filenameDiv = document.getElementById('result-filename');
    if (filenameDiv && filename) {
        filenameDiv.textContent = `文件: ${filename}`;
        filenameDiv.style.display = 'block';
    }
}

function updateTranscriptionStatus(status, type) {
    const statusDiv = document.getElementById('transcription-status');
    if (statusDiv) {
        statusDiv.innerHTML = `<span class="badge bg-${type}">${status}</span>`;
    }
}

// 历史记录
function addToHistory(text, filename) {
    if (!text || text.trim() === '') return;
    
    const historyContainer = document.getElementById('transcription-history');
    if (!historyContainer) return;
    
    const timestamp = new Date().toLocaleString('zh-CN');
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';
    historyItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <div class="history-timestamp">${timestamp}</div>
            <div>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="copyToClipboard(this)" data-text="${text.replace(/"/g, '&quot;')}">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="removeHistoryItem(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <div class="history-filename text-muted small mb-2">${filename || '录音文件'}</div>
        <div class="history-text">${text}</div>
    `;
    
    historyContainer.insertBefore(historyItem, historyContainer.firstChild);
    
    // 限制历史记录数量
    const maxHistory = 50;
    const historyItems = historyContainer.children;
    if (historyItems.length > maxHistory) {
        for (let i = maxHistory; i < historyItems.length; i++) {
            historyContainer.removeChild(historyItems[i]);
        }
    }
}

function copyToClipboard(button) {
    const text = button.getAttribute('data-text');
    navigator.clipboard.writeText(text).then(function() {
        showMessage('已复制到剪贴板', 'success');
    }).catch(function(error) {
        console.error('复制失败:', error);
        showMessage('复制失败', 'danger');
    });
}

function removeHistoryItem(button) {
    const historyItem = button.closest('.history-item');
    if (historyItem) {
        historyItem.remove();
    }
}

// 系统状态检查
function checkSystemStatus() {
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            updateSystemStatus(data);
        })
        .catch(error => {
            console.error('系统状态检查失败:', error);
            updateSystemStatus({ status: 'error', message: '无法获取系统状态' });
        });
}

function updateSystemStatus(data) {
    const statusElement = document.getElementById('system-status');
    if (!statusElement) return;
    
    let statusClass = 'bg-secondary';
    let statusText = '未知状态';
    
    if (data.server_running && data.client_running) {
        statusClass = 'bg-success';
        statusText = '系统正常';
    } else if (data.server_running || data.client_running) {
        statusClass = 'bg-warning';
        statusText = '部分服务运行';
    } else {
        statusClass = 'bg-danger';
        statusText = '服务未运行';
    }
    
    statusElement.className = `badge ${statusClass}`;
    statusElement.innerHTML = `<i class="fas fa-circle me-1"></i>${statusText}`;
}

// 消息提示
function showMessage(message, type = 'info', duration = 5000) {
    const messageContainer = document.getElementById('message-container');
    if (!messageContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    messageContainer.appendChild(alertDiv);
    
    // 自动移除消息
    setTimeout(function() {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// 工具函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 验证音频文件格式
function isValidAudioFile(file) {
    const validTypes = [
        'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/mp4', 'audio/aac',
        'audio/ogg', 'audio/webm', 'audio/flac', 'audio/x-wav', 'audio/x-m4a'
    ];
    
    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m3u8', '.ts', '.vob', '.ogv', '.divx', '.xvid', '.rm', '.rmvb', '.mpg', '.mpeg', '.3gp', '.mxf', '.asf', '.dat','.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.amr', '.opus', '.ac3', '.eac3', '.dts', '.ape', '.alac', '.aiff', '.caf'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
    
    return validTypes.includes(file.type) || hasValidExtension;
}

// 清除选择的文件
function clearSelectedFile() {
    const fileInput = document.getElementById('audio-file-input');
    const dragDropArea = document.getElementById('drag-drop-area');
    const fileInfo = document.getElementById('file-info');
    
    if (fileInput) {
        fileInput.value = '';
    }
    
    if (dragDropArea && fileInfo) {
        // 显示拖拽区域，隐藏文件信息
        dragDropArea.style.display = 'block';
        fileInfo.style.display = 'none';
    }
    
    showAlert('已清除选择的文件', 'info');
}

// 显示提示信息（兼容showAlert函数）
function showAlert(message, type = 'info') {
    showMessage(message, type);
}

// 导出函数供全局使用
window.CapsWriterApp = {
    showMessage,
    showAlert,
    copyToClipboard,
    removeHistoryItem,
    clearFile,
    transcribeFile,
    transcribeLocalFile,
    isValidAudioFile,
    clearSelectedFile
};
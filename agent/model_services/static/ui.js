/**
 * UI 交互模块
 * 提供用户界面相关功能，包括动画、提示、布局调整等
 */

// DOM元素
let chatMessages;
let messageInput;
let sendButton;
let typingIndicator;
let chatPanel;
let settingsPanel;
let temperatureSlider;
let temperatureValue;
let temperatureDisplay;
let modelSelect;
let saveSettingsButton;

// 添加声音提示功能
const messageSound = new Audio('/static/message.mp3');

// 初始化DOM元素
function initDOMElements() {
    chatMessages = document.getElementById('chat-messages');
    messageInput = document.getElementById('message-input');
    sendButton = document.getElementById('send-button');
    typingIndicator = document.getElementById('typing-indicator');
    chatPanel = document.getElementById('chat-panel');
    settingsPanel = document.getElementById('settings-panel');
    temperatureSlider = document.getElementById('temperature-slider');
    temperatureValue = document.getElementById('temperature-value');
    temperatureDisplay = document.querySelector('.temperature-display');
    modelSelect = document.getElementById('model-select');
    saveSettingsButton = document.getElementById('save-settings');
}

// 标签页切换功能
function initTabSwitching() {
    document.querySelectorAll('.chat-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.chat-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const tabName = this.getAttribute('data-tab');
            if (tabName === 'chat') {
                chatPanel.style.display = 'flex';
                settingsPanel.style.display = 'none';
            } else if (tabName === 'settings') {
                chatPanel.style.display = 'none';
                settingsPanel.style.display = 'block';
            }
        });
    });
}

// 显示打字指示器
function showTypingIndicator() {
    typingIndicator.style.display = 'block';
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 隐藏打字指示器
function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// 添加消息到聊天界面
function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user-message' : 'assistant-message');
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // 处理代码块
    if (!isUser) {
        // 处理所有消息的换行和代码块
        messageDiv.innerHTML = content.replace(/\n/g, '<br>');
        if (content.includes('```')) {
            codeBlockManager.processCodeBlocks(messageDiv);
        }
    }
    
    return messageDiv;
}

// 播放消息提示音
function playMessageSound() {
    if (messageSound) {
        messageSound.play().catch(error => {
            console.error('播放声音失败:', error);
        });
    }
}

// 初始化UI事件
function initUIEvents() {
    // 初始化标签页切换
    initTabSwitching();
    
    // 发送按钮点击事件
    sendButton.addEventListener('click', () => {
        messageHandler.sendMessage();
    });
    
    // 输入框回车事件
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            messageHandler.sendMessage();
        }
    });
    
    // 温度滑块事件
    temperatureSlider.addEventListener('input', function() {
        const value = this.value;
        temperatureValue.textContent = `当前值: ${value}`;
        settingsManager.setTemperature(parseFloat(value));
    });
    
    // 保存设置按钮
    saveSettingsButton.addEventListener('click', function() {
        settingsManager.saveSettings();
        // 切换回聊天面板
        document.querySelector('.chat-tab[data-tab="chat"]').click();
    });
}

// 初始化UI
function init() {
    initDOMElements();
    initUIEvents();
}

// 导出UI模块函数
const uiManager = {
    init,
    addMessage,
    showTypingIndicator,
    hideTypingIndicator
};

const UI = {
    // 初始化 UI
    init() {
        this.setupResponsiveLayout();
        this.setupBootstrapComponents();
        this.createToastContainer();
    },

    // 设置响应式布局
    setupResponsiveLayout() {
        // 监听窗口大小变化
        window.addEventListener('resize', this.adjustLayout.bind(this));
        
        // 初始调整
        this.adjustLayout();
    },
    
    // 设置Bootstrap组件
    setupBootstrapComponents() {
        // 初始化所有tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // 初始化所有popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },
    
    // 创建Toast容器
    createToastContainer() {
        // 检查是否已存在
        let toastContainer = document.querySelector('.toast-container');
        
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
    },

    // 调整布局
    adjustLayout() {
        // 调整聊天容器高度
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            const navbar = document.querySelector('.navbar');
            const navbarHeight = navbar ? navbar.offsetHeight : 0;
            
            // 设置聊天容器高度
            chatContainer.style.height = `calc(100vh - ${navbarHeight}px)`;
        }
        
        // 调整消息容器滚动区域
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            const inputContainer = document.querySelector('.chat-input-container');
            const inputHeight = inputContainer ? inputContainer.offsetHeight : 0;
            
            // 确保足够的滚动空间
            messagesContainer.style.paddingBottom = `${inputHeight + 20}px`;
        }
    },
    
    // 显示加载状态
    showLoading(message = '加载中...') {
        // 检查是否已存在加载层
        let loadingOverlay = document.querySelector('.loading-overlay');
        
        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="loading-spinner"></div>
                <div class="loading-message text-white mt-3">${message}</div>
            `;
            document.body.appendChild(loadingOverlay);
        } else {
            loadingOverlay.querySelector('.loading-message').textContent = message;
            loadingOverlay.style.display = 'flex';
        }
    },
    
    // 隐藏加载状态
    hideLoading() {
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    },
    
    // 显示提示信息
    showToast(message, type = 'info', duration = 3000) {
        const container = document.querySelector('.toast-container');
        if (!container) return;
        
        // 创建Toast元素
        const toastElement = document.createElement('div');
        toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');
        
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        container.appendChild(toastElement);
        
        // 初始化Toast
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: duration
        });
        
        // 显示Toast
        toast.show();
        
        // 监听关闭事件，移除DOM元素
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },
    
    // 显示错误信息
    showError(message) {
        this.showToast(message, 'danger', 5000);
    },
    
    // 显示成功信息
    showSuccess(message) {
        this.showToast(message, 'success', 3000);
    },
    
    // 显示警告信息
    showWarning(message) {
        this.showToast(message, 'warning', 4000);
    },
    
    // 显示确认对话框
    showConfirm(message, onConfirm, onCancel) {
        // 检查是否已存在
        let confirmModal = document.getElementById('ui-confirm-modal');
        
        if (!confirmModal) {
            confirmModal = document.createElement('div');
            confirmModal.className = 'modal fade';
            confirmModal.id = 'ui-confirm-modal';
            confirmModal.setAttribute('tabindex', '-1');
            confirmModal.setAttribute('aria-hidden', 'true');
            
            confirmModal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">确认</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p id="ui-confirm-message"></p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="ui-confirm-cancel">取消</button>
                            <button type="button" class="btn btn-primary" id="ui-confirm-ok">确认</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(confirmModal);
        }
        
        // 设置消息内容
        const messageElement = document.getElementById('ui-confirm-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        // 获取按钮
        const okButton = document.getElementById('ui-confirm-ok');
        const cancelButton = document.getElementById('ui-confirm-cancel');
        
        // 移除旧的事件监听器
        const newOkButton = okButton.cloneNode(true);
        const newCancelButton = cancelButton.cloneNode(true);
        okButton.parentNode.replaceChild(newOkButton, okButton);
        cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
        
        // 初始化模态框
        const modal = new bootstrap.Modal(confirmModal);
        
        // 添加确认按钮事件
        newOkButton.addEventListener('click', () => {
            modal.hide();
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
        });
        
        // 添加取消按钮事件
        newCancelButton.addEventListener('click', () => {
            if (typeof onCancel === 'function') {
                onCancel();
            }
        });
        
        // 显示模态框
        modal.show();
    },
    
    // 添加浮动按钮
    addFloatingButton(icon, tooltip, onClick) {
        // 检查是否已存在
        const existingButtons = document.querySelectorAll('.floating-action-button');
        const offsetBottom = 16 + (existingButtons.length * 70); // 叠放按钮
        
        // 创建按钮
        const button = document.createElement('button');
        button.className = 'floating-action-button';
        button.innerHTML = `<i class="bi bi-${icon}"></i>`;
        button.title = tooltip;
        button.style.bottom = `${offsetBottom}px`;
        
        // 添加点击事件
        button.addEventListener('click', onClick);
        
        // 添加到文档
        document.body.appendChild(button);
        
        // 返回按钮元素，方便后续操作
        return button;
    },
    
    // 设置深色/浅色模式
    setThemeMode(darkMode) {
        document.body.setAttribute('data-theme', darkMode ? 'dark' : 'light');
        
        // 更新本地存储
        try {
            localStorage.setItem('theme_mode', darkMode ? 'dark' : 'light');
        } catch (e) {
            console.error('无法保存主题设置:', e);
        }
    },
    
    // 设置字体大小
    setFontSize(size) {
        // 验证尺寸
        const validSizes = ['small', 'medium', 'large'];
        if (!validSizes.includes(size)) {
            size = 'medium';
        }
        
        document.body.setAttribute('data-font-size', size);
        
        // 更新本地存储
        try {
            localStorage.setItem('font_size', size);
        } catch (e) {
            console.error('无法保存字体大小设置:', e);
        }
    },
    
    // 格式化日期时间
    formatDateTime(timestamp) {
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);
            
            // 显示相对时间
            if (diffMins < 1) return '刚刚';
            if (diffMins < 60) return `${diffMins}分钟前`;
            if (diffHours < 24) return `${diffHours}小时前`;
            if (diffDays < 7) return `${diffDays}天前`;
            
            // 显示完整日期
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            console.error('格式化日期时间失败:', e);
            return timestamp;
        }
    },
    
    // 创建标签
    createTab(parent, text, isActive = false, onClick) {
        const tab = document.createElement('div');
        tab.className = `custom-tab ${isActive ? 'active' : ''}`;
        tab.textContent = text;
        
        if (typeof onClick === 'function') {
            tab.addEventListener('click', onClick);
        }
        
        parent.appendChild(tab);
        return tab;
    },
    
    // 切换组件可见性
    toggleVisibility(element, visible) {
        if (!element) return;
        
        if (visible) {
            element.classList.remove('d-none');
            setTimeout(() => {
                element.classList.add('fade-in');
            }, 10);
        } else {
            element.classList.remove('fade-in');
            setTimeout(() => {
                element.classList.add('d-none');
            }, 300); // 匹配CSS过渡时间
        }
    },
    
    // 添加声音提示功能
    playMessageSound
};

// 导出模块
window.UI = UI;
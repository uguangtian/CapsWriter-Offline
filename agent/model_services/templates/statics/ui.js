/**
 * UI交互模块
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
    if (!isUser && content.includes('```')) {
        codeBlockManager.processCodeBlocks(messageDiv);
    }
    
    return messageDiv;
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
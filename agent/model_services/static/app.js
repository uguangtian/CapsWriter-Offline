/**
 * CapsWriter 聊天界面主应用
 * 负责初始化各模块、协调模块间的交互，以及处理核心业务逻辑
 */

// 应用状态管理
const AppState = {
    // 当前选中的模型ID
    currentModel: Settings.getSetting('currentModel'),
    // 当前温度设置
    temperature: Settings.getSetting('temperature'),
    // 聊天历史记录
    chatHistory: [],
    // 用户消息历史记录（用于上下键浏览）
    userMessageHistory: [],
    // 当前历史消息浏览位置
    historyIndex: -1,
    // 是否处于深色模式
    darkMode: Settings.getSetting('darkMode'),
    // 字体大小设置
    fontSize: Settings.getSetting('fontSize'),
    // 是否启用声音提示
    soundEnabled: Settings.getSetting('soundEnabled'),
    // 是否自动滚动到最新消息
    autoScroll: Settings.getSetting('autoScroll'),
    // 选中的消息ID（用于消息操作）
    selectedMessageId: null,
    
    // 初始化应用状态
    init() {
        // 从本地存储加载设置
        this.loadSettings();
        
        // 应用初始设置
        document.body.setAttribute('data-theme', this.darkMode ? 'dark' : 'light');
        document.body.setAttribute('data-font-size', this.fontSize);
        
        // 更新UI显示
        const currentModelEl = document.getElementById('current-model');
        if (currentModelEl) {
            currentModelEl.textContent = Settings.getModelName(this.currentModel);
        }
        
        const currentTempEl = document.getElementById('current-temperature');
        if (currentTempEl) {
            currentTempEl.textContent = this.temperature;
        }
        
        const temperatureSlider = document.getElementById('temperature-slider');
        if (temperatureSlider) {
            temperatureSlider.value = this.temperature;
        }
        
        const temperatureValue = document.getElementById('temperature-value');
        if (temperatureValue) {
            temperatureValue.textContent = this.temperature;
        }
        
        const fontSizeSelect = document.getElementById('font-size-select');
        if (fontSizeSelect) {
            fontSizeSelect.value = this.fontSize;
        }
        
        const soundToggle = document.getElementById('soundToggle');
        if (soundToggle) {
            soundToggle.checked = this.soundEnabled;
        }
        
        const autoScrollToggle = document.getElementById('autoScrollToggle');
        if (autoScrollToggle) {
            autoScrollToggle.checked = this.autoScroll;
        }
    },
    
    // 保存设置到本地存储
    saveSettings() {
        const settings = {
            darkMode: this.darkMode,
            fontSize: this.fontSize,
            temperature: this.temperature,
            currentModel: this.currentModel,
            soundEnabled: this.soundEnabled,
            autoScroll: this.autoScroll
        };
        
        Settings.updateSetting('darkMode', settings.darkMode);
        Settings.updateSetting('fontSize', settings.fontSize);
        Settings.updateSetting('temperature', settings.temperature);
        Settings.updateSetting('currentModel', settings.currentModel);
        Settings.updateSetting('soundEnabled', settings.soundEnabled);
        Settings.updateSetting('autoScroll', settings.autoScroll);
    },
    
    // 从本地存储加载设置
    loadSettings() {
        const settings = Settings.getSettings();
        
        this.darkMode = settings.darkMode;
        this.fontSize = settings.fontSize;
        this.temperature = settings.temperature;
        this.currentModel = settings.currentModel;
        this.soundEnabled = settings.soundEnabled;
        this.autoScroll = settings.autoScroll;
    },
    
    // 获取模型名称
    getModelName(modelId) {
        return Settings.getModelName(modelId);
    },
    
    // 添加用户消息到历史记录
    addUserMessageToHistory(message) {
        this.userMessageHistory.unshift(message);
        
        // 限制历史记录数量
        if (this.userMessageHistory.length > 50) {
            this.userMessageHistory.pop();
        }
        
        // 重置历史索引
        this.historyIndex = -1;
    },
    
    // 浏览历史记录
    browseHistory(direction) {
        if (this.userMessageHistory.length === 0) return null;
        
        if (direction === 'up') {
            this.historyIndex = Math.min(this.historyIndex + 1, this.userMessageHistory.length - 1);
        } else {
            this.historyIndex = Math.max(this.historyIndex - 1, -1);
        }
        
        return this.historyIndex === -1 ? '' : this.userMessageHistory[this.historyIndex];
    },
    
    // 添加消息到聊天历史
    addMessageToChat(message, isUser) {
        const timestamp = new Date().toISOString();
        const id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const messageObj = {
            id,
            content: message,
            role: isUser ? 'user' : 'assistant',
            timestamp
        };
        
        this.chatHistory.push(messageObj);
        return messageObj;
    },
    
    // 删除消息
    deleteMessage(messageId) {
        const index = this.chatHistory.findIndex(msg => msg.id === messageId);
        
        if (index !== -1) {
            this.chatHistory.splice(index, 1);
            return true;
        }
        
        return false;
    },
    
    // 编辑消息
    editMessage(messageId, newContent) {
        const message = this.chatHistory.find(msg => msg.id === messageId);
        
        if (message) {
            message.content = newContent;
            message.edited = true;
            return true;
        }
        
        return false;
    },
    
    // 清空聊天历史
    clearChat() {
        this.chatHistory = [];
    },
    
    // 导出聊天历史
    exportChat() {
        const formattedChat = this.chatHistory.map(msg => {
            return {
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp
            };
        });
        
        return JSON.stringify(formattedChat, null, 2);
    }
};

// 主应用模块
const App = {
    // 初始化应用
    init() {
        // 初始化应用状态
        AppState.init();
        
        // 获取必要的DOM元素
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.clearButton = document.getElementById('clear-button');
        this.uploadButton = document.getElementById('upload-button');
        this.messagesContainer = document.getElementById('messages-container');
        this.emptyState = document.getElementById('empty-state');
        
        // 设置事件监听器
        this.setupEventListeners();
        
        // 让输入框可聚焦
        this.chatInput.focus();
        
        // 让输入框输入时启用发送按钮
        this.updateSendButtonState();
    },
    
    // 设置事件监听器
    setupEventListeners() {
        // 输入框事件
        if (this.chatInput) {
            this.chatInput.addEventListener('input', () => {
                this.adjustTextareaHeight();
                this.updateSendButtonState();
            });
            
            this.chatInput.addEventListener('keydown', (e) => {
                // Enter键发送消息
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
                
                // Shift+Enter插入换行
                if (e.key === 'Enter' && e.shiftKey) {
                    // 默认行为即可
                }
                
                // 上下键浏览历史
                if (e.key === 'ArrowUp' && this.chatInput.value === '') {
                    const historyMessage = AppState.browseHistory('up');
                    if (historyMessage !== null) {
                        this.chatInput.value = historyMessage;
                        this.adjustTextareaHeight();
                        // 将光标移到末尾
                        setTimeout(() => {
                            this.chatInput.selectionStart = this.chatInput.selectionEnd = this.chatInput.value.length;
                        }, 0);
                    }
                }
                
                if (e.key === 'ArrowDown' && this.chatInput.value === AppState.userMessageHistory[AppState.historyIndex]) {
                    const historyMessage = AppState.browseHistory('down');
                    this.chatInput.value = historyMessage || '';
                    this.adjustTextareaHeight();
                }
            });
        }
        
        // 发送按钮事件
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => {
                this.sendMessage();
            });
        }
        
        // 清空聊天按钮事件
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => {
                this.showClearConfirmation();
            });
        }
        
        // 确认清空按钮事件
        const confirmClearBtn = document.getElementById('confirmClearBtn');
        if (confirmClearBtn) {
            confirmClearBtn.addEventListener('click', () => {
                this.clearChat();
                
                // 关闭确认对话框
                const modal = bootstrap.Modal.getInstance(document.getElementById('clearConfirmModal'));
                if (modal) {
                    modal.hide();
                }
            });
        }
        
        // 上传按钮事件
        if (this.uploadButton) {
            this.uploadButton.addEventListener('click', () => {
                // TODO: 实现文件上传功能
                UI.showToast('文件上传功能即将上线', 'info');
            });
        }
    },
    
    // 调整文本框高度
    adjustTextareaHeight() {
        if (!this.chatInput) return;
        
        this.chatInput.style.height = 'auto';
        const newHeight = Math.min(this.chatInput.scrollHeight, 200);
        this.chatInput.style.height = `${newHeight}px`;
    },
    
    // 更新发送按钮状态
    updateSendButtonState() {
        if (!this.sendButton || !this.chatInput) return;
        
        if (this.chatInput.value.trim() === '') {
            this.sendButton.disabled = true;
        } else {
            this.sendButton.disabled = false;
        }
    },
    
    // 根据模型类型构建请求数据
    buildRequestData(messageText, model, temperature) {
        const modelConfig = Settings.getModelConfig(model);
        if (!modelConfig) return null;

        // 提取模型提供商信息
        const provider = this.getModelProvider(model);

        switch (provider) {
            case 'anthropic':
                return {
                    messages: [{ role: 'user', content: messageText }],
                    model: model,
                    temperature: temperature,
                    stream: true
                };

            case 'openai':
                return {
                    messages: [{ role: 'user', content: messageText }],
                    model: model,
                    temperature: temperature,
                    stream: true
                };

            case 'deepseek':
                return {
                    model: model.includes('coder') ? 'deepseek-coder-33b-instruct' : 'deepseek-chat-33b',
                    messages: [{
                        role: 'user',
                        content: messageText
                    }],
                    temperature: temperature,
                    max_tokens: modelConfig.maxTokens,
                    top_p: 0.8,
                    stream: true,
                    stop: null
                };

            case 'doubao':
                return {
                    messages: [{ role: 'user', content: messageText }],
                    model: model,
                    temperature: temperature,
                    stream: true
                };

            case 'qianwen':
                return {
                    model: model,
                    input: {
                        messages: [{ role: 'user', content: messageText }]
                    },
                    parameters: {
                        temperature: temperature,
                        result_format: 'message',
                        stream: true
                    }
                };

            default:
                return {
                    messages: [{ role: 'user', content: messageText }],
                    model: model,
                    temperature: temperature,
                    stream: true
                };
        }
    },

    // 获取模型提供商
    getModelProvider(modelId) {
        if (modelId.includes('gpt-claude')) return 'anthropic';
        if (modelId.includes('claude')) return 'anthropic';
        if (modelId.includes('gpt')) return 'openai';
        if (modelId.includes('deepseek')) return 'deepseek';
        if (modelId.includes('doubao')) return 'doubao';
        if (modelId.includes('qianwen')) return 'qianwen';
        return 'unknown';
    },

    // 处理不同模型的响应格式
    processModelResponse(chunk, provider) {
        try {
            const data = JSON.parse(chunk.slice(6)); // 移除 "data: " 前缀

            switch (provider) {
                case 'anthropic':
                case 'openai':
                case 'deepseek':
                case 'doubao':
                    return data.content || '';

                case 'qianwen':
                    if (data.output && data.output.text) {
                        return data.output.text;
                    }
                    return '';

                default:
                    return data.content || '';
            }
        } catch (error) {
            console.error('处理响应数据出错:', error);
            return '';
        }
    },

    // 发送消息
    async sendMessage() {
        // 如果按钮被禁用，不执行任何操作
        if (this.sendButton && this.sendButton.disabled) {
            console.log('发送按钮被禁用，不执行发送操作');
            return;
        }
        
        const messageText = this.chatInput.value.trim();
        if (!messageText) {
            console.log('消息内容为空，不执行发送操作');
            return;
        }

        console.log('准备发送消息:', messageText);

        // 隐藏空状态
        if (this.emptyState) {
            this.emptyState.style.display = 'none';
        }

        // 清空输入框
        this.chatInput.value = '';
        this.chatInput.style.height = 'auto';
        this.updateSendButtonState();
        this.chatInput.focus();

        // 添加到历史记录
        AppState.addUserMessageToHistory(messageText);

        // 获取消息对象
        const msgObj = AppState.addMessageToChat(messageText, true);
        console.log('创建用户消息对象:', msgObj);

        // 显示用户消息
        MessageHandler.createMessage(messageText, true, msgObj.id);

        // 显示打字指示器
        MessageHandler.showTypingIndicator();

        try {
            // 获取当前模型配置
            const modelConfig = Settings.getModelConfig(AppState.currentModel);
            console.log('当前模型配置:', modelConfig);
            
            if (!modelConfig) {
                throw new Error('未找到模型配置');
            }

            // 获取模型提供商
            const provider = this.getModelProvider(AppState.currentModel);
            console.log('模型提供商:', provider);

            // 构建请求数据
            const requestData = this.buildRequestData(
                messageText,
                AppState.currentModel,
                AppState.temperature
            );
            console.log('构建的请求数据:', requestData);

            if (!requestData) {
                throw new Error('构建请求数据失败');
            }

            // 预创建助手消息容器
            const assistantMessageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const assistantMsgObj = AppState.addMessageToChat('', false);
            assistantMsgObj.id = assistantMessageId;
            console.log('创建助手消息容器:', assistantMessageId);

            MessageHandler.startNewMessage(assistantMessageId);

            // 构建发送到本地服务器的数据
            const serverRequestData = {
                message: messageText,
                temperature: AppState.temperature,
                model: AppState.currentModel,
                api_url: modelConfig.baseUrl,
                api_key: modelConfig.apiKey
            };
            console.log('准备发送请求到本地服务器:', serverRequestData);

            // 发送请求到本地服务器
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(serverRequestData)
            });
            console.log('收到响应状态:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}, statusText: ${response.statusText}`);
            }

            // 处理流式响应
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            console.log('开始读取流式响应');

            let done = false;
            let accumulatedContent = '';

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;

                if (done) {
                    console.log('流式响应结束');
                    // 流结束，完成消息
                    MessageHandler.finishMessage();
                    break;
                }

                // 解码响应数据
                const chunk = decoder.decode(value, { stream: true });
                console.log('收到数据块:', chunk);

                // 处理 SSE 格式数据
                const lines = chunk.split('\n\n');
                for (const line of lines) {
                    if (!line.trim()) continue;

                    if (line.startsWith('data: ')) {
                        console.log('处理SSE数据行:', line);
                        try {
                            const data = JSON.parse(line.slice(6)); // 移除 "data: " 前缀
                            if (data.content === '[DONE]') {
                                console.log('收到结束标记');
                                MessageHandler.finishMessage();
                            } else if (data.content) {
                                console.log('解析出的内容:', data.content);
                                // 更新消息内容
                                MessageHandler.handleStreamResponse(data.content);
                                accumulatedContent += data.content;
                            }
                        } catch (error) {
                            console.error('解析SSE数据出错:', error);
                        }
                    }
                }
            }

            // 更新助手消息内容
            assistantMsgObj.content = accumulatedContent;
            console.log('最终累积的内容长度:', accumulatedContent.length);

            // 隐藏打字指示器
            MessageHandler.hideTypingIndicator();

            // 播放声音提示（如果启用）
            if (AppState.soundEnabled) {
                UI.playMessageSound();
            }

        } catch (error) {
            console.error('发送消息出错:', error);
            console.error('错误堆栈:', error.stack);
            UI.showToast('发送消息失败: ' + error.message, 'error');

            // 隐藏打字指示器
            MessageHandler.hideTypingIndicator();

            // 显示错误消息
            MessageHandler.createMessage('抱歉，发送消息时出现错误: ' + error.message, false);
        }
    },
    
    // 显示清空确认对话框
    showClearConfirmation() {
        const modal = new bootstrap.Modal(document.getElementById('clearConfirmModal'));
        modal.show();
    },
    
    // 清空聊天
    clearChat() {
        // 清空状态
        AppState.clearChat();
        
        // 清空UI
        MessageHandler.clearMessages();
        
        // 显示空状态
        if (this.emptyState) {
            this.emptyState.style.display = 'flex';
        }
        
        // 显示提示
        UI.showToast('聊天已清空', 'success');
    }
};

// 导出模块
window.App = App;
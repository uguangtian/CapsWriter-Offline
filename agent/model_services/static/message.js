/**
 * 消息处理模块
 * 负责处理聊天消息的创建、更新、渲染和删除
 */

// 当前助手消息
let currentAssistantMessage = "";

// 发送消息函数
// 保存对话历史
let chatHistory = [];

function sendMessage() {
    const message = messageInput.value.trim();
    const fileInput = document.getElementById('file-input');
    
    // 处理文件上传
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const chunkSize = 1024 * 1024; // 1MB分块
        let offset = 0;
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
            fetch('/file', {
                method: 'POST',
                body: e.target.result,
                headers: {
                    'Content-Range': `bytes ${offset}-${offset + e.target.result.size}/${file.size}`,
                    'X-File-Name': encodeURIComponent(file.name)
                }
            }).then(response => {
                offset += e.target.result.size;
                if (offset < file.size) {
                    readNextChunk();
                }
            });
        };
        
        const readNextChunk = () => {
            const chunk = file.slice(offset, offset + chunkSize);
            reader.readAsArrayBuffer(chunk);
        };
        
        readNextChunk();
    }
    
    // 处理文本消息
    if (message === '') return;
    
    // 保存用户消息到历史
    chatHistory.push({role: 'user', content: message});
    uiManager.addMessage(message, true);
    messageInput.value = '';
    
    uiManager.showTypingIndicator();
    currentAssistantMessage = "";
    
    // 创建响应消息元素
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'assistant-message');
    chatMessages.appendChild(messageDiv);
    
    // 发送请求到服务器
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            message: message,
            temperature: settingsManager.getTemperature(),
            model: settingsManager.getModel()
        }),
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        uiManager.hideTypingIndicator();
        
        function processStream({ done, value }) {
            if (done) {
                // 处理完成后处理代码块
                if (currentAssistantMessage.includes('```')) {
                    codeBlockManager.processCodeBlocks(messageDiv);
                }
                return;
            }
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.content !== undefined) {
                            // 保存助手消息到历史
                            chatHistory.push({role: 'assistant', content: data.content});
                            currentAssistantMessage += data.content;
                            messageDiv.textContent = currentAssistantMessage;
                            // 实时处理新代码块
                            if (data.content.includes('```')) {
                                codeBlockManager.processCodeBlocks(messageDiv);
                            }
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e);
                    }
                }
            }
            
            return reader.read().then(processStream);
        }
        
        // 开始处理流
        return reader.read().then(processStream);
    })
    .catch(error => {
        console.error('Error fetching response:', error);
        uiManager.hideTypingIndicator();
        uiManager.addMessage('抱歉，发生了错误，请稍后再试。', false);
    });
}

// 导出消息处理模块
const messageHandler = {
    sendMessage
};

function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user-message' : 'assistant-message');
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; // 确保滚动到底部
    
    // 处理代码块
    if (!isUser && content.includes('```')) {
        codeBlockManager.processCodeBlocks(messageDiv);
    }
}

// 消息处理
const MessageHandler = {
    // 当前正在处理的消息元素
    currentMessageElement: null,
    // 当前消息的ID
    currentMessageId: null,
    // 当前消息的缓冲区
    messageBuffer: '',
    // 是否正在等待代码块结束
    waitingForCodeBlock: false,
    // 代码块缓冲区
    codeBuffer: '',
    // 当前代码块的语言
    currentCodeLang: '',
    // 消息计数器（用于生成唯一ID）
    messageCounter: 0,
    // 消息容器
    messagesContainer: null,
    // 打字指示器
    typingIndicator: null,

    // 初始化
    init() {
        this.messagesContainer = document.getElementById('messages-container');
        this.typingIndicator = document.getElementById('typing-indicator');
        
        // 确保元素存在
        if (!this.messagesContainer) {
            console.error('找不到消息容器元素 #messages-container');
            return;
        }
        
        if (!this.typingIndicator) {
            console.error('找不到打字指示器元素 #typing-indicator');
        }
        
        // 检查是否有历史消息需要处理
        this.processExistingMessages();
    },
    
    // 处理已存在的消息
    processExistingMessages() {
        if (!this.messagesContainer) return;
        
        const existingMessages = this.messagesContainer.querySelectorAll('.message');
        existingMessages.forEach(message => {
            if (message.classList.contains('assistant-message')) {
                // 处理代码块等特殊内容
                this.processMessageContent(message);
                
                // 添加消息操作按钮
                this.addMessageActions(message);
            }
        });
    },
    
    // 处理消息内容
    processMessageContent(messageElement) {
        if (!messageElement) return;
        
        // 如果有 marked 库可用，尝试渲染 Markdown
        if (window.marked && window.DOMPurify) {
            try {
                const content = messageElement.innerHTML;
                const rendered = marked.parse(content);
                // 使用 DOMPurify 净化 HTML
                const clean = DOMPurify.sanitize(rendered);
                messageElement.innerHTML = clean;
            } catch (error) {
                console.error('Markdown 渲染失败:', error);
            }
        }
        
        // 处理代码块
        if (window.CodeBlock) {
            CodeBlock.highlight(messageElement);
        }
    },
    
    // 创建新的消息元素
    createMessage(content, isUser = false, messageId = null) {
        if (!this.messagesContainer) return null;
        
        // 生成消息 ID
        const id = messageId || `msg-${Date.now()}-${this.messageCounter++}`;
        
        // 创建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : ''}`;
        messageDiv.dataset.id = id;
        
        // 创建消息头像
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        const avatarImg = document.createElement('img');
        avatarImg.src = isUser ? '/static/user-avatar.svg' : '/static/bot-avatar.svg';
        avatarImg.alt = isUser ? 'User' : 'Assistant';
        avatarDiv.appendChild(avatarImg);
        
        // 创建消息内容包装器
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';
        
        // 创建消息头部
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        
        // 创建发送者名称
        const senderDiv = document.createElement('div');
        senderDiv.className = 'message-sender';
        senderDiv.textContent = isUser ? '您' : 'CapsWriter 助手';
        
        // 创建消息时间
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());
        
        // 添加到消息头部
        headerDiv.appendChild(senderDiv);
        headerDiv.appendChild(timeDiv);
        
        // 创建消息气泡
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        
        // 处理内容
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        if (isUser) {
            // 用户消息使用文本内容
            textDiv.textContent = content;
        } else {
            // AI消息支持 Markdown
            if (content && window.marked && window.DOMPurify) {
                try {
                    const rendered = marked.parse(content);
                    // 使用 DOMPurify 净化 HTML
                    const clean = DOMPurify.sanitize(rendered);
                    textDiv.innerHTML = clean;
                } catch (error) {
                    console.error('Markdown 渲染失败:', error);
                    textDiv.textContent = content;
                }
            } else {
                textDiv.textContent = content;
            }
        }
        
        // 组装消息结构
        bubbleDiv.appendChild(textDiv);
        contentWrapper.appendChild(headerDiv);
        contentWrapper.appendChild(bubbleDiv);
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentWrapper);
        
        // 添加到容器
        if (this.typingIndicator) {
            this.messagesContainer.insertBefore(messageDiv, this.typingIndicator);
        } else {
            this.messagesContainer.appendChild(messageDiv);
        }
        
        // 添加消息操作按钮
        this.addMessageActions(messageDiv);
        
        // 处理代码块
        if (!isUser && window.CodeBlock) {
            setTimeout(() => CodeBlock.highlight(messageDiv), 0);
        }
        
        // 滚动到底部
        this.scrollToBottom();
        
        return messageDiv;
    },
    
    // 添加消息操作按钮
    addMessageActions(messageElement) {
        if (!messageElement) return;
        
        // 获取消息气泡
        const bubble = messageElement.querySelector('.message-bubble');
        if (!bubble) return;
        
        // 检查是否已有操作按钮
        if (bubble.querySelector('.message-actions')) {
            return;
        }
        
        // 创建操作按钮容器
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        // 复制按钮
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action-btn';
        copyBtn.innerHTML = '<i class="bi bi-clipboard"></i>';
        copyBtn.title = '复制消息';
        copyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.copyMessage(messageElement);
        });
        
        // 更多操作按钮（打开菜单）
        const moreBtn = document.createElement('button');
        moreBtn.className = 'message-action-btn';
        moreBtn.innerHTML = '<i class="bi bi-three-dots-vertical"></i>';
        moreBtn.title = '更多操作';
        moreBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            // 设置当前选中的消息ID
            if (window.AppState) {
                AppState.selectedMessageId = messageElement.dataset.id;
            }
            
            // 显示操作菜单（暂未实现）
            UI.showToast('更多操作即将推出', 'info');
        });
        
        // 添加按钮到容器
        actionsDiv.appendChild(copyBtn);
        actionsDiv.appendChild(moreBtn);
        
        // 添加到消息气泡
        bubble.appendChild(actionsDiv);
    },
    
    // 复制消息
    copyMessage(messageElement) {
        if (!messageElement) return;
        
        // 获取消息文本内容
        const textElement = messageElement.querySelector('.message-text');
        if (!textElement) return;
        
        const messageText = textElement.innerText;
        
        // 复制到剪贴板
        navigator.clipboard.writeText(messageText)
            .then(() => {
                if (window.UI) {
                    UI.showToast('已复制到剪贴板', 'success');
                } else {
                    alert('已复制到剪贴板');
                }
            })
            .catch(err => {
                console.error('复制失败:', err);
                if (window.UI) {
                    UI.showToast('复制失败，请手动复制', 'error');
                } else {
                    alert('复制失败，请手动复制');
                }
            });
    },
    
    // 开始新消息
    startNewMessage(messageId) {
        if (!this.messagesContainer) return null;
        
        // 创建消息结构
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.dataset.id = messageId;
        
        // 创建消息头像
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        const avatarImg = document.createElement('img');
        avatarImg.src = '/static/bot-avatar.svg';
        avatarImg.alt = 'Assistant';
        avatarDiv.appendChild(avatarImg);
        
        // 创建消息内容包装器
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';
        
        // 创建消息头部
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        
        // 创建发送者名称
        const senderDiv = document.createElement('div');
        senderDiv.className = 'message-sender';
        senderDiv.textContent = 'CapsWriter 助手';
        
        // 创建消息时间
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());
        
        // 添加到消息头部
        headerDiv.appendChild(senderDiv);
        headerDiv.appendChild(timeDiv);
        
        // 创建消息气泡
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        
        // 创建消息文本
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        // 组装消息结构
        bubbleDiv.appendChild(textDiv);
        contentWrapper.appendChild(headerDiv);
        contentWrapper.appendChild(bubbleDiv);
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentWrapper);
        
        // 添加到容器
        if (this.typingIndicator) {
            this.messagesContainer.insertBefore(messageDiv, this.typingIndicator);
        } else {
            this.messagesContainer.appendChild(messageDiv);
        }
        
        // 设置当前处理的消息
        this.currentMessageElement = textDiv;
        this.currentMessageId = messageId;
        this.messageBuffer = '';
        this.waitingForCodeBlock = false;
        this.codeBuffer = '';
        this.currentCodeLang = '';
        
        // 滚动到底部
        this.scrollToBottom();
        
        return messageDiv;
    },
    
    // 处理流式响应
    handleStreamResponse(content) {
        if (!this.currentMessageElement) {
            return;
        }

        // 处理代码块
        if (content.includes('```')) {
            this.handleCodeBlockContent(content);
        } else {
            // 普通文本处理
            this.handleRegularContent(content);
        }

        // 更新消息显示
        this.updateMessageDisplay();
    },

    // 处理代码块内容
    handleCodeBlockContent(content) {
        const codeBlockStart = /```(\w*)/;
        const codeBlockEnd = /```/;

        if (!this.waitingForCodeBlock && content.match(codeBlockStart)) {
            // 开始新的代码块
            const langMatch = content.match(codeBlockStart);
            const lang = langMatch && langMatch[1] ? langMatch[1] : '';
            this.waitingForCodeBlock = true;
            this.currentCodeLang = lang;
            this.codeBuffer = '';
            this.messageBuffer += content;
        } else if (this.waitingForCodeBlock && content.match(codeBlockEnd)) {
            // 结束代码块
            this.waitingForCodeBlock = false;
            this.messageBuffer += content;
        } else if (this.waitingForCodeBlock) {
            // 代码块内容
            this.codeBuffer += content;
            this.messageBuffer += content;
        } else {
            // 普通文本
            this.messageBuffer += content;
        }
    },

    // 处理普通内容
    handleRegularContent(content) {
        this.messageBuffer += content;
    },

    // 更新消息显示
    updateMessageDisplay() {
        if (!this.currentMessageElement) return;

        try {
            // 使用 Markdown 渲染，如果可用
            if (window.marked && window.DOMPurify) {
                const rendered = marked.parse(this.messageBuffer);
                // 使用 DOMPurify 净化 HTML
                const clean = DOMPurify.sanitize(rendered);
                this.currentMessageElement.innerHTML = clean;
            } else {
                // 备用方案：简单替换换行符
                this.currentMessageElement.textContent = this.messageBuffer;
            }
            
            // 处理代码块
            if (window.CodeBlock) {
                const messageContainer = this.currentMessageElement.closest('.message');
                if (messageContainer) {
                    setTimeout(() => CodeBlock.highlight(messageContainer), 0);
                }
            }
            
            // 自动滚动到底部
            if (window.AppState && AppState.autoScroll) {
                this.scrollToBottom();
            }
        } catch (error) {
            console.error('更新消息显示失败:', error);
            // 使用文本备用方案
            this.currentMessageElement.textContent = this.messageBuffer;
        }
    },

    // 完成消息处理
    finishMessage() {
        if (!this.currentMessageElement) return;
        
        // 更新AppState的消息内容，如果可用
        if (window.AppState && this.currentMessageId) {
            const message = AppState.chatHistory.find(msg => msg.id === this.currentMessageId);
            if (message) {
                message.content = this.messageBuffer;
            }
        }
        
        // 最终更新一次显示
        this.updateMessageDisplay();
        
        // 添加消息操作按钮
        const messageContainer = this.currentMessageElement.closest('.message');
        if (messageContainer) {
            this.addMessageActions(messageContainer);
        }
        
        // 重置消息处理状态
        this.currentMessageElement = null;
        this.currentMessageId = null;
        this.messageBuffer = '';
        this.waitingForCodeBlock = false;
        this.codeBuffer = '';
        this.currentCodeLang = '';
    },

    // 显示打字指示器
    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
            this.scrollToBottom();
        }
    },

    // 隐藏打字指示器
    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    },

    // 滚动到底部
    scrollToBottom() {
        if (this.messagesContainer) {
            // 使用平滑滚动
            this.messagesContainer.scrollTo({
                top: this.messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        }
    },

    // 清空消息
    clearMessages() {
        if (!this.messagesContainer) return;
        
        // 保留打字指示器，移除其他内容
        const children = Array.from(this.messagesContainer.children);
        for (const child of children) {
            if (child !== this.typingIndicator && child.id !== 'empty-state') {
                this.messagesContainer.removeChild(child);
            }
        }
    },
    
    // 格式化时间
    formatTime(date) {
        if (!date) return '';
        
        try {
            // 简单地返回 HH:MM 格式
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            return `${hours}:${minutes}`;
        } catch (e) {
            console.error('格式化时间出错:', e);
            return '';
        }
    }
};

// 导出模块
window.MessageHandler = MessageHandler;
/**
 * 消息处理模块
 */

// 对话历史上下文
let chatHistory = [];

// 当前助手消息
let currentAssistantMessage = "";

// 发送消息函数
function sendMessage() {
    const message = messageInput.value.trim();
    if (message === '') return;
    
    console.log('发送新消息:', message);
    
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
    const requestParams = { 
        message: message,
        temperature: settingsManager.getTemperature(),
        model: settingsManager.getModel()
    };
    console.log('请求参数:', requestParams);
    
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestParams),
    })
    .then(response => {
        console.log('收到服务器响应:', response.status);
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
                            console.log('收到助手消息:', data.content);
                            // 保存助手消息到历史
                            chatHistory.push({role: 'assistant', content: data.content});
                            currentAssistantMessage += data.content;
                            messageDiv.textContent = currentAssistantMessage;
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
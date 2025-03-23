/**
 * 代码块处理模块
 * 处理聊天消息中代码块的高亮显示和格式化
 */

const CodeBlock = {
    // 代码高亮库是否已加载
    highlightjsLoaded: false,
    
    // 初始化代码块处理
    init() {
        // 加载代码高亮所需的资源
        this.loadHighlightResources();
        
        // 设置复制代码块的事件处理
        this.setupCodeCopyEvents();
    },
    
    // 加载代码高亮所需的资源
    loadHighlightResources() {
        // 如果已经加载过，则不再重复加载
        if (this.highlightjsLoaded) {
            return;
        }
        
        // 加载 highlight.js CSS
        const highlightCSS = document.createElement('link');
        highlightCSS.rel = 'stylesheet';
        highlightCSS.href = 'https://cdn.jsdelivr.net/npm/highlight.js@11.7.0/styles/github-dark.min.css';
        document.head.appendChild(highlightCSS);
        
        // 加载 highlight.js
        const highlightScript = document.createElement('script');
        highlightScript.src = 'https://cdn.jsdelivr.net/npm/highlight.js@11.7.0/highlight.min.js';
        document.head.appendChild(highlightScript);
        
        // 设置加载完成后的回调
        highlightScript.onload = () => {
            this.highlightjsLoaded = true;
            // 高亮当前页面中的所有代码块
            this.highlightAll();
        };
    },
    
    // 高亮指定元素中的所有代码块
    highlight(element) {
        if (!this.highlightjsLoaded || !window.hljs) {
            // 如果高亮库尚未加载完成，则等待加载完成后再执行
            setTimeout(() => this.highlight(element), 100);
            return;
        }
        
        try {
            // 查找元素中的所有代码块
            const codeBlocks = element.querySelectorAll('pre code');
            codeBlocks.forEach(block => {
                // 如果代码块尚未高亮，则进行高亮处理
                if (!block.classList.contains('hljs')) {
                    window.hljs.highlightElement(block);
                    
                    // 为代码块添加复制按钮
                    this.addCopyButton(block.parentElement);
                    
                    // 为代码块添加语言标签
                    this.addLanguageLabel(block);
                }
            });
        } catch (e) {
            console.error('高亮代码块时出错:', e);
        }
    },
    
    // 高亮页面中的所有代码块
    highlightAll() {
        if (!this.highlightjsLoaded || !window.hljs) {
            // 如果高亮库尚未加载完成，则等待加载完成后再执行
            setTimeout(() => this.highlightAll(), 100);
            return;
        }
        
        try {
            // 高亮所有代码块
            window.hljs.highlightAll();
            
            // 为所有代码块添加复制按钮和语言标签
            const codeBlocks = document.querySelectorAll('pre code');
            codeBlocks.forEach(block => {
                this.addCopyButton(block.parentElement);
                this.addLanguageLabel(block);
            });
        } catch (e) {
            console.error('高亮所有代码块时出错:', e);
        }
    },
    
    // 为代码块添加复制按钮
    addCopyButton(preElement) {
        // 检查是否已经添加过复制按钮
        if (preElement.querySelector('.code-copy-button')) {
            return;
        }
        
        // 创建复制按钮
        const copyButton = document.createElement('button');
        copyButton.className = 'code-copy-button';
        copyButton.innerHTML = '<i class="bi bi-clipboard"></i>';
        copyButton.title = '复制代码';
        
        // 将复制按钮添加到代码块中
        preElement.appendChild(copyButton);
    },
    
    // 为代码块添加语言标签
    addLanguageLabel(codeElement) {
        // 获取代码块的父元素
        const preElement = codeElement.parentElement;
        
        // 检查是否已经添加过语言标签
        if (preElement.querySelector('.code-language-label')) {
            return;
        }
        
        // 获取代码块的语言
        let language = '';
        for (const className of codeElement.classList) {
            if (className.startsWith('language-')) {
                language = className.replace('language-', '');
                break;
            }
        }
        
        // 如果找到了语言，则添加语言标签
        if (language) {
            const languageLabel = document.createElement('div');
            languageLabel.className = 'code-language-label';
            languageLabel.textContent = language;
            preElement.appendChild(languageLabel);
        }
    },
    
    // 设置复制代码块的事件处理
    setupCodeCopyEvents() {
        // 使用事件委托，监听复制按钮的点击事件
        document.addEventListener('click', event => {
            // 检查点击的元素是否为复制按钮
            const copyButton = event.target.closest('.code-copy-button');
            if (copyButton) {
                // 获取代码块元素
                const preElement = copyButton.closest('pre');
                const codeElement = preElement.querySelector('code');
                
                // 调用复制代码的方法
                this.copyCodeToClipboard(codeElement, copyButton);
            }
        });
    },
    
    // 复制代码到剪贴板
    copyCodeToClipboard(codeElement, copyButton) {
        try {
            // 获取代码内容
            const codeText = codeElement.textContent || '';
            
            // 复制到剪贴板
            navigator.clipboard.writeText(codeText)
                .then(() => {
                    // 复制成功，更新按钮样式
                    copyButton.innerHTML = '<i class="bi bi-check2"></i>';
                    copyButton.classList.add('copied');
                    
                    // 显示提示
                    UI.showSuccess('代码已复制到剪贴板');
                    
                    // 1.5秒后恢复按钮样式
                    setTimeout(() => {
                        copyButton.innerHTML = '<i class="bi bi-clipboard"></i>';
                        copyButton.classList.remove('copied');
                    }, 1500);
                })
                .catch(err => {
                    console.error('复制失败:', err);
                    UI.showError('复制代码失败');
                });
        } catch (e) {
            console.error('复制代码时出错:', e);
            UI.showError('复制代码失败');
        }
    },
    
    // 转义HTML特殊字符
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },
    
    // 识别代码块中的语言
    detectLanguage(code) {
        if (!this.highlightjsLoaded || !window.hljs) {
            return '';
        }
        
        try {
            // 使用 highlight.js 自动检测语言
            const result = window.hljs.highlightAuto(code);
            return result.language || '';
        } catch (e) {
            console.error('检测代码语言时出错:', e);
            return '';
        }
    },
    
    // 格式化代码
    formatCode(code, language = '') {
        // 转义HTML特殊字符
        const escapedCode = this.escapeHtml(code);
        
        // 如果没有指定语言，则尝试检测
        if (!language && this.highlightjsLoaded) {
            language = this.detectLanguage(code);
        }
        
        // 创建格式化后的HTML
        const languageClass = language ? ` class="language-${language}"` : '';
        return `<pre><code${languageClass}>${escapedCode}</code></pre>`;
    }
};

// 导出模块
window.CodeBlock = CodeBlock;
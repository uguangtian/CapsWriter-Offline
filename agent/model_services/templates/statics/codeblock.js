/**
 * 代码块处理模块
 */

// 处理代码块函数
function processCodeBlocks(element) {
    if (!element) return;
    
    const content = element.innerHTML;
    if (content.includes('```')) {
        const codeRegex = /```(?:(\w+)\n)?([\s\S]*?)```/g;
        let newContent = content;
        let match;
        
        while ((match = codeRegex.exec(content)) !== null) {
            const language = match[1] || '';
            const code = match[2];
            const replacement = `<div class="code-block">
                <button class="copy-button" onclick="copyCode(this)">复制</button>
                <pre><code class="${language}">${code}</code></pre>
            </div>`;
            
            newContent = newContent.replace(match[0], replacement);
        }
        
        element.innerHTML = newContent;
    }
}

// 复制代码函数
function copyCode(button) {
    const code = button.nextElementSibling.querySelector('code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        button.textContent = '已复制';
        setTimeout(() => button.textContent = '复制', 2000);
    });
}

// 导出代码块处理模块
const codeBlockManager = {
    processCodeBlocks,
    copyCode
};
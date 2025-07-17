/**
 * 应用初始化模块
 */

// 当文档加载完成后初始化应用
document.addEventListener('DOMContentLoaded', function() {
    // 初始化UI
    uiManager.init();
    
    // 设置复制代码函数为全局函数
    window.copyCode = codeBlockManager.copyCode;
});
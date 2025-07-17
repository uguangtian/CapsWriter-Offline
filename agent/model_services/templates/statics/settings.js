/**
 * 设置管理模块
 */

// 设置变量
let currentTemperature = 1;
let currentModel = "gpt-claude-3-7-sonnet-thinking-20250219-vision";

// 设置温度值
function setTemperature(value) {
    currentTemperature = value;
}

// 设置模型
function setModel(model) {
    currentModel = model;
}

// 保存设置
function saveSettings() {
    // 更新温度显示
    document.querySelector('.temperature-display').textContent = `温度: ${currentTemperature}`;
    // 获取当前选择的模型
    currentModel = document.getElementById('model-select').value;
}

// 获取当前温度
function getTemperature() {
    return currentTemperature;
}

// 获取当前模型
function getModel() {
    return currentModel;
}

// 导出设置管理模块
const settingsManager = {
    setTemperature,
    setModel,
    saveSettings,
    getTemperature,
    getModel
};
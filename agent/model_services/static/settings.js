/**
 * 设置管理模块
 * 负责处理应用的所有配置项，包括主题、字体大小、声音、API设置等
 */

const Settings = {
    // 默认设置
    defaults: {
        darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
        fontSize: 'medium',
        temperature: 0.7,
        currentModel: 'gpt-claude-3-7-sonnet-thinking-20250219-vision',
        soundEnabled: true,
        autoScroll: true,
        // API提供商配置
        providers: [
            {
                id: 'anthropic',
                name: 'Anthropic Claude',
                baseUrl: 'http://localhost:8000/v1/chat/completions',
                apiKey: '',
                models: [
                    {
                        id: 'gpt-claude-3-7-sonnet-thinking-20250219-vision',
                        name: 'Claude 3.7 Sonnet',
                        maxTokens: 4096
                    }
                ],
                description: 'Anthropic的Claude系列模型',
                authType: 'x-api-key',
                requestFormat: 'anthropic'
            },
            {
                id: 'openai',
                name: 'OpenAI',
                baseUrl: 'https://api.openai.com/v1/chat/completions',
                apiKey: '',
                models: [
                    {
                        id: 'gpt-4',
                        name: 'GPT-4',
                        maxTokens: 4096
                    }
                ],
                description: 'OpenAI的GPT系列模型',
                authType: 'bearer',
                requestFormat: 'openai'
            },
            {
                id: 'deepseek',
                name: 'Deepseek',
                baseUrl: 'https://api.deepseek.com/v1/chat/completions',
                apiKey: '',
                models: [
                    {
                        id: 'deepseek-chat',
                        name: 'Deepseek Chat',
                        maxTokens: 8192
                    }
                ],
                description: 'Deepseek开源大模型',
                authType: 'bearer',
                requestFormat: 'openai'
            },
            {
                id: 'doubao',
                name: '豆包',
                baseUrl: 'https://api.doubao.com/v1/chat/completions',
                apiKey: '',
                models: [
                    {
                        id: 'doubao-chat',
                        name: '豆包对话',
                        maxTokens: 4096
                    }
                ],
                description: '豆包AI对话模型',
                authType: 'bearer',
                requestFormat: 'openai'
            },
            {
                id: 'qianwen',
                name: '通义千问',
                baseUrl: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                apiKey: '',
                models: [
                    {
                        id: 'qianwen-max',
                        name: '千问Max',
                        maxTokens: 6144
                    }
                ],
                description: '阿里通义千问系列模型',
                authType: 'bearer',
                requestFormat: 'qianwen'
            }
        ]
    },

    // 初始化设置
    init() {
        // 加载设置
        this.loadSettings();
        
        // 设置事件监听器
        this.setupEventListeners();
        
        // 应用初始设置
        this.applySettings();
        
        // 初始化模型列表
        this.initializeModelList();
    },

    // 初始化模型列表
    initializeModelList() {
        const modelList = document.getElementById('model-list');
        if (!modelList) return;

        // 清空现有列表
        modelList.innerHTML = '';

        // 添加服务商和模型选项
        this.defaults.providers.forEach(provider => {
            const providerSection = document.createElement('div');
            providerSection.className = 'provider-section mb-4';
            providerSection.innerHTML = `
                <div class="provider-header d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0">${provider.name}</h6>
                    <button class="btn btn-sm btn-outline-primary add-model-btn" data-provider-id="${provider.id}">
                        <i class="bi bi-plus"></i> 添加模型
                    </button>
                </div>
                <div class="provider-info mb-3">
                    <p class="text-muted small mb-2">${provider.description}</p>
                    <div class="mb-2">
                        <small class="text-muted">API Base URL:</small>
                        <input type="text" class="form-control form-control-sm mt-1 api-url-input" 
                               value="${provider.baseUrl}" data-provider-id="${provider.id}">
                    </div>
                    <div>
                        <small class="text-muted">API Key:</small>
                        <input type="password" class="form-control form-control-sm mt-1 api-key-input" 
                               value="${provider.apiKey}" data-provider-id="${provider.id}">
                    </div>
                </div>
                <div class="models-container" data-provider-id="${provider.id}">
                    ${provider.models.map(model => this.createModelItemHtml(provider, model)).join('')}
                </div>
            `;

            // 添加事件监听器
            const addModelBtn = providerSection.querySelector('.add-model-btn');
            addModelBtn.addEventListener('click', () => this.showAddModelModal(provider.id));

            // API URL 和 Key 的变更监听器
            const apiUrlInput = providerSection.querySelector('.api-url-input');
            const apiKeyInput = providerSection.querySelector('.api-key-input');

            apiUrlInput.addEventListener('change', () => {
                this.updateProviderConfig(provider.id, 'baseUrl', apiUrlInput.value);
            });

            apiKeyInput.addEventListener('change', () => {
                this.updateProviderConfig(provider.id, 'apiKey', apiKeyInput.value);
            });

            // 为每个模型添加事件监听器
            provider.models.forEach(model => {
                this.addModelEventListeners(providerSection, provider.id, model.id);
            });

            modelList.appendChild(providerSection);
        });
    },

    // 创建模型项的HTML
    createModelItemHtml(provider, model) {
        return `
            <div class="model-item p-3 border rounded mb-2" data-model-id="${model.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="mb-2">
                            <small class="text-muted">模型ID:</small>
                            <input type="text" class="form-control form-control-sm mt-1 model-id-input" 
                                   value="${model.id}" data-provider-id="${provider.id}" data-model-id="${model.id}">
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">显示名称:</small>
                            <input type="text" class="form-control form-control-sm mt-1 model-name-input" 
                                   value="${model.name}" data-provider-id="${provider.id}" data-model-id="${model.id}">
                        </div>
                        <div>
                            <small class="text-muted">最大Token数:</small>
                            <input type="number" class="form-control form-control-sm mt-1 model-tokens-input" 
                                   value="${model.maxTokens}" data-provider-id="${provider.id}" data-model-id="${model.id}">
                        </div>
                    </div>
                    <div class="ms-3 d-flex flex-column">
                        <button class="btn btn-sm btn-primary mb-2 select-model-btn" data-model-id="${model.id}">
                            ${this.defaults.currentModel === model.id ? '当前使用中' : '选择'}
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-model-btn" data-model-id="${model.id}">
                            删除
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    // 为模型添加事件监听器
    addModelEventListeners(container, providerId, modelId) {
        const modelItem = container.querySelector(`[data-model-id="${modelId}"]`);
        if (!modelItem) return;

        // 选择按钮
        const selectBtn = modelItem.querySelector('.select-model-btn');
        selectBtn.addEventListener('click', () => this.changeModel(providerId, modelId));

        // 删除按钮
        const deleteBtn = modelItem.querySelector('.delete-model-btn');
        deleteBtn.addEventListener('click', () => this.deleteModel(providerId, modelId));

        // 输入框变更事件
        const idInput = modelItem.querySelector('.model-id-input');
        const nameInput = modelItem.querySelector('.model-name-input');
        const tokensInput = modelItem.querySelector('.model-tokens-input');

        idInput.addEventListener('change', () => {
            this.updateModelConfig(providerId, modelId, 'id', idInput.value);
        });

        nameInput.addEventListener('change', () => {
            this.updateModelConfig(providerId, modelId, 'name', nameInput.value);
        });

        tokensInput.addEventListener('change', () => {
            this.updateModelConfig(providerId, modelId, 'maxTokens', parseInt(tokensInput.value));
        });
    },

    // 更新服务商配置
    updateProviderConfig(providerId, key, value) {
        const provider = this.defaults.providers.find(p => p.id === providerId);
        if (provider) {
            provider[key] = value;
            this.saveSettings();
        }
    },

    // 更新模型配置
    updateModelConfig(providerId, modelId, key, value) {
        const provider = this.defaults.providers.find(p => p.id === providerId);
        if (!provider) return;

        const model = provider.models.find(m => m.id === modelId);
        if (model) {
            if (key === 'id' && this.defaults.currentModel === modelId) {
                this.defaults.currentModel = value;
            }
            model[key] = value;
            this.saveSettings();
            this.initializeModelList(); // 重新渲染列表以更新显示
        }
    },

    // 显示添加模型对话框
    showAddModelModal(providerId) {
        const provider = this.defaults.providers.find(p => p.id === providerId);
        if (!provider) return;

        const modalHtml = `
            <div class="modal fade" id="addModelModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">添加${provider.name}模型</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="add-model-form">
                                <div class="mb-3">
                                    <label class="form-label">模型ID</label>
                                    <input type="text" class="form-control" id="new-model-id" required>
                                    <small class="text-muted">模型的唯一标识符，如 gpt-4-turbo</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">显示名称</label>
                                    <input type="text" class="form-control" id="new-model-name" required>
                                    <small class="text-muted">在界面上显示的名称</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">最大Token数</label>
                                    <input type="number" class="form-control" id="new-model-max-tokens" value="4096">
                                    <small class="text-muted">模型支持的最大token数量</small>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="save-new-model-btn">保存</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 添加模态框到文档
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer);

        // 获取模态框实例
        const modal = new bootstrap.Modal(document.getElementById('addModelModal'));

        // 保存按钮事件
        const saveBtn = document.getElementById('save-new-model-btn');
        saveBtn.addEventListener('click', () => {
            const newModel = {
                id: document.getElementById('new-model-id').value,
                name: document.getElementById('new-model-name').value,
                maxTokens: parseInt(document.getElementById('new-model-max-tokens').value)
            };

            try {
                this.addModel(providerId, newModel);
                modal.hide();
                if (window.UI) {
                    UI.showToast('新模型添加成功', 'success');
                }
            } catch (error) {
                if (window.UI) {
                    UI.showToast(error.message, 'error');
                }
            }
        });

        // 显示模态框
        modal.show();

        // 模态框关闭时清理
        document.getElementById('addModelModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    },

    // 添加新模型
    addModel(providerId, modelConfig) {
        const provider = this.defaults.providers.find(p => p.id === providerId);
        if (!provider) {
            throw new Error('未找到服务商');
        }

        // 验证必要字段
        if (!modelConfig.id || !modelConfig.name) {
            throw new Error('模型配置缺少必要字段');
        }

        // 检查ID是否已存在
        if (provider.models.some(m => m.id === modelConfig.id)) {
            throw new Error('模型ID已存在');
        }

        // 添加新模型
        provider.models.push(modelConfig);
        this.saveSettings();
        this.initializeModelList();
    },

    // 删除模型
    deleteModel(providerId, modelId) {
        const provider = this.defaults.providers.find(p => p.id === providerId);
        if (!provider) return;

        // 不允许删除当前使用的模型
        if (modelId === this.defaults.currentModel) {
            if (window.UI) {
                UI.showToast('无法删除当前使用的模型', 'error');
            }
            return;
        }

        const index = provider.models.findIndex(m => m.id === modelId);
        if (index !== -1) {
            provider.models.splice(index, 1);
            this.saveSettings();
            this.initializeModelList();
        }
    },

    // 更改模型
    changeModel(providerId, modelId) {
        const provider = this.defaults.providers.find(p => p.id === providerId);
        if (!provider) return;

        const model = provider.models.find(m => m.id === modelId);
        if (!model) return;

        this.defaults.currentModel = modelId;

        // 更新UI
        const currentModelEl = document.getElementById('current-model');
        if (currentModelEl) {
            currentModelEl.textContent = this.getModelName(modelId);
        }

        this.saveSettings();
        this.initializeModelList(); // 重新渲染列表以更新按钮状态
        if (window.UI) {
            UI.showToast(`已切换到 ${this.getModelName(modelId)}`, 'success');
        }
    },

    // 获取模型名称
    getModelName(modelId) {
        for (const provider of this.defaults.providers) {
            const model = provider.models.find(m => m.id === modelId);
            if (model) {
                return model.name;
            }
        }
        return modelId;
    },

    // 获取模型配置
    getModelConfig(modelId) {
        for (const provider of this.defaults.providers) {
            const model = provider.models.find(m => m.id === modelId);
            if (model) {
                return {
                    ...model,
                    provider: provider.id,
                    baseUrl: provider.baseUrl,
                    apiKey: provider.apiKey,
                    authType: provider.authType,
                    requestFormat: provider.requestFormat
                };
            }
        }
        return null;
    },

    // 设置事件监听器
    setupEventListeners() {
        // 温度滑块
        const temperatureSlider = document.getElementById('temperature-slider');
        const temperatureValue = document.getElementById('temperature-value');
        if (temperatureSlider && temperatureValue) {
            temperatureSlider.addEventListener('input', (e) => {
                const value = e.target.value;
                temperatureValue.textContent = value;
                this.updateSetting('temperature', parseFloat(value));
            });
        }

        // 字体大小选择
        const fontSizeSelect = document.getElementById('font-size-select');
        if (fontSizeSelect) {
            fontSizeSelect.addEventListener('change', (e) => {
                this.setFontSize(e.target.value);
            });
        }

        // 自动滚动开关
        const autoScrollToggle = document.getElementById('autoScrollToggle');
        if (autoScrollToggle) {
            autoScrollToggle.addEventListener('change', (e) => {
                this.updateSetting('autoScroll', e.target.checked);
            });
        }

        // 声音开关
        const soundToggle = document.getElementById('soundToggle');
        if (soundToggle) {
            soundToggle.addEventListener('change', (e) => {
                this.updateSetting('soundEnabled', e.target.checked);
            });
        }

        // 保存设置按钮
        const saveSettingsBtn = document.getElementById('saveSettingsBtn');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => {
                this.saveSettings();
                if (window.UI) {
                    UI.showToast('设置已保存', 'success');
                }
                // 关闭设置模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
                if (modal) {
                    modal.hide();
                }
            });
        }

        // 主题切换按钮
        const themeToggleBtn = document.getElementById('themeToggleBtn');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // API设置保存按钮
        const saveApiSettingsBtn = document.getElementById('saveApiSettingsBtn');
        if (saveApiSettingsBtn) {
            saveApiSettingsBtn.addEventListener('click', () => {
                this.saveApiSettings();
            });
        }

        // 模型选择
        const modelItems = document.querySelectorAll('.dropdown-item[data-model]');
        modelItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.changeModel(item.dataset.model);
            });
        });

        // 添加新模型按钮
        const addModelBtn = document.getElementById('add-model-btn');
        if (addModelBtn) {
            addModelBtn.addEventListener('click', () => {
                this.showAddModelModal();
            });
        }
    },

    // 加载设置
    loadSettings() {
        try {
            const savedSettings = localStorage.getItem('capswriter_chat_settings');
            if (savedSettings) {
                const settings = JSON.parse(savedSettings);
                // 合并默认设置和保存的设置
                Object.assign(this.defaults, settings);
            }
        } catch (error) {
            console.error('加载设置失败:', error);
        }
    },

    // 保存设置
    saveSettings() {
        try {
            localStorage.setItem('capswriter_chat_settings', JSON.stringify(this.defaults));
        } catch (error) {
            console.error('保存设置失败:', error);
            if (window.UI) {
                UI.showToast('保存设置失败', 'error');
            }
        }
    },

    // 应用设置
    applySettings() {
        // 应用主题
        document.body.setAttribute('data-theme', this.defaults.darkMode ? 'dark' : 'light');
        
        // 应用字体大小
        document.body.setAttribute('data-font-size', this.defaults.fontSize);
        
        // 更新UI显示
        this.updateUIDisplay();
    },

    // 更新UI显示
    updateUIDisplay() {
        // 更新温度显示
        const temperatureSlider = document.getElementById('temperature-slider');
        const temperatureValue = document.getElementById('temperature-value');
        if (temperatureSlider) temperatureSlider.value = this.defaults.temperature;
        if (temperatureValue) temperatureValue.textContent = this.defaults.temperature;

        // 更新字体大小选择
        const fontSizeSelect = document.getElementById('font-size-select');
        if (fontSizeSelect) fontSizeSelect.value = this.defaults.fontSize;

        // 更新自动滚动开关
        const autoScrollToggle = document.getElementById('autoScrollToggle');
        if (autoScrollToggle) autoScrollToggle.checked = this.defaults.autoScroll;

        // 更新声音开关
        const soundToggle = document.getElementById('soundToggle');
        if (soundToggle) soundToggle.checked = this.defaults.soundEnabled;

        // 更新当前模型显示
        const currentModelEl = document.getElementById('current-model');
        if (currentModelEl) currentModelEl.textContent = this.getModelName(this.defaults.currentModel);

        // 更新主题按钮图标
        this.updateThemeButtonIcon();
    },

    // 更新设置项
    updateSetting(key, value) {
        if (key in this.defaults) {
            this.defaults[key] = value;
            this.saveSettings();
        }
    },

    // 切换主题
    toggleTheme() {
        this.defaults.darkMode = !this.defaults.darkMode;
        document.body.setAttribute('data-theme', this.defaults.darkMode ? 'dark' : 'light');
        this.updateThemeButtonIcon();
        this.saveSettings();
    },

    // 更新主题按钮图标
    updateThemeButtonIcon() {
        const themeToggleBtn = document.getElementById('themeToggleBtn');
        if (themeToggleBtn) {
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                icon.className = this.defaults.darkMode ? 'bi bi-sun' : 'bi bi-moon-stars';
            }
            themeToggleBtn.innerHTML = `<i class="${this.defaults.darkMode ? 'bi bi-sun' : 'bi bi-moon-stars'}"></i> ${this.defaults.darkMode ? '浅色模式' : '深色模式'}`;
        }
    },

    // 设置字体大小
    setFontSize(size) {
        if (['small', 'medium', 'large'].includes(size)) {
            this.defaults.fontSize = size;
            document.body.setAttribute('data-font-size', size);
            this.saveSettings();
        }
    },

    // 保存API设置
    saveApiSettings() {
        // API设置现在通过updateProviderConfig方法处理
        // 该方法会在UI中直接调用，不需要额外的保存方法
        if (window.UI) {
            UI.showToast('API设置已更新', 'success');
        }
        
        // 关闭设置模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
        if (modal) {
            modal.hide();
        }
    },

    // 获取当前设置
    getSettings() {
        return { ...this.defaults };
    },

    // 获取特定设置项
    getSetting(key) {
        return this.defaults[key];
    }
};

// 导出模块
window.Settings = Settings;
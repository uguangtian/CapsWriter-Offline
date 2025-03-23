class GlobalConfig:
    def __init__(self):
        self.lmstudio_config = None
        self.deepseek_config = None
        self.doubao_config = None

    def set_lmstudio_config(self, config):
        self.lmstudio_config = config

    def get_lmstudio_config(self):
        return self.lmstudio_config

    def set_deepseek_config(self, config):
        self.deepseek_config = config

    def get_deepseek_config(self):
        return self.deepseek_config

    def set_doubao_config(self, config):
        self.doubao_config = config

    def get_doubao_config(self):
        return self.doubao_config

# 创建全局配置实例
global_config = GlobalConfig()
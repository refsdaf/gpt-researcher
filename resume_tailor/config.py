import os
from typing import Optional

class Config:
    """简历定制代理的配置类"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.model = os.getenv("RESUME_TAILOR_MODEL", "gpt-4o")
        self.temperature = float(os.getenv("RESUME_TAILOR_TEMPERATURE", 0.0))
        self.verbose = os.getenv("RESUME_TAILOR_VERBOSE", "false").lower() == "true"

        # 默认配置
        self.remove_irrelevant = True
        self.exaggerate = False
        self.style_mode = "standard"

    def update_from_dict(self, config_dict: dict):
        """从字典更新配置"""
        if "remove_irrelevant" in config_dict:
            self.remove_irrelevant = config_dict["remove_irrelevant"]
        if "exaggerate" in config_dict:
            self.exaggerate = config_dict["exaggerate"]
        if "style_mode" in config_dict:
            self.style_mode = config_dict["style_mode"]

# -*- coding: utf-8 -*-
"""
样式基类 - 所有箱唛样式的抽象基类
"""
from abc import ABC, abstractmethod
from PIL import Image
import pathlib as Path


class BoxMarkStyle(ABC):
    """箱唛样式抽象基类"""
    
    def __init__(self, base_dir, ppi=300):
        self.base_dir = base_dir
        self.ppi = ppi
        self.dpi = ppi / 2.54  # cm to px
        self.resources = {}
        self.font_paths = {}
        self._load_resources()
        self._load_fonts()
    
    @abstractmethod
    def _load_resources(self):
        """加载样式所需的图片资源"""
        pass
    
    @abstractmethod
    def _load_fonts(self):
        """加载样式所需的字体"""
        pass
    
    # @abstractmethod
    # def generate_left_panel(self, sku_config):
    #     """生成左侧面板（上下）"""
    #     pass
    
    # @abstractmethod
    # def generate_right_panel(self, sku_config):
    #     """生成右侧面板（上下）"""
    #     pass
    
    @abstractmethod
    def generate_front_panel(self, sku_config):
        """生成正面面板"""
        pass
    
    @abstractmethod
    def generate_side_panel(self, sku_config):
        """生成侧面面板"""
        pass
    
    @abstractmethod
    def get_style_name(self):
        """返回样式名称"""
        pass
    
    @abstractmethod
    def get_style_description(self):
        """返回样式描述"""
        pass
    
    @abstractmethod
    def get_required_params(self):
        """返回该样式所需的额外参数列表"""
        return []
    
    @abstractmethod
    def get_layout_config(self, sku_config):
        """
        返回该样式的布局配置
        返回格式: {
            "区域名称": (x, y, width, height),
            ...
        }
        """
        pass
    
    @abstractmethod
    def get_panels_mapping(self, sku_config):
        """
        返回布局区域与面板的映射关系
        返回格式: {
            "区域名称": "面板键名",
            ...
        }
        面板键名应该对应 generate_all_panels() 返回的字典键
        """
        pass
    
    @abstractmethod
    def generate_all_panels(self, sku_config):
        """
        生成该样式需要的所有面板
        返回格式: {
            "面板键名": PIL.Image 对象,
            ...
        }
        例如: {
            "left_up": canvas_left_up,
            "front": canvas_front,
            ...
        }
        """
        pass


class StyleRegistry:
    """样式注册表 - 管理所有可用的样式"""
    
    _styles = {}
    
    @classmethod
    def register(cls, style_class):
        """注册一个样式类"""
        # 创建临时实例获取样式名称
        temp_instance = style_class(base_dir=Path.Path(__file__).parent, ppi=72)
        style_name = temp_instance.get_style_name()
        cls._styles[style_name] = style_class
        return style_class
    
    @classmethod
    def get_style(cls, style_name, base_dir, ppi=300):
        """根据名称获取样式实例"""
        if style_name not in cls._styles:
            raise ValueError(f"未找到样式: {style_name}. 可用样式: {list(cls._styles.keys())}")
        return cls._styles[style_name](base_dir=base_dir, ppi=ppi)
    
    @classmethod
    def get_all_styles(cls):
        """获取所有已注册的样式信息"""
        styles_info = []
        for style_name, style_class in cls._styles.items():
            # 创建临时实例获取描述
            temp_instance = style_class(base_dir=Path.Path(__file__).parent, ppi=72)
            styles_info.append({
                'name': style_name,
                'description': temp_instance.get_style_description(),
                'required_params': temp_instance.get_required_params()
            })
        return styles_info
    
    @classmethod
    def list_styles(cls):
        """列出所有可用样式名称"""
        return list(cls._styles.keys())

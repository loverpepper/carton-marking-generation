# -*- coding: utf-8 -*-
"""
MCombo 标准样式 - 将原有的 BoxMarkEngine 转换为样式类
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib as Path
from style_base import BoxMarkStyle, StyleRegistry
import general_functions


@StyleRegistry.register
class BarberpubTopAndBottomStyle(BoxMarkStyle):
    '''Barberpub 天地盖样式'''
    
    def get_style_name(self):
        return "barberpub_topandbottom"
    
    def get_style_description(self):
        return "Barberpub 天地盖箱唛样式 - 带公司Logo、SKU信息、条形码"
    
    def get_required_params(self):
        return ['length_cm', 'width_cm', 'height_cm', 'color', 'product', 'size', 'side_text', 'box_number', 'sponge_verified']
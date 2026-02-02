# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pandas as pd
import pathlib as Path
import sys
import os
import general_functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')


class SKUConfig:
    def __init__(self, sku_name, length_cm, width_cm, height_cm, color, product, size, side_text, box_number,sponge_verified=False, bottom_gb_h_cm=10, ppi=300):
        self.sku_name = sku_name
        self.l_cm = length_cm
        self.w_cm = width_cm
        self.h_cm = height_cm
        self.bottom_gb_h = bottom_gb_h_cm  # 底部黑色底框高度，单位厘米
        self.color = color
        self.product = product
        self.size = size
        self.side_text = side_text
        self.box_number = box_number
        self.sponge_verified = sponge_verified
        self.gw_val = side_text['gw_value']
        self.dpi = ppi / 2.54  # 转换因子：cm 到 像素 (1 inch = 2.54 cm), 1 厘米有多少像素
        self.ppi = ppi
        # 预计算像素值，方便后续绘图
        self.l_px = int(length_cm * self.dpi)
        self.w_px = int(width_cm * self.dpi)
        self.h_px = int(height_cm * self.dpi)
        self.half_w_px = int(self.w_px / 2) # 顶盖和底盖通常是宽的一半
        self.bottom_gb_h_px = int(self.bottom_gb_h * self.dpi)

class BoxMarkEngine:
    def __init__(self, base_dir, ppi=300):
        self.base_dir = base_dir
        self.ppi = ppi
    
        self.resources = {
            'icon_left_2_panel': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '顶部-左-2箱.png').convert('RGBA'),
            'icon_left_3_panel': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '顶部-左-3箱.png').convert('RGBA'),
            'icon_right_2-1_panel': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '顶部-右-2-1.png').convert('RGBA'),
            'icon_right_3-1_panel': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '顶部-右-3-1.png').convert('RGBA'),
            'icon_trademark': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '正唛logo.png').convert('RGBA'),
            'icon_company': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '正唛公司信息.png').convert('RGBA'),
            'icon_box_number_1': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '正唛 Box 1.png').convert('RGBA'),
            'icon_box_number_2': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '正唛 Box 2.png').convert('RGBA'),
            'icon_box_number_3': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '正唛 Box 3.png').convert('RGBA'),
            'icon_side_label_box': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '侧唛标签框.png').convert('RGBA'),
            'icon_side_logo': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '侧唛logo.png').convert('RGBA'),
            'icon_side_text_box': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '侧唛文本框.png').convert('RGBA'),
            'icon_side_sponge': Image.open(base_dir / 'assets' / 'Mcombo' /  '样式一' /'矢量文件' / '海绵认证.png').convert('RGBA')
        }
        
        # 字体大小相对比例（基于参考箱子：77x67.5x47cm, ppi=72）
        # 这些比例是相对于箱子高度的像素值
        self.font_ratios = {
            'color_font': 51 / 1332,      # 51px / (47cm * 72/2.54) ≈ 0.038
            'product_font': 180 / 1332,   # 180px / 1332 ≈ 0.135
            'size_font': 60 / 1332,       # 60px / 1332 ≈ 0.045
            'regular_font': 40 / 1332,     # 40px / 1332 ≈ 0.030
            'side_font': 40 / 1332         # 40px / 1332 ≈ 0.030
        }
    
    def get_layout_config(self, sku_config):
        """
        按照 [侧面, 正面, 侧面, 正面] 的顺序定义横向坐标 (X)
        以及 [顶盖, 正身, 底盖] 的顺序定义纵向坐标 (Y)
        """
        # 定义 X 轴的关键节点
        x0 = 0
        x1 = sku_config.l_px 
        x2 = sku_config.w_px + sku_config.l_px
        x3 = sku_config.w_px + sku_config.l_px * 2
         
        # 定义 Y 轴的关键节点
        y0 = 0                             # 顶盖顶部
        y1 = sku_config.half_w_px                # 正身顶部
        y2 = sku_config.half_w_px + sku_config.h_px    # 底盖顶部
        
        # 重新命名的布局字典，更符合纸箱结构
        return {
            # 第一行：顶盖层 (Top Flaps)
            "flap_top_front1":  (x0, y0, sku_config.l_px, sku_config.half_w_px),
            "flap_top_side1": (x1, y0, sku_config.w_px, sku_config.half_w_px),
            "flap_top_front2":  (x2, y0, sku_config.l_px, sku_config.half_w_px),
            "flap_top_side2": (x3, y0, sku_config.w_px, sku_config.half_w_px),

            # 第二行：正身层 (Main Body)
            "panel_front1":     (x0, y1, sku_config.l_px, sku_config.h_px),
            "panel_side1":    (x1, y1, sku_config.w_px, sku_config.h_px),
            "panel_front2":     (x2, y1, sku_config.l_px, sku_config.h_px),
            "panel_side2":    (x3, y1, sku_config.w_px, sku_config.h_px),

            # 第三行：底盖层 (Bottom Flaps)
            "flap_btm_front1":  (x0, y2, sku_config.l_px, sku_config.half_w_px),
            "flap_btm_side1": (x1, y2, sku_config.w_px, sku_config.half_w_px),
            "flap_btm_front2":  (x2, y2, sku_config.l_px, sku_config.half_w_px),
            "flap_btm_side2": (x3, y2, sku_config.w_px, sku_config.half_w_px),
        }
    
    def _get_fonts_path(self):
        """获取所有字体文件的路径"""
        return {
            'calibri_bold': str(self.base_dir / 'assets' / 'Mcombo' /  '样式一' / '箱唛字体' / 'calibri_blod.ttf'),
            'itc_demi': str(self.base_dir / 'assets' / 'Mcombo' /  '样式一' / '箱唛字体' / 'ITC Avant Garde Gothic LT Demi.ttf'),
            'courier': str(self.base_dir / 'assets' / 'Mcombo' /  '样式一' / '箱唛字体' / 'cour.ttf'),
            'side_font_label': str(self.base_dir / 'assets' / 'Mcombo' /  '样式一' / '箱唛字体' /'ITC Avant Garde Gothic LT Demi.ttf'),
            'side_font_bold': str(self.base_dir / 'assets' / 'Mcombo' /  '样式一' / '箱唛字体' / 'calibri_blod.ttf'),
            'side_font_barcode': str(self.base_dir / 'assets' / 'Mcombo' /  '样式一' / '箱唛字体' / 'calibri_blod.ttf')
        }
    
    def _get_fonts(self, sku_config):
        """根据箱子尺寸动态计算字体大小"""
        # 基于箱子高度计算字体大小
        height_px = sku_config.h_px
        font_paths = self._get_fonts_path()
        
        fonts = {
            'color_font': ImageFont.truetype(
                font_paths['calibri_bold'], 
                size=int(height_px * self.font_ratios['color_font'])
            ),
            'product_font': ImageFont.truetype(
                font_paths['itc_demi'], 
                size=int(height_px * self.font_ratios['product_font'])
            ),
            'size_font': ImageFont.truetype(
                font_paths['calibri_bold'], 
                size=int(height_px * self.font_ratios['size_font'])
            ),
            'regular_font': ImageFont.truetype(
                font_paths['itc_demi'], 
                size=int(height_px * self.font_ratios['regular_font'])
            )
        }
        return fonts
            
        

    def generate_left_panel(self, sku_config):
        # 正面面板尺寸应该是长×半宽
        canvas_left_up = Image.new('RGB', (sku_config.l_px, sku_config.half_w_px), (161,142,102))
        canvas_left_down = Image.new('RGB', (sku_config.l_px, sku_config.half_w_px), (161,142,102))

        # 判断总共有几箱，选择对应的图片资源
        total_box_number = sku_config.box_number['total_boxes']
        icon_left_panel = self.resources[f'icon_left_{total_box_number}_panel']
        
        icon_left_up_panel = icon_left_panel
        icon_left_down_panel = icon_left_panel.rotate(180, expand=True)
        
        canvas_left_up = general_functions.paste_center_with_height(canvas_left_up, icon_left_up_panel, height_cm=10, dpi=sku_config.dpi)
        canvas_left_down = general_functions.paste_center_with_height(canvas_left_down, icon_left_down_panel, height_cm=10, dpi=sku_config.dpi)
        return canvas_left_up, canvas_left_down
        
        

    def generate_right_panel(self, sku_config):
        # 正面面板尺寸应该是长×半宽
        canvas_right_up = Image.new('RGB', (sku_config.l_px, sku_config.half_w_px), (161,142,102))
        canvas_right_down = Image.new('RGB', (sku_config.l_px, sku_config.half_w_px), (161,142,102))
        
        total_box_number = sku_config.box_number['total_boxes']
        
        # 判断总共有几箱，选择对应的图片资源
        icon_right_panel = self.resources[f'icon_right_{total_box_number}-1_panel']
        
        icon_right_panel_up = icon_right_panel.rotate(180, expand=True)
        icon_right_panel_down = icon_right_panel
        
        canvas_right_up = general_functions.paste_center_with_height(canvas_right_up, icon_right_panel_up, height_cm=9, dpi=sku_config.dpi)
        canvas_right_down = general_functions.paste_center_with_height(canvas_right_down, icon_right_panel_down, height_cm=9, dpi=sku_config.dpi)
        return canvas_right_up, canvas_right_down


    def generate_front_panel(self, sku_config):
        canvas = Image.new('RGB', (sku_config.l_px, sku_config.h_px), (161,142,102))
        icon_trademark = self.resources['icon_trademark']
        
        # 获取动态字体
        fonts = self._get_fonts(sku_config)
        
        # 粘贴正唛标志，目标高度为正面高度的三分之一
        canvas_w, canvas_h = canvas.size
        icon_trademark_target_h = canvas_h // 3 # 目标高度为正面高度的三分之一
        icon_trademark_resized = general_functions.scale_by_height(icon_trademark, icon_trademark_target_h)
        icon_trademark_target_w, icon_trademark_target_h = icon_trademark_resized.size
        paste_x = (canvas_w - icon_trademark_target_w) // 2
        paste_y = 0
        canvas.paste(icon_trademark_resized, (paste_x, paste_y), mask=icon_trademark_resized)
        
        
        draw = ImageDraw.Draw(canvas)
        bottom_bg_h = int( sku_config.bottom_gb_h * sku_config.dpi)  # 10 cm 高的黑色底框
        
        ######################################################
        # 自动化生成底部黑色底框和动态SKU文本、公司信息图标、箱号信息
        icon_company = self.resources['icon_company']
        icon_box_number = self.resources[f"icon_box_number_{sku_config.box_number['current_box']}"]
        
        fonts_paths = self._get_fonts_path()
        general_functions.draw_dynamic_bottom_bg(canvas, sku_config, icon_company, icon_box_number, fonts_paths)

        ######################################################
        # 写入右上角颜色信息
        color_font = fonts['color_font']
        color_text = f"{sku_config.color}"
        bbox = draw.textbbox((0, 0), color_text, font=color_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        color_x = canvas_w - text_w - int(4 * sku_config.dpi)  # 右侧留4cm边距
        color_y = int(4 * sku_config.dpi)  # 顶部留4cm边距
        color_xy = (color_x, color_y)
        # 为颜色信息加入圆角矩形背景
        draw = general_functions.draw_rounded_bg_for_text(draw, bbox, sku_config, color_xy,
                                bg_color=(0, 0, 0), padding_cm=(0.8, 0.4), radius=16) # padding_cm: (水平, 垂直)内边距， radius: 圆角半径
        
        draw.text((color_x, color_y), color_text, font=color_font, fill=(161,142,102))
        
        
        ######################################################
        # 写入产品名称SKU信息和产品尺寸信息
        product_text = sku_config.product
        size_text = sku_config.size
        product_font = fonts['product_font']
        size_font = fonts['size_font']
        bbox_product = draw.textbbox((0, 0), product_text, font=product_font)
        bbox_size = draw.textbbox((0, 0), size_text, font=size_font)
        product_w = bbox_product[2] - bbox_product[0]
        size_w = bbox_size[2] - bbox_size[0]
        
        #将产品名和大小信息和椭圆直线作为整体处理
        gap_px = int(1 * sku_config.dpi)  # 产品名和尺寸信息之间都和横线间隔1cm
        line_height = 7 / 0.74  # 线条高度10pt转换为px
        line_width = int(product_w * 0.85)
        # --- 计算整体总高度 ---
        total_group_height = product_font.size + line_height + size_font.size +  gap_px * 2
        
        # --- 计算起始 Y 坐标 (让整个组在logo下方的剩余空间中垂直居中)
        remaining_space = canvas_h - icon_trademark_target_h - bottom_bg_h # logo下方的剩余空间
        group_start_y = icon_trademark_target_h + (remaining_space - total_group_height) // 2  # 在剩余空间中居中
        
        ######################################################
        # A. 绘制产品名称 (Product Text)
        product_x = (canvas_w - product_w) // 2
        ascent, descent = product_font.getmetrics()
        draw.text((product_x, group_start_y + ascent), product_text, font=product_font, fill=(0, 0, 0), anchor="ls")
        
        # B. 绘制下划线 (Underline)
        # 线的 Y 坐标在产品文字下方
        line_y_top = group_start_y + product_font.size + gap_px
        line_x0 = (canvas_w - line_width) // 2
        line_x1 = line_x0 + line_width
        line_box = [line_x0, line_y_top, line_x1, line_y_top + line_height]
        general_functions.draw_smooth_ellipse(draw, canvas, line_box, fill=(0, 0, 0))
        
        # C. 绘制尺寸信息 (Size Text)
        size_x = (canvas_w - size_w) // 2
        size_y = line_y_top + gap_px + line_height
        draw.text((size_x, size_y), size_text, font=size_font, fill=(0, 0, 0))
        ######################################################
        return canvas



    def generate_side_panel(self, sku_config):
        canvas = Image.new('RGB', (sku_config.w_px, sku_config.h_px), (161,142,102))
        font_paths = self._get_fonts_path()
        general_functions.draw_side_dynamic_bottom_bg(canvas, sku_config, self.resources['icon_company'], font_paths)
        
        # 放置侧唛标签框， 左边和上边的间距与正唛颜色信息相同
        icon_side_label_box = self.resources['icon_side_label_box']
        icon_side_label_box_resized = general_functions.scale_by_height(icon_side_label_box, int(5 * sku_config.dpi)) # 侧唛标签框高度5cm， 宽度为9cm
        icon_side_label_box_x, icon_side_label_box_y = int(3 * sku_config.dpi), int(4 * sku_config.dpi)
        canvas.paste(icon_side_label_box_resized, (icon_side_label_box_x, icon_side_label_box_y), mask=icon_side_label_box_resized)
        
        # 放置侧唛 logo，logo高度暂定同侧唛标签框高度一致，5cm，宽度自适应，右边间距4cm, 上边间距同样为4cm
        icon_side_logo = self.resources['icon_side_logo']
        icon_side_logo_resized = general_functions.scale_by_height(icon_side_logo, int(5 * sku_config.dpi))
        icon_side_logo_w, icon_side_logo_h = icon_side_logo_resized.size
        icon_side_logo_x = canvas.width - icon_side_logo_w - int(4 * sku_config.dpi)
        icon_side_logo_y = int(4 * sku_config.dpi)
        canvas.paste(icon_side_logo_resized, (icon_side_logo_x, icon_side_logo_y), mask=icon_side_logo_resized)
        
        # 放置侧唛文字信息框，左边间距4cm, 底部和侧唛底框顶部间距3cm
        icon_side_text_box_spacing_left = int(4 * sku_config.dpi)
        icon_side_text_box_spacing_bottom = int(3 * sku_config.dpi)
        table_height_px  = int(8 * sku_config.dpi)  # 侧唛文字信息框高度8cm
        
        # 1. 预计算坐标 (作为基准点)
        base_x = icon_side_text_box_spacing_left
        # 底部对齐逻辑：画布高度 - 底框 - 间距 - 表格高度
        base_y = canvas.height - sku_config.bottom_gb_h_px - icon_side_text_box_spacing_bottom - table_height_px
        
        icon_side_text_box = self.resources['icon_side_text_box'].copy()
        icon_side_text_box_resized = general_functions.scale_by_height(icon_side_text_box, table_height_px)  # 侧唛文字信息框高度8cm
        if sku_config.sponge_verified:
            icon_side_sponge = self.resources['icon_side_sponge'].copy()
            icon_side_sponge_resized = general_functions.scale_by_height(icon_side_sponge, table_height_px) # 海绵认证高度8cm
            canvas.paste(icon_side_sponge_resized, (base_x, base_y), mask=icon_side_sponge_resized)
            
            # 计算侧唛文字信息框的最终位置
            base_x += icon_side_sponge_resized.size[0] + int( 0.6 * sku_config.dpi )  # 侧唛文字信息框在海绵认证右边，间隔0.6cm
            fonts_paths = self._get_fonts_path()
            fill_image = general_functions.fill_sidepanel_text(icon_side_text_box_resized, sku_config, fonts_paths)
            canvas.paste(fill_image, (base_x, base_y), mask=icon_side_text_box_resized)
            
            
        else:
            base_x = icon_side_text_box_spacing_left # 左边间距4cm
            base_y = canvas.height - sku_config.bottom_gb_h_px - icon_side_text_box_spacing_bottom - icon_side_text_box_resized.size[1]  # 底部和侧唛底框顶部间距3cm
            
            # 填充文字信息到侧唛文字信息框
            fonts_paths = self._get_fonts_path()
            fill_image = general_functions.fill_sidepanel_text(icon_side_text_box_resized, sku_config, fonts_paths)
            canvas.paste(fill_image, (base_x, base_y), mask=icon_side_text_box_resized)
        
        return canvas
    


def visualize_layout(sku_config, BoxMarkEngine):
    # 1. 获取布局数据
    layout = BoxMarkEngine.get_layout_config(sku_config)
    
    # 2. 计算画布总尺寸
    # 总宽 = 2*L + 2*W, 总高 = H + W (顶盖+底盖)
    total_width = (sku_config.l_px * 2) + (sku_config.w_px * 2)
    total_height = sku_config.h_px + sku_config.w_px
    
    # 创建画布
    canvas = Image.new('RGB', (total_width, total_height), (161,142,102))
    
    # 3. 生成各个面板
    canvas_left_up, canvas_left_down = BoxMarkEngine.generate_left_panel(sku_config)
    canvas_right_up, canvas_right_down = BoxMarkEngine.generate_right_panel(sku_config)
    canvas_front = BoxMarkEngine.generate_front_panel(sku_config)
    canvas_side = BoxMarkEngine.generate_side_panel(sku_config)
    
    # 打印调试信息
    print(f"canvas_left_up 尺寸: {canvas_left_up.size}")
    print(f"canvas_left_down 尺寸: {canvas_left_down.size}")
    print(f"canvas_right_up 尺寸: {canvas_right_up.size}")
    print(f"canvas_right_down 尺寸: {canvas_right_down.size}")
    print(f"canvas_front 尺寸: {canvas_front.size}")
    print(f"canvas_side 尺寸: {canvas_side.size}")
    # 4. 将完成的面板粘贴到对应位置
    # 第1块：flap_top_front1 (顶盖第1张，正面)
    x, y, w, h = layout["flap_top_front1"]
    print(f"flap_top_front1 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_left_up, (int(x), int(y)))
    
    # 第3块：flap_top_front2 (顶盖第3张，正面)
    x, y, w, h = layout["flap_top_front2"]
    print(f"flap_top_front2 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_right_up, (int(x), int(y)))
    
    # 第5块：panel_front1 (正身第1张，正面)
    x, y, w, h = layout["panel_front1"]
    print(f"panel_front1 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_front, (int(x), int(y)))
    
    # 第6块：panel_side1 (侧身第1张，正面)
    x, y, w, h = layout["panel_side1"]
    print(f"panel_side1 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_side, (int(x), int(y)))
    
    # 第7块：panel_front2 (正身第2张，正面)
    x, y, w, h = layout["panel_front2"]
    print(f"panel_front2 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_front, (int(x), int(y)))
    
    # 第8块：panel_side2 (侧身第2张，正面)
    x, y, w, h = layout["panel_side2"]
    print(f"panel_side2 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_side, (int(x), int(y)))
    
    # 第9块：flap_btm_front1 (底盖第1张，正面)
    x, y, w, h = layout["flap_btm_front1"]
    print(f"flap_btm_front1 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_left_down, (int(x), int(y)))
    
    # 第11块：flap_btm_front2 (底盖第3张，正面)
    x, y, w, h = layout["flap_btm_front2"]
    print(f"flap_btm_front2 位置: ({x}, {y}), 尺寸: ({w}, {h})")
    canvas.paste(canvas_right_down, (int(x), int(y)))
    
    # 5. 画出所有格子的边框（用于调试和验证）
    draw = ImageDraw.Draw(canvas)
    for name, (x, y, w, h) in layout.items():
        shape = [x, y, x + w, y + h]
        draw.rectangle(shape, outline=(0,0,0), width=3)
    
    # 由RGB转CMYK以便印刷
    canvas = canvas.convert("CMYK")
    # canvas.show()
    # 6. 保存为PDF格式（用于印刷）
    output_filename = f"{sku_config.sku_name}_carton_marking.pdf"
    # PDF需要RGB模式
    canvas_rgb = canvas.convert('RGB')
    canvas_rgb.save(output_filename, "PDF", resolution=sku_config.ppi, quality=100)
    print(f"✅ 箱唛已生成为PDF！文件: {output_filename}")
    print(f"   尺寸: {total_width}x{total_height}px ({total_width/sku_config.dpi:.1f}cm x {total_height/sku_config.dpi:.1f}cm)")
    print(f"   分辨率: {sku_config.ppi} PPI")

# --- 测试运行 ---
# 使用你样图中的尺寸: 77, 67.5, 47
sku_text = {
    'gw_value': 188.8,
    'nw_value': 94.4,
    'dimention_text': f'BOX SIZE: 30.3\'\' x 26.6\'\' x 18.5\'\'',
    'sn_code': '08429383723953'
}

sku_sponge_verified = True
box_number = {
    'total_boxes': 3,
    'current_box': 1
}
test_sku = SKUConfig("6160-R7096BE-1", 79, 68, 47, 'Beige', product = 'Lift Recliner', size = '(Medium-Wide)', side_text=sku_text, box_number=box_number, sponge_verified=sku_sponge_verified, ppi= 150)
boxengine1 = BoxMarkEngine(base_dir = Path.Path(__file__).parent, ppi = 150) 
visualize_layout(test_sku, boxengine1)



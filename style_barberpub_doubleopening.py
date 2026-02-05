# -*- coding: utf-8 -*-
"""
Barberpub 对开盖样式 - 将原有的 BoxMarkEngine 转换为样式类
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib as Path
from style_base import BoxMarkStyle, StyleRegistry
import general_functions


@StyleRegistry.register
class BarberpubDoubleOpeningStyle(BoxMarkStyle):
    '''Barberpub 对开盖样式'''
    
    def get_style_name(self):
        return "barberpub_doubleopening"
    
    def get_style_description(self):
        return "Barberpub 对开盖箱唛样式 - 带公司Logo、SKU信息、条形码"
    
    def get_required_params(self):
        return ['length_cm', 'width_cm', 'height_cm', 'color', 'origin', 'product', 'side_text', 'sku_name', 'box_number']
    
    def get_layout_config(self, sku_config):
        '''
        Barberpub 对开盖样式 - 5块布局（4列3行）
        '''
        
        x0 = 0
        x1 = sku_config.l_px
        x2 = sku_config.l_px + sku_config.w_px
        x3 = sku_config.l_px * 2 + sku_config.w_px
        
        y0 = 0
        y1 = sku_config.half_w_px
        y2 = sku_config.half_w_px + sku_config.h_px
        
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
    
    def get_panels_mapping(self, sku_config):
        """定义每个区域应该粘贴哪个面板"""
        
        return {
            "flap_top_front1": "left_up",
            "flap_top_side1": "blank",
            "flap_top_front2": "right_up",
            "flap_top_side2": "blank",
            "panel_front1": "front",
            "panel_side1": "side",
            "panel_front2": "front",
            "panel_side2": "side",
            "flap_btm_front1": "left_down",
            "flap_btm_side1": "blank",
            "flap_btm_front2": "right_down",
            "flap_btm_side2": "blank",
        }
        
    def generate_all_panels(self, sku_config):
        """生成 Barberpub 对开盖样式需要的所有面板"""
        
        canvas_front = self.generate_barberpub_front_panel(sku_config)
        canvas_side = self.generate_barberpub_side_panel(sku_config)
        canvas_left_up, canvas_left_down = self.generate_barberpub_left_panel(sku_config)
        canvas_right_up, canvas_right_down = self.generate_barberpub_right_panel(sku_config)
        canvas_blank = Image.new(sku_config.color_mode, (sku_config.w_px, sku_config.half_w_px), sku_config.background_color)


        return {
            "left_up": canvas_left_up,
            "left_down": canvas_left_down,
            "right_up": canvas_right_up,
            "right_down": canvas_right_down,
            "front": canvas_front,
            "side": canvas_side,
            "blank": canvas_blank,
        }
    
    
    def _load_resources(self):
        """加载 Barberpub 对开盖样式的图片资源"""
        res_base = self.base_dir / 'assets' / 'Barberpub' / '对开盖' / '矢量文件'
        
        self.resources = {
            'icon_logo': Image.open(res_base / '正唛logo.png').convert('RGBA'),
            'icon_top_logo': Image.open(res_base / '顶盖logo信息.png').convert('RGBA'),
            'icon_attention_info': Image.open(res_base / '对开盖开箱注意事项.png').convert('RGBA'),
            'icon_company': Image.open(res_base / '正唛公司信息.png').convert('RGBA'),
            'icon_webside': Image.open(res_base / '侧唛网址.png').convert('RGBA'),
            'icon_side_label_wide': Image.open(res_base / '侧唛标签_宽.png').convert('RGBA'),
            'icon_side_label_narrow': Image.open(res_base / '侧唛标签_窄.png').convert('RGBA'),
            'icon_slogan': Image.open(res_base / '正唛宣传语.png').convert('RGBA'),
            'icon_box_info': Image.open(res_base / '正唛多箱选择框.png').convert('RGBA'),
            'img_line_drawing': Image.open(res_base / '侧唛线描图.png').convert('RGBA'),
        }
    
    def _load_fonts(self):
        """加载字体路径"""
        font_base = self.base_dir / 'assets' / 'Barberpub' / '对开盖' / '箱唛字体'
        self.font_paths = {
            'CentSchbook BT': str(font_base / '111.ttf'),
            'Droid Sans Bold': str(font_base / 'CENSBKBI.ttf'),
            'Calibri Bold': str(font_base / 'calibri_blod.TTF'),

        }
    
    def generate_barberpub_left_panel(self, sku_config):
        """生成 Barberpub 对开盖样式的左侧面板"""
        canvas = Image.new(sku_config.color_mode, (sku_config.l_px, sku_config.half_w_px), sku_config.background_color)
        canvas_left_up = canvas.copy()
        canvas_left_down = canvas.copy()
        icon_top_logo = self.resources['icon_top_logo']
        
        # 在左侧面板顶部粘贴顶盖logo
        icon_top_loge_w = int( canvas.width * 0.55 ) # 宽度为面板宽度的60%
        icon_top_logo_resized = general_functions.scale_by_width(icon_top_logo, icon_top_loge_w)
        icon_top_logo_x = (canvas.width - icon_top_logo_resized.width) // 2
        icon_top_loge_y = (canvas.height - icon_top_logo_resized.height) // 2
        canvas_left_up.paste(icon_top_logo_resized, (icon_top_logo_x, icon_top_loge_y), icon_top_logo_resized)
        
        return canvas_left_up, canvas_left_down
        
    def generate_barberpub_right_panel(self, sku_config):
        """生成 Barberpub 对开盖样式的右侧面板"""
        canvas = Image.new(sku_config.color_mode, (sku_config.l_px, sku_config.half_w_px), sku_config.background_color)
        canvas_right_up = canvas.copy()
        canvas_right_down = canvas.copy()
        icon_attention_info = self.resources['icon_attention_info']
        
        # 在右侧面板顶部粘贴开箱注意事项
        icon_attention_info_w = int( canvas.width * 0.86 ) # 宽度为面板宽度的80%
        icon_attention_info_resized = general_functions.scale_by_width(icon_attention_info, icon_attention_info_w)
        icon_attention_info_x = (canvas.width - icon_attention_info_resized.width) // 2
        icon_attention_info_y = (canvas.height - icon_attention_info_resized.height) // 2
        canvas_right_up.paste(icon_attention_info_resized, (icon_attention_info_x, icon_attention_info_y), icon_attention_info_resized)
        
        return canvas_right_up, canvas_right_down
    
    def generate_barberpub_front_panel(self, sku_config):
        canvas = Image.new(sku_config.color_mode, (sku_config.l_px, sku_config.h_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        
        canvas_w, canvas_h = canvas.size
        
        # 加载字体路径
        font_path_centschbook = self.font_paths['CentSchbook BT']
        font_path_droid = self.font_paths['Droid Sans Bold']
        
        # --- 区域 A: 左上角 Logo ---
        margin_top_px = int(3 * sku_config.dpi)  # 顶部边距3cm
        margin_left_px = int(3 * sku_config.dpi)  # 左边距3cm
        margin_right_px = int(2.7 * sku_config.dpi)  # 右边距2.7cm
        
        icon_logo = self.resources['icon_logo']
        icon_logo_h_px = int(canvas_h * 0.14)  # Logo高度约为画布高度的14%
        icon_logo_resized = general_functions.scale_by_height(icon_logo, icon_logo_h_px)
        icon_logo_x = margin_left_px
        icon_logo_y = margin_top_px
        canvas.paste(icon_logo_resized, (icon_logo_x, icon_logo_y), mask=icon_logo_resized)
        
        # --- 区域 B: 右上角公司信息 ---
        icon_company = self.resources['icon_company']
        icon_company_h_px = int(canvas_h * 0.06)  # 公司信息高度约为画布高度的6%
        icon_company_resized = general_functions.scale_by_height(icon_company, icon_company_h_px)
        icon_company_x = canvas_w - icon_company_resized.width - margin_right_px
        icon_company_y = margin_top_px
        canvas.paste(icon_company_resized, (icon_company_x, icon_company_y), mask=icon_company_resized)
        
        # --- 区域 C: 中间 Product 名称和标语作为整体居中（稍微缩小）---
        product_text = sku_config.product
        target_product_w = int(canvas_w * 0.63)  # 缩小到68%宽度
        max_product_h = int(canvas_h * 0.28)  # 缩小到28%高度
        
        product_font_size = general_functions.get_max_font_size(
            product_text, font_path_droid, target_product_w, max_height=max_product_h
        )
        product_font = ImageFont.truetype(font_path_droid, product_font_size)
        
        # 计算Product文字尺寸
        product_w = draw.textlength(product_text, font=product_font)
        bbox = draw.textbbox((0, 0), product_text, font=product_font)
        product_h = bbox[3] - bbox[1]
        
        # --- 区域 D: 标语（小字，斜体）---
        icon_slogan = self.resources['icon_slogan']
        icon_slogan_h_px = int(canvas_h * 0.05)  # 稍微缩小到5%
        icon_slogan_resized = general_functions.scale_by_height(icon_slogan, icon_slogan_h_px)
        
        # 计算Product和Slogan的整体高度
        vertical_gap = int(1.3 * sku_config.dpi)  # Product和Slogan之间间距1.3cm
        total_center_h = product_h + vertical_gap + icon_slogan_resized.height
        
        # 整体垂直居中（在画布的48%处）
        center_y_start = int(canvas_h * 0.48) - (total_center_h // 2)
        
        # 绘制Product（居中）
        product_x = (canvas_w - product_w) // 2
        product_y = center_y_start
        draw.text((product_x, product_y), product_text, font=product_font, fill=(0, 0, 0))
        
        # 粘贴Slogan（居中）
        icon_slogan_x = (canvas_w - icon_slogan_resized.width) // 2
        icon_slogan_y = product_y + product_h + vertical_gap
        canvas.paste(icon_slogan_resized, (icon_slogan_x, icon_slogan_y), mask=icon_slogan_resized)
        
        # --- 区域 G: 底部斜纹条块（先绘制，避免遮盖文字）---
        stripe_height_cm = 1.2
        bottom_margin_cm = 0.6
        stripe_y_start = canvas_h - int(stripe_height_cm * sku_config.dpi) - int(bottom_margin_cm * sku_config.dpi)
        stripe_y_end = canvas_h - int(bottom_margin_cm * sku_config.dpi)

        
        canvas = general_functions.draw_diagonal_stripes(
            canvas, 
            stripe_height_cm=stripe_height_cm,
            dpi=sku_config.dpi,
            bottom_margin_cm=bottom_margin_cm,
            stripe_width_px=150,
            stripe_color=(0, 0, 0),
            bg_color=sku_config.background_color
        )
        draw = ImageDraw.Draw(canvas)  # 重新创建draw对象，因为canvas被更新了
        
        # --- 区域 E: 左下角颜色和SKU代码 ---
        margin_bottom_px = int(3.2 * sku_config.dpi)  # 底部边距3.2cm（增大，确保文字在斜纹上方）
        text_vertical_gap = int(0.3 * sku_config.dpi)  # 文字之间的垂直间距
        
        # SKU代码文字（大字，粗体）
        sku_code_text = sku_config.sku_name
        target_sku_code_w = int(canvas_w * 0.715)  # 宽度为面板宽度的68%
        sku_code_font_size = general_functions.get_max_font_size(
            sku_code_text, font_path_centschbook, target_sku_code_w, max_height=int(canvas_h * 0.14)
        )
        sku_code_font = ImageFont.truetype(font_path_centschbook, sku_code_font_size)
        
        # 计算SKU代码尺寸
        bbox_sku = draw.textbbox((0, 0), sku_code_text, font=sku_code_font)
        sku_code_h = bbox_sku[3] - bbox_sku[1]
        
        # SKU代码Y坐标（从底部往上算）
        sku_code_y = canvas_h - margin_bottom_px - sku_code_h - int(0.5 * sku_config.dpi)
        sku_code_x = margin_left_px - int(0.6 * sku_config.dpi)  # 左移0.6cm以增加边距

        draw.text((sku_code_x, sku_code_y), sku_code_text, font=sku_code_font, fill=(0, 0, 0))
        
        # 颜色文字（粗体，与SKU代码相同字体）
        color_text = f"{sku_config.color.upper()}"
        color_font_size = int(canvas_h * 0.06)
        color_font = ImageFont.truetype(font_path_centschbook, color_font_size)
        
        bbox_color = draw.textbbox((0, 0), color_text, font=color_font)
        color_text_h = bbox_color[3] - bbox_color[1]
        color_text_y = sku_code_y - color_text_h - text_vertical_gap  # 在SKU代码上方
        color_text_x = margin_left_px
      
        draw.text((color_text_x, color_text_y), color_text, font=color_font, fill=(0, 0, 0))
        
        # --- 区域 F: 右下角箱号信息（黑框文字）---
        box_text = f"BOX {sku_config.box_number['current_box']} OF {sku_config.box_number['total_boxes']}"
        box_text_font_size = int(canvas_h * 0.038)  # 字体大小为画布高度的5.5%
        box_text_font = ImageFont.truetype(font_path_centschbook, box_text_font_size)
        
        # 计算文字尺寸
        bbox_box_text = draw.textbbox((0, 0), box_text, font=box_text_font)
        bbox_box_text_w = bbox_box_text[2] - bbox_box_text[0]
        bbox_box_text_h = bbox_box_text[3] - bbox_box_text[1]
        
        # 箱号位置（右下角，与SKU代码Y坐标对齐）
        bbox_text_x = canvas_w - margin_right_px - bbox_box_text_w
        bbox_text_y = canvas_h - margin_bottom_px - bbox_box_text_h - int(0.5 * sku_config.dpi) 
        box_text_pos = (bbox_text_x, bbox_text_y)
        
        # 绘制黑框背景
        draw = general_functions.draw_rounded_bg_for_text(
            draw, bbox_box_text, sku_config, box_text_pos,
            bg_color=(0, 0, 0), padding_cm=(0.5, 0.7), radius=12
        )
        
        # 绘制白色文字
        draw.text(box_text_pos, box_text, font=box_text_font, fill=sku_config.background_color)
        
        canvas_front = canvas
        return canvas_front
    
    def generate_barberpub_side_panel(self, sku_config):
        """
        生成 Barberpub 对开盖样式的侧面板
        在这里分成了两种情况：宽侧唛和窄侧唛，根据箱子宽度决定使用哪种侧唛
            
        """
        canvas = Image.new(sku_config.color_mode, (sku_config.w_px, sku_config.h_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        
        canvas_w, canvas_h = canvas.size
        
        # 加载字体路径
        font_path_centschbook = self.font_paths['CentSchbook BT']
        
        # --- 区域 A: 侧唛网址 ---
        """ 两种情况下都放置侧唛网址，位置和大小相同 """
        icon_webside = self.resources['icon_webside']
        icon_webside_w_px = int(canvas_w * 0.5)  # 宽度为画布宽度的50%
        icon_webside_resized = general_functions.scale_by_width(icon_webside, icon_webside_w_px)
        icon_webside_x = (canvas_w - icon_webside_resized.width) // 2
        icon_webside_y = int(3 * sku_config.dpi)  # 顶部边距3cm
        canvas.paste(icon_webside_resized, (icon_webside_x, icon_webside_y), mask=icon_webside_resized)

        
        canvas_side = canvas
        return canvas_side
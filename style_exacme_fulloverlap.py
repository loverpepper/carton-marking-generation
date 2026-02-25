# -*- coding: utf-8 -*-
"""
Exacme 全搭盖样式 - 将原有的 BoxMarkEngine 转换为样式类
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib as Path
from style_base import BoxMarkStyle, StyleRegistry
import general_functions
import layout_engine as engine
import re
import general_functions


@StyleRegistry.register
class ExacmeFullOverlapStyle(BoxMarkStyle):
    '''Exacme 全搭盖样式'''
    
    def get_style_name(self):
        return "exacme_fulloverlap"
    
    def get_style_description(self):
        return "Exacme 全搭盖箱唛样式 - 带公司Logo、品牌Logo、SKU信息、颜色信息、重量信息、条形码"
    
    def get_required_params(self):
        return ['length_cm', 'width_cm', 'height_cm', 'ppi', 'color', 'color_mode', 'background_color', 'product', 'side_text', 'sku_name', 'box_number']
    
    def get_layout_config(self, sku_config):
        '''
        Exacme 全搭盖样式 - 5块布局（4列3行）
        '''
        
        x0 = 0
        x1 = sku_config.l_px
        x2 = sku_config.l_px + sku_config.w_px
        x3 = sku_config.l_px * 2 + sku_config.w_px
        
        y0 = 0
        y1 = sku_config.w_px
        y2 = sku_config.w_px + sku_config.h_px
        
        return {
            # 第一行：顶盖层 (Top Flaps)
            "flap_top_front1":  (x0, y0, sku_config.l_px, sku_config.w_px),
            "flap_top_side1": (x1, y0, sku_config.w_px, sku_config.w_px),
            "flap_top_front2":  (x2, y0, sku_config.l_px, sku_config.w_px),
            "flap_top_side2": (x3, y0, sku_config.w_px, sku_config.w_px),

            # 第二行：正身层 (Main Body)
            "panel_front1":     (x0, y1, sku_config.l_px, sku_config.h_px),
            "panel_side1":    (x1, y1, sku_config.w_px, sku_config.h_px),
            "panel_front2":     (x2, y1, sku_config.l_px, sku_config.h_px),
            "panel_side2":    (x3, y1, sku_config.w_px, sku_config.h_px),

            # 第三行：底盖层 (Bottom Flaps)
            "flap_btm_front1":  (x0, y2, sku_config.l_px, sku_config.w_px),
            "flap_btm_side1": (x1, y2, sku_config.w_px, sku_config.w_px),
            "flap_btm_front2":  (x2, y2, sku_config.l_px, sku_config.w_px),
            "flap_btm_side2": (x3, y2, sku_config.w_px, sku_config.w_px),
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
        """生成 Exacme 全搭盖样式需要的所有面板"""
        
        canvas_front = self.generate_exacme_front_panel(sku_config)
        canvas_side = self.generate_exacme_side_panel(sku_config)
        canvas_left_up, canvas_left_down, canvas_right_up, canvas_right_down = self.generate_exacme_left_panel(sku_config)
        canvas_blank = Image.new(sku_config.color_mode, (sku_config.w_px, sku_config.w_px), sku_config.background_color)


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
        """加载 Exacme 全搭盖样式的图片资源"""
        res_base = self.base_dir / 'assets' / 'Exacme' / '全搭盖' / '矢量文件'
        
        self.resources = {
            'icon_logo_product': Image.open(res_base / '正唛公司logo及产品名称.png').convert('RGBA'),
            'icon_top_logo': Image.open(res_base / '全搭盖顶部logo.png').convert('RGBA'),
            'icon_top_attention': Image.open(res_base / '全搭盖顶部提示标.png').convert('RGBA'),
            'icon_top_smallicons': Image.open(res_base / '全搭盖顶部提示图标.png').convert('RGBA'),
            'icon_top_notice': Image.open(res_base / '全搭盖顶部保留箱子提示.png').convert('RGBA'),
            'icon_company': Image.open(res_base / '正唛公司信息.png').convert('RGBA'),
            'icon_side_label': Image.open(res_base / '侧唛标签.png').convert('RGBA'),
        }
    
    def _load_fonts(self):
        """加载字体路径"""
        font_base = self.base_dir / 'assets' / 'Exacme' / '全搭盖' / '箱唛字体'
        self.font_paths = {
            'Arial Regular': str(font_base / 'arial.ttf'),
            'Arial Bold': str(font_base / 'arialbd.ttf'),
            'Arial Black': str(font_base / 'ariblk.ttf'),
        }
        
    def generate_exacme_front_panel(self, sku_config):
        # 准备画布
        canvas = Image.new(sku_config.color_mode, (sku_config.l_px, sku_config.h_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        
        # 准备字体 (根据你的设计图，左边字号大且粗，右边正常)
        font_size_top_left = int(canvas.height * 0.12) # 左上角字体大小占正身高度的 12%
        font_size_top_right = int(canvas.height * 0.08) # 右上角字体大小占正身高度的 8%
        font_top_left = ImageFont.truetype(self.font_paths['Arial Black'], font_size_top_left)
        font_top_right = ImageFont.truetype(self.font_paths['Arial Bold'], font_size_top_right)
        
        
        # 制作顶部的一整行 (魔法降临！)
        match = re.search(r'S(\d{2})', sku_config.sku_name)

        if match:
            # group(1) 代表获取括号里匹配到的那一部分
            product_size_number = match.group(1) 
            print(f"提取成功: {product_size_number}")  # 输出: 12
        else:
            print("没有找到匹配的数字")
            raise ValueError("SKU 名称格式不正确，无法提取尺寸信息")
        
        top_padding = int( 2.5 * sku_config.dpi )  # 顶部和左右安全距离，2.5厘米的像素值
        
        top_row = engine.Row(
            fixed_width = sku_config.l_px, # 锁死宽度为箱唛物理长
            justify = 'space-between',     # 开启两端对齐魔法
            padding = top_padding,         # 让文字离箱子边缘有 40px 的安全距离
            align = 'center',              # 如果左右字号不一样，让它们在同一水平中心线上
            children = [
                engine.Text(f"{product_size_number}FT", font=font_top_left),
                engine.Text(f"{sku_config.color}", font=font_top_right)
            ]
        )
        
        
        # 把正唛公司logo及产品名称放在正唛的正中间，logo的宽度占正身宽度的 37%，高度自适应
        icon_logo_product = self.resources['icon_logo_product']
        icon_logo_product_target_width = int(canvas.width * 0.37)
        general_functions.paste_image_center_with_heightorwidth(canvas, icon_logo_product, width=icon_logo_product_target_width)
        
        # 放置左下角正唛公司信息和右下角SKU_name
        icon_company = self.resources['icon_company']
        icon_company_target_width = int(canvas.width * 0.19) # 公司信息占正身宽度的 19%
        icon_company_resized = icon_company.resize((icon_company_target_width, int(icon_company_target_width * icon_company.height / icon_company.width)), Image.Resampling.LANCZOS)
        
        font_size_bottom_right = int(canvas.height * 0.14) # 右下角SKU_name字体大小占正身高度的 14%
        font_bottom_right = ImageFont.truetype(self.font_paths['Arial Bold'], font_size_bottom_right)
        # SKU 黑框内部的文字内边距 ( 1 厘米)
        sku_box_internal_padding = int(1.0  * sku_config.dpi)
        # SKU 黑框的圆角半径 (要大一点才像腰圆型)
        sku_box_radius = int(canvas.height * 0.05)
        
        bottom_row = engine.Row(
            fixed_width=sku_config.l_px,  # 锁死宽度
            justify='space-between',      # 两端对齐
            align='bottom',               # 【关键】垂直方向靠下对齐
            padding=top_padding,          # 与顶行保持一致的安全边距
            children=[
                # --- 左下角元素 ---
                # 给图片自己设置大的安全内边距，把它“撑”离左下角
                engine.Image(icon_company_resized, nudge_y= int( icon_company_resized.height * 0.2) ),  # 图片本身的高度就是它的安全边距，这样就能保证图片完全在安全区域内

                # --- 右下角元素 ---
                engine.Text(
                    sku_config.sku_name,        # 例如 "6180-S124SG"
                    font=font_bottom_right,
                    color=sku_config.background_color,              # 白字
                    padding=sku_box_internal_padding, # 文字离黑框边缘的距离
                    draw_background=True,       # 开启背景魔法
                    background_color='black',   # 黑底
                    border_radius=sku_box_radius # 圆角
                )
            ]
        )
        
        # 把 顶行、底行 全部塞进一个大 Column 里
        main_panel = engine.Column(
            fixed_height=sku_config.h_px, # 锁死整个大盒子的高度 = 箱子高度
            justify='space-between',      # 让上中下三块在垂直方向上两端对齐(中间块自动居中)
            align='center',               # 保证中间那个 center_block 在水平方向绝对居中
            padding=0,                    # 大面板也不要 padding，保证顶底贴边
            children=[
                top_row,       # 顶部行 (自带 safe padding)
                bottom_row     # 底部行 (左侧自带 padding，右侧贴边)
            ]
        )

        # ================= 渲染 =================
        # 见证奇迹：只需要告诉大管家从 (0,0) 开始干活就行了
        main_panel.layout(0, 0)
        main_panel.render(draw)
        
        return canvas
        
    def generate_exacme_side_panel(self, sku_config):
        # 1. 准备画布
        canvas = Image.new(sku_config.color_mode, (sku_config.w_px, sku_config.h_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        

        
        
        return canvas
    
    def generate_exacme_left_panel(self, sku_config):
        # 1. 准备画布
        canvas = Image.new(sku_config.color_mode, (sku_config.l_px, sku_config.w_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        canvas_left_down, canvas_right_up = canvas, canvas
        
        # 准备字体 
        font_size_top_right = int(canvas.height * 0.12) # 右上角字体大小占正身高度的 12%
        font_top_right = ImageFont.truetype(self.font_paths['Arial Black'], font_size_top_right)

        # 准备图片资源
        
        
        
        # 制作顶部的一整行 (魔法降临！)
        match = re.search(r'S(\d{2})', sku_config.sku_name)

        if match:
            # group(1) 代表获取括号里匹配到的那一部分
            product_size_number = match.group(1) 
            print(f"提取成功: {product_size_number}")  # 输出: 12
        else:
            print("没有找到匹配的数字")
            raise ValueError("SKU 名称格式不正确，无法提取尺寸信息")
        
        top_padding = int( 2.5 * sku_config.dpi )  # 顶部和左右安全距离，2.5厘米的像素值
        
        top_row = engine.Row(
            fixed_width = sku_config.l_px, # 锁死宽度为箱唛物理长
            justify = 'space-between',     # 开启两端对齐魔法
            padding = top_padding,         # 让文字离箱子边缘有 40px 的安全距离
            align = 'center',              # 如果左右字号不一样，让它们在同一水平中心线上
            children = [
                
                engine.Text(f"{product_size_number}FT", font=font_top_right),
                
            ]
        )
        
        
        
        
        
        canvas_left_up = canvas.copy()
        canvas_right_down = canvas.rotate(180, expand=True) # 旋转90度作为右下角的面板
        return canvas_left_up, canvas_left_down, canvas_right_up, canvas_right_down
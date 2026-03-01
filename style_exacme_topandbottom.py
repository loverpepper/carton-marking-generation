"""
@author: Yushu
"""


from PIL import Image, ImageDraw, ImageFont
from style_base import BoxMarkStyle, StyleRegistry
import general_functions

@StyleRegistry.register
class ExacmeTopAndBottomStyle(BoxMarkStyle):
    '''Exacme 天地盖样式'''

    def get_style_name(self):
        return "exacme_topandbottom"

    def get_style_description(self):
        return "Exacme 天地盖箱唛样式 - 带线描图、底部警告栏"

    def get_required_params(self):
        return ['length_cm', 'width_cm', 'height_cm', 'sku_name', 'box_number']

    def get_layout_config(self, sku_config):
        '''
        Exacme 天地盖样式 - 5块布局（3列3行）
        修正布局：中间大面 (L x W)，上下侧面 (L x H)，左右侧面 (H x W)
        '''
        x0 = 0
        x1 = sku_config.h_px
        x2 = sku_config.h_px + sku_config.l_px

        y0 = 0
        y1 = sku_config.h_px
        y2 = sku_config.h_px + sku_config.w_px

        return {
            "back_side_panel": (x1, y0, sku_config.l_px, sku_config.h_px),
            "left_side_panel": (x0, y1, sku_config.h_px, sku_config.w_px),
            "top_panel": (x1, y1, sku_config.l_px, sku_config.w_px),
            "right_side_panel": (x2, y1, sku_config.h_px, sku_config.w_px),
            "front_side_panel": (x1, y2, sku_config.l_px, sku_config.h_px)
        }

    def get_panels_mapping(self, sku_config):
        return {
            'top_panel': 'main_panel',
            'back_side_panel': 'long_side_upper',
            'front_side_panel': 'long_side_lower',
            'left_side_panel': 'short_side_left',
            'right_side_panel': 'short_side_right'
        }

    def generate_all_panels(self, sku_config):
        canvas_main = self.generate_exacme_main_panel(sku_config)
        canvas_long_side = self.generate_exacme_long_side_panel(sku_config)
        canvas_short_left, canvas_short_right = self.generate_exacme_short_side_panels(sku_config)

        # 生成 Upper (Back) 需要旋转 180 度
        canvas_long_upper = canvas_long_side.rotate(180)
        canvas_long_lower = canvas_long_side

        return {
            'main_panel': canvas_main,
            'long_side_upper': canvas_long_upper,
            'long_side_lower': canvas_long_lower,
            'short_side_left': canvas_short_left,
            'short_side_right': canvas_short_right
        }

    def _load_resources(self):
        """加载 Exacme 天地盖样式的图片资源"""
        res_base = self.base_dir / 'assets' / 'Exacme' / '天地盖' / '矢量图'

        self.resources = {
            'logo': Image.open(res_base / '1.6185-D正唛logo.png').convert('RGBA'),
            'line_drawing': Image.open(res_base / '2.6185-D正唛线描图.png').convert('RGBA'),
            'color_frame': Image.open(res_base / '3.正唛颜色底框.png').convert('RGBA'),
            'empty_frame': Image.open(res_base / '4.正唛空白框.png').convert('RGBA'),
            'info_box1': Image.open(res_base / '5.1正唛公司信息及box1.png').convert('RGBA'),
            'info_box2': Image.open(res_base / '5.2正唛公司信息及box2.png').convert('RGBA'),
            'info_box3': Image.open(res_base / '5.3正唛公司信息及box3.png').convert('RGBA'),
            'warning_1': Image.open(res_base / '6.正唛底部提示1.png').convert('RGBA'),
            'warning_2': Image.open(res_base / '7.正唛底部提示2.png').convert('RGBA'),
            'warning_3': Image.open(res_base / '8.正唛底部提示3.png').convert('RGBA'),
            'warning_bg': Image.open(res_base / '9.正唛底部提示底框.png').convert('RGBA'),
            'side_label': Image.open(res_base / '10.侧唛标签.png').convert('RGBA'),
            'side_sku_box': Image.open(res_base / '11.侧唛标签SKU旁BOX底框.png').convert('RGBA'),
            'side_info': Image.open(res_base / '12.侧唛箱子信息.png').convert('RGBA'),
            'side_warning': Image.open(res_base / '13.侧唛提示语.png').convert('RGBA'),
            'side_warning_left': Image.open(res_base / '14.侧唛提示语左.png').convert('RGBA')
        }

    def _load_fonts(self):
        """加载字体路径 """
        font_base = self.base_dir / 'assets' / 'Exacme' / '天地盖' / '字体'
        self.font_paths = {
            'CentSchbook BT': str(font_base / 'arialbd.ttf'), # Century Schoolbook
            'Calibri Bold': str(font_base / 'arialbd.ttf'),
            'CENSBKB': str(font_base / 'arialbd.ttf'),
        }

    def generate_exacme_main_panel(self, sku_config):
        """生成 Exacme 中间主面板 (L x W)"""
        # 注意: 这里是主页面，尺寸 L x W
        canvas = Image.new(sku_config.color_mode, (sku_config.l_px, sku_config.w_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        canvas_w, canvas_h = canvas.size

        # 1. 顶部 Logo (移除此处绘制，移至线描图后层绘制)
        img_logo = self.resources['logo']
        logo_h = int(canvas_h * 0.37)  # 稍微加大
        img_logo_resized = general_functions.scale_by_height(img_logo, logo_h)
        # 居中，靠上
        # canvas.paste(img_logo_resized, ((canvas_w - img_logo_resized.width) // 2, int(canvas_h * 0.35)),
        #              mask=img_logo_resized)

        # 2. 中间线描图
        # 修正: 样图中 线描图很大，作为背景一样的存在，EXACME字样在中间。
        img_line = self.resources['line_drawing']
        line_h = int(canvas_h * 0.80) # 增大到 75%
        img_line_resized = general_functions.scale_by_height(img_line, line_h)
        # 居中，稍微往上挪一点 (0.10 -> 0.05) 以免被底部遮挡
        canvas.paste(img_line_resized, ((canvas_w - img_line_resized.width) // 2, int(canvas_h * 0.05)),
                     mask=img_line_resized)

        # 重新绘制Logo (在最上层)
        canvas.paste(img_logo_resized, ((canvas_w - img_logo_resized.width) // 2, int(canvas_h * 0.30)),
                     mask=img_logo_resized)

        # 3. 底部黑色警告背景条
        img_warning_bg = self.resources['warning_bg']
        warn_bar_h = int(canvas_h * 0.10)
        img_warning_bg_resized = img_warning_bg.resize((canvas_w, warn_bar_h), Image.Resampling.LANCZOS)
        warn_bar_y = canvas_h - warn_bar_h
        canvas.paste(img_warning_bg_resized, (0, warn_bar_y), mask=img_warning_bg_resized)

        # 4. 警告图标排列
        icons = [self.resources['warning_1'], self.resources['warning_2'], self.resources['warning_3']]
        icon_h = int(warn_bar_h * 0.6)
        # 分布: 左(靠左), 中(居中), 右(居右区域)
        section_w = canvas_w // 3

        for i, icon in enumerate(icons):
            res_icon = general_functions.scale_by_height(icon, icon_h)
            pos_y = warn_bar_y + (warn_bar_h - res_icon.height) // 2

            if i == 0:
                # 左边图标：往左靠 (例如左边距 2% + 稍微一点偏移)
                pos_x = int(canvas_w * 0.02)
            elif i == 1:
                # 中间图标：保持绝对居中
                pos_x = (canvas_w - res_icon.width) // 2
            else:
                # 右边图标：靠右
                pos_x = canvas_w - res_icon.width - int(canvas_w * 0.02)

            canvas.paste(res_icon, (pos_x, pos_y), mask=res_icon)

        # 5. SKU (右下角，警告条上方)
        sku_text = sku_config.sku_name
        font_sku_size = int(canvas_h * 0.13)
        font_sku = ImageFont.truetype(self.font_paths['Calibri Bold'], font_sku_size)

        bbox = draw.textbbox((0,0), sku_text, font=font_sku)
        sku_w = bbox[2] - bbox[0]
        sku_h = bbox[3] - bbox[1]

        sku_x = canvas_w - sku_w - int(canvas_w * 0.01)
        sku_y = warn_bar_y - sku_h - int(canvas_h * 0.05)

        draw.text((sku_x, sku_y), sku_text, font=font_sku, fill=(40, 40, 40))

        # 6. Box 信息 (左下角)
        current_box = sku_config.box_number['current_box']
        img_box_info = self.resources.get(f'info_box{current_box}', self.resources['info_box1'])
        box_h = int(canvas_h * 0.15)
        img_box_resized = general_functions.scale_by_height(img_box_info, box_h)
        # 放在左下，警告条上方
        box_x = int(canvas_w * 0.02) # 调整为 0.02，更靠左
        box_y = warn_bar_y - img_box_resized.height - int(canvas_h * 0.02)
        canvas.paste(img_box_resized, (box_x, box_y), mask=img_box_resized)

        # 7. 左上角 10FT
        size_text = "10FT"
        if "10" in sku_config.sku_name: size_text = "10FT"
        elif "12" in sku_config.sku_name: size_text = "12FT"
        elif "14" in sku_config.sku_name: size_text = "14FT"

        font_ft = ImageFont.truetype(self.font_paths['Calibri Bold'], int(canvas_h * 0.08))
        # 靠左纯黑色
        draw.text((int(canvas_w * 0.01), int(canvas_h * 0.03)), size_text, font=font_ft, fill=(0, 0, 0))

        # 8. 右上角 (COL: 颜色 + 虚线框)
        # 调整逻辑：先确定下方虚线框的大小，然后让颜色框跟它一样宽

        # 8.2 下方虚线框 (先计算尺寸)
        img_empty_frame = self.resources['empty_frame']
        empty_frame_h = int(canvas_h * 0.12)
        img_empty_frame_resized = general_functions.scale_by_height(img_empty_frame, empty_frame_h)

        # 8.1 颜色底框
        img_col_frame = self.resources['color_frame']

        # 确定尺寸: 高度按比例，但宽度强制与虚线框一致
        col_frame_h = int(canvas_h * 0.08) # 原始高度计算
        # img_col_frame_resized = general_functions.scale_by_height(img_col_frame, col_frame_h)
        # 强制宽度一致
        img_col_frame_resized = img_col_frame.resize((img_empty_frame_resized.width, col_frame_h), Image.Resampling.LANCZOS)

        # 确定位置: 右上角，留出边距
        right_margin = int(canvas_w * 0.02)
        top_margin = int(canvas_h * 0.05)

        # 对齐虚线框的位置 (虚线框在下，颜色框在上)
        # 颜色框的位置
        col_x = canvas_w - img_col_frame_resized.width - right_margin
        col_y = top_margin

        canvas.paste(img_col_frame_resized, (col_x, col_y), mask=img_col_frame_resized)

        # 绘制颜色文字 "COL : Turquoise"
        # 从配置中获取颜色，去掉括号
        color_text = "Turquoise"
        full_color_text = f"COL : {color_text}"

        # 字体颜色: 浅色/白色? 样图中 fondo 是深色，字是浅色
        font_col = ImageFont.truetype(self.font_paths['Calibri Bold'], int(col_frame_h * 0.5))

        # 文字居中于底框
        bbox_col = draw.textbbox((0,0), full_color_text, font=font_col)
        text_w = bbox_col[2] - bbox_col[0]
        text_h = bbox_col[3] - bbox_col[1]

        text_x = col_x + (img_col_frame_resized.width - text_w) // 2
        text_y = col_y + (img_col_frame_resized.height - text_h) // 2
        # 微调y
        text_y -= int(col_frame_h * 0.1)

        draw.text((text_x, text_y), full_color_text, font=font_col, fill=(161, 142, 102)) # 白色

        # 8.2 绘制下方虚线框 (位置依赖于颜色框)
        empty_x = col_x + (img_col_frame_resized.width - img_empty_frame_resized.width) // 2
        empty_y = col_y + img_col_frame_resized.height + int(canvas_h * 0.02) # 间隔

        canvas.paste(img_empty_frame_resized, (empty_x, empty_y), mask=img_empty_frame_resized)

        return canvas

    def generate_exacme_short_side_panels(self, sku_config):
        """生成 Exacme 短侧面板 (左右侧，H x W)
           只放置 side_label，旋转90度
        """
        # left_side_panel: (x0, y1, sku_config.h_px, sku_config.w_px) -> H x W

        canvas = Image.new(sku_config.color_mode, (sku_config.h_px, sku_config.w_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        cw, ch = canvas.size

        # 1. 侧唛标签 (Barcode 区域)
        img_label = self.resources['side_label']
        # 旋转 90 度
        #img_label = img_label.rotate(90, expand=True)

        # 调整大小: 宽度撑满 canvas 宽度的 85%
        label_w = int(cw * 0.85) # 占满宽度 85%
        img_label_resized = general_functions.scale_by_width(img_label, label_w)

        # 如果高度超过了 canvas 高度，则按高度缩放4
        if img_label_resized.height > ch * 0.85:
            label_h = int(ch * 0.85)
            img_label_resized = general_functions.scale_by_height(img_label, label_h)

        # 居中放置
        label_x = (cw - img_label_resized.width) // 2
        label_y = (ch - img_label_resized.height) // 2
        canvas.paste(img_label_resized, (label_x, label_y), mask=img_label_resized)

        # 2. SKU 旁边的 Box 颜色块 (side_sku_box)
        # 用户需求：垂直放在侧边箱唛的side_label元素的图层之上，然后靠侧边的左放在黑边上
        img_side_sku_box = self.resources['side_sku_box']

        # 调整大小: 假设高度为 label 高度的 12% (稍微调小一点，确保能放入黑边)
        sku_box_h = int(img_label_resized.height * 0.12)
        img_side_sku_resized = general_functions.scale_by_height(img_side_sku_box, sku_box_h)

        # side_sku_box 的位置：
        #box_x = label_x + int(img_label_resized.width * 0.04) # 靠左

        # 让我们把 box 放在 label 左上部分（黑框区域）。
        box_x = label_x + int(img_label_resized.width * 0.13) # 经验值：左侧黑框边距
        box_y = label_y + int(img_label_resized.height * 0.185) # 顶部边距

        canvas.paste(img_side_sku_resized, (box_x, box_y), mask=img_side_sku_resized)

        # 3. 写入 Box 信息 "Box X of Y" (竖着写入)
        current_box = sku_config.box_number['current_box']
        total_boxes = sku_config.box_number['total_boxes']
        box_text = f"Box {current_box} of {total_boxes}"

        # 创建临时 canvas 绘制文字然后旋转
        font_box_size = int(img_side_sku_resized.width * 0.65) # 字体大小基于宽度
        font_box = ImageFont.truetype(self.font_paths['Calibri Bold'], font_box_size)

        bbox_box = draw.textbbox((0,0), box_text, font=font_box)
        text_w = bbox_box[2] - bbox_box[0]
        text_h = bbox_box[3] - bbox_box[1]

        # 创建透明层绘制文字
        txt_img = Image.new('RGBA', (int(text_w), int(text_h)), (255, 255, 255, 0))
        d_txt = ImageDraw.Draw(txt_img)
        d_txt.text((0, 0), box_text, font=font_box, fill=(0, 0, 0))

        # 改为90
        txt_img_rot = txt_img.rotate(90, expand=True)

        # 居中显示在 box 图片上
        text_x = box_x + (img_side_sku_resized.width - txt_img_rot.width) // 2
        # 用户需求：再稍微靠左一点
        text_x -= int(img_side_sku_resized.width * 0.17)

        text_y = box_y + (img_side_sku_resized.height - txt_img_rot.height) // 2

        canvas.paste(txt_img_rot, (text_x, text_y), mask=txt_img_rot)

        # 4. 写入 SKU (在 side_sku_box 下方，也是竖着写入)
        sku_text = sku_config.sku_name
        font_sku_size = int(img_side_sku_resized.width * 2.3) # 基于宽度
        font_sku = ImageFont.truetype(self.font_paths['Calibri Bold'], font_sku_size)

        bbox_sku = draw.textbbox((0,0), sku_text, font=font_sku)
        sku_w = bbox_sku[2] - bbox_sku[0]
        sku_h = bbox_sku[3] - bbox_sku[1]

        txt_sku_img = Image.new('RGBA', (int(sku_w), int(sku_h)), (255, 255, 255, 0))
        d_sku = ImageDraw.Draw(txt_sku_img)
        d_sku.text((0, 0), sku_text, font=font_sku, fill=(161, 142, 102))

        txt_sku_rot = txt_sku_img.rotate(90, expand=True) # 同样旋转改为90

        # 位置: side_sku_box 下方，水平居中对齐 box
        # 间距
        gap = int(ch * 0.015)
        sku_x = box_x + (img_side_sku_resized.width - txt_sku_rot.width) // 2

        # SKU信息再靠左一点
        sku_x -= int(img_side_sku_resized.width * 1.1)

        sku_y = box_y + img_side_sku_resized.height + gap

        # 颜色: 白色 (在黑框上)
        canvas.paste(txt_sku_rot, (sku_x, sku_y), mask=txt_sku_rot)

        # 5. 生成条形码 (SKU 条码) - 放置在 side_sku_box 右侧区域
        barcode_len_px = int(img_label_resized.height * 0.31) # 缩短条码长度
        barcode_thickness_px = int(img_label_resized.width * 0.33)

        # 1. SKU Barcode
        sku_code = sku_config.sku_name
        # 调用 general_functions 生成条码 (返回只有条码的透明图片)
        # generate_barcode_image(code, width, height) -> width is barcode length, height is bars height
        img_sku_barcode = general_functions.generate_barcode_image(sku_code, barcode_len_px, barcode_thickness_px)

        # 旋转 90 度 (变成竖条: height becomes width, width becomes height)
        img_sku_barcode_rot = img_sku_barcode.rotate(90, expand=True)

        # 定位: 在 side_sku_box 的右边
        # box_x 是 side_sku_box 的左边缘
        # barcode_x 应该在 box 右侧
        barcode_x = box_x + img_side_sku_resized.width + int(cw * 0.05)

        # 第一个放在上面，第二个放在下面
        barcode_y_1 = label_y + int(img_label_resized.height * 0.02) # 顶部对齐 label 内容区

        canvas.paste(img_sku_barcode_rot, (barcode_x, barcode_y_1), mask=img_sku_barcode_rot)

        # 2. 第二个条形码
        second_code = getattr(sku_config, 'upc_number', None) or "BOX-CODE-EXAMPLE"
        if hasattr(sku_config, 'side_text') and isinstance(sku_config.side_text, dict):
             second_code = sku_config.side_text.get('sn_code', second_code)

        img_sn_barcode = general_functions.generate_barcode_image(second_code, barcode_len_px, barcode_thickness_px)
        img_sn_barcode_rot = img_sn_barcode.rotate(90, expand=True)

        # 第二个条码在第一个条码下方 (x 坐标相同)
        barcode_x_2 = barcode_x
        # 间距调小一点
        gap_barcodes = int(img_label_resized.height * 0.02)
        barcode_y_2 = barcode_y_1 + img_sku_barcode_rot.height + gap_barcodes

        canvas.paste(img_sn_barcode_rot, (barcode_x_2, barcode_y_2), mask=img_sn_barcode_rot)

        # 条形码右侧的微小文字 (竖排)
        # 上方条码右侧: "09429381135347" (UPC or similar)
        # 下方条码右侧: "MADE IN CHINA"
        # 字体 调大一点
        tiny_font_size = int(img_label_resized.width * 0.06)
        tiny_font = ImageFont.truetype(self.font_paths['Calibri Bold'], tiny_font_size)

        # 上方文字 (优先使用 side_text 中的 sn_code)
        text_up = "BOX-CODE-EXAMPLE"
        if hasattr(sku_config, 'side_text') and isinstance(sku_config.side_text, dict):
             text_up = sku_config.side_text.get('sn_code', text_up)
        # 也可以回退到 upc_number 如果 sn_code 不存在
        if text_up == "BOX-CODE-EXAMPLE" and getattr(sku_config, 'upc_number', None):
            text_up = sku_config.upc_number

        bbox_up = draw.textbbox((0,0), text_up, font=tiny_font)
        w_up = bbox_up[2] - bbox_up[0]
        h_up = bbox_up[3] - bbox_up[1]

        txt_up_img = Image.new('RGBA', (int(w_up), int(h_up)), (255, 255, 255, 0))
        d_up = ImageDraw.Draw(txt_up_img)
        d_up.text((0, 0), text_up, font=tiny_font, fill=(0, 0, 0))
        # 旋转 90 度
        # orientation. Vertical text usually is rotated.
        txt_up_rot = txt_up_img.rotate(90, expand=True)

        # 位置: 上方条码 (img_sku_barcode_rot) 的右侧
        # barcode_x 是条码左边， barcode_x + width 是条码右边
        text_up_x = barcode_x + img_sku_barcode_rot.width + int(cw * 0.005)
        # 垂直居中于上方条码
        text_up_y = barcode_y_1 + (img_sku_barcode_rot.height - txt_up_rot.height) // 2

        canvas.paste(txt_up_rot, (text_up_x, text_up_y), mask=txt_up_rot)

        # 下方文字 "MADE IN CHINA" (优先使用 side_text 中的 origin_text)
        text_down = "MADE IN CHINA"
        if hasattr(sku_config, 'side_text') and isinstance(sku_config.side_text, dict):
             text_down = sku_config.side_text.get('origin_text', text_down)

        bbox_down = draw.textbbox((0,0), text_down, font=tiny_font)
        w_down = bbox_down[2] - bbox_down[0]
        h_down = bbox_down[3] - bbox_down[1]

        txt_down_img = Image.new('RGBA', (int(w_down), int(h_down)), (255, 255, 255, 0))
        d_down = ImageDraw.Draw(txt_down_img)
        d_down.text((0, 0), text_down, font=tiny_font, fill=(0, 0, 0))
        txt_down_rot = txt_down_img.rotate(90, expand=True)

        # 位置: 下方条码 (img_sn_barcode_rot) 的右侧
        text_down_x = barcode_x_2 + img_sn_barcode_rot.width + int(cw * 0.005)
        # 垂直居中于下方条码
        text_down_y = barcode_y_2 + (img_sn_barcode_rot.height - txt_down_rot.height) // 2

        canvas.paste(txt_down_rot, (text_down_x, text_down_y), mask=txt_down_rot)

        # 返回两个 canvas (左右侧板)
        # 左边的旋转180度
        return canvas.rotate(180), canvas

    def generate_exacme_long_side_panel(self, sku_config):
        """生成 Exacme 长侧面板 (上下侧，L x H) - 显示 SHIP IN 3 BOXES + 左右提示语"""
        canvas = Image.new(sku_config.color_mode, (sku_config.l_px, sku_config.h_px), sku_config.background_color)
        draw = ImageDraw.Draw(canvas)
        canvas_w, canvas_h = canvas.size

        # 1. 中间部分 side_info (使用图片 side_info)
        # 放在中间
        if 'side_info' in self.resources:
            img_info = self.resources['side_info']
            # side_info 在短侧是 0.7 H. 在这里也类似
            img_info_h = int(canvas_h * 0.55) # 调小
            img_info_resized = general_functions.scale_by_height(img_info, img_info_h)

            x_pos = (canvas_w - img_info_resized.width) // 2
            y_pos = (canvas_h - img_info_resized.height) // 2
            canvas.paste(img_info_resized, (x_pos, y_pos), mask=img_info_resized)

        # 2. 左侧提示语 (使用图片 side_warning_left)
        # 放在左侧
        if 'side_warning_left' in self.resources:
            img_left = self.resources['side_warning_left']
            img_left_h = int(canvas_h * 0.25) # 调小
            img_left_resized = general_functions.scale_by_height(img_left, img_left_h)

            # 靠左边距
            left_margin = int(canvas_w * 0.02) # 调小边距，更靠左
            y_pos = (canvas_h - img_left_resized.height) // 2
            canvas.paste(img_left_resized, (left_margin, y_pos), mask=img_left_resized)

        # 3. 右侧提示语 (使用图片 side_warning)
        # 放在右侧
        if 'side_warning' in self.resources:
            img_right = self.resources['side_warning']
            img_right_h = int(canvas_h * 0.25) # 调小
            img_right_resized = general_functions.scale_by_height(img_right, img_right_h)

            right_margin = int(canvas_w * 0.02) # 调小边距，更靠右
            x_pos = canvas_w - img_right_resized.width - right_margin
            y_pos = (canvas_h - img_right_resized.height) // 2
            canvas.paste(img_right_resized, (x_pos, y_pos), mask=img_right_resized)

        return canvas

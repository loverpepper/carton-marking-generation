from PIL import Image, ImageDraw, ImageFont
import numpy as np  
import pathlib as Path
import barcode
from barcode.writer import ImageWriter
base_dir = Path.Path(__file__).parent

'''
已有的函数千万别动，但是可以调用它们，或者复制粘贴到新的函数里修改
可以在后面无限加自己的函数

'''


def paste_center_with_height(canvas, icon, height_cm, dpi):
    """
    将 icon 按照指定高度等比例缩放后，居中粘贴到 canvas 上
    """
    # 1. 计算目标高度的像素值 (10cm)
    # 300 PPI 下，1英寸=2.54cm，所以 10cm 对应的像素如下：
    target_height_px = int(height_cm * dpi)  # 10 cm 转像素

    # 2. 计算缩放比例并调整图片大小
    # 原始尺寸
    original_w, original_h = icon.size
    # 计算比例：保持长宽比不变
    ratio = target_height_px / original_h
    target_width_px = int(original_w * ratio)

    # 调整图标尺寸 (使用 Resampling.LANCZOS 保证印刷级清晰度)
    icon_resized = icon.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)

    # 3. 计算居中坐标
    # 画布尺寸 (l_px 是长，w_px 是宽)
    canvas_w, canvas_h = canvas.size
    # 居中位置 = (画布宽 - 图标宽)//2 , (画布高 - 图标高)//2
    paste_x = (canvas_w - target_width_px) // 2
    paste_y = (canvas_h - target_height_px) // 2

    # 4. 粘贴到画布 (注意：必须使用 icon_resized 自身作为 mask 以保持透明背景)
    canvas.paste(icon_resized, (paste_x, paste_y), mask=icon_resized)
    
    return canvas

def scale_by_height(image, target_height):
    """根据目标高度等比例缩放图片"""
    w, h = image.size
    target_width = int(w * (target_height / h))
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)

def scale_by_width(image, target_width):
    """根据目标宽度等比例缩放图片"""
    w, h = image.size
    target_height = int(h * (target_width / w))
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)

def draw_rounded_bg_for_text(draw, bbox, sku_config, color_xy,
                             bg_color=(0, 0, 0), padding_cm=(0.8, 0.3), radius=15):
    """
    只绘制圆角矩形背景，并返回建议的文字起始坐标。
    """
    # 1. 计算文字尺寸（只测量，不绘制）
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # 2. 转换间距
    px_padding_x = int(padding_cm[0] * sku_config.dpi) #左右内边距 padding_cm[0]
    px_padding_y = int(padding_cm[1] * sku_config.dpi) #上下内边距 padding_cm[1]
    
    # 调整上下边距比例，使视觉上更平衡
    px_padding_y_top = int(px_padding_y * 0.7 )    # 上边距增加30%
    px_padding_y_bottom = int(px_padding_y * 1.4 ) # 下边距减少30%
    
    # 3. 计算黑框整体尺寸
    rect_w = text_w + 2 * px_padding_x
    rect_h = text_h + px_padding_y_top + px_padding_y_bottom
    
    # 4. 计算黑框坐标 (以右上角为锚点)
    color_x, color_y = color_xy
    rect_x0 = color_x - px_padding_x
    rect_y0 = color_y - px_padding_y_top
    rect_x1 = color_x + text_w + px_padding_x
    rect_y1 = color_y + text_h + px_padding_y_bottom
    
    # 5. 绘制圆角矩形
    draw.rounded_rectangle([rect_x0, rect_y0, rect_x1, rect_y1], radius=radius, fill=bg_color)
    return draw


def draw_smooth_ellipse(draw, canvas, box, fill=(0, 0, 0), scale=4):
    """
    可以用于Mconbo两种样式正唛产品名下方的椭圆形装饰
    在指定的 box 区域内绘制一个丝滑的椭圆形（抗锯齿）
    scale: 放大倍数，越高越丝滑，通常 4 足够。
    """
    x0, y0, x1, y1 = box
    w = int((x1 - x0) * scale)
    h = int((y1 - y0) * scale)
    
    # 创建一个透明的高清临时层
    temp_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # 在高清层画椭圆
    temp_draw.ellipse([0, 0, w, h], fill=fill)
    
    # 缩小回目标尺寸 (使用 LANCZOS 或 HAMMING 滤镜)
    smooth_line = temp_img.resize((int(x1 - x0), int(y1 - y0)), resample=Image.LANCZOS)
    
    # 粘贴回主画布
    canvas.paste(smooth_line, (int(x0), int(y0)), mask=smooth_line)
    
def draw_dynamic_bottom_bg(canvas, sku_config, icon_company, icon_box_number, font_paths):
    draw = ImageDraw.Draw(canvas)
    canvas_w, canvas_h = canvas.size
    bottom_bg_h = int(sku_config.bottom_gb_h * sku_config.dpi)
    # --- 1. 计算基础尺寸 ---
    h_right = int( 10 * sku_config.dpi)  # 10 cm 高的黑色底框
    h_left = int( 0.5 * h_right)  # 左侧底框高度为右侧的50%    
    margin_1cm = int( 1 * sku_config.dpi)
    margin_2cm = int( 2 * sku_config.dpi)  
    margin_3cm = int( 3 * sku_config.dpi)
    margin_4cm = int( 4 * sku_config.dpi)
    margin_6cm = int( 6 * sku_config.dpi)
    margin_8cm = int( 8 * sku_config.dpi)
    margin_10cm = int( 10 * sku_config.dpi)  
    
    # --- 2. 处理公司信息 Logo 并确定左侧宽度 ---
    # Logo 与底框上边缘平齐，高度设为 1.6 cm
    icon_h = int(1.6 * sku_config.dpi) 
    icon_company_res = scale_by_height(icon_company, icon_h)
    icon_company_w, _ = icon_company_res.size
    
    # 左侧“弧头”总宽度 = 1cm + Logo宽 + 4cm
    left_section_w = margin_1cm + icon_company_w + margin_4cm
    
    # --- 3. 绘制异形底框 (黑色) ---
    # A. 左侧小矩形 + 右侧大矩形 + 中间连接部分
    # 绘制贝塞尔曲线过渡部分
    
    # --- a. 准备工作 ---
    # 过渡区的起点 (x3, y3) 和 终点 (x4, y4)
    x3, y3 = left_section_w - margin_10cm, canvas_h - h_left
    x4, y4 = left_section_w , canvas_h - h_right

    # --- b. 绘制左侧和右侧的方块 ---
    # 左侧矮块
    draw.rectangle([0, canvas_h - h_left, x3, canvas_h], fill=(0, 0, 0))
    # 右侧高块
    draw.rectangle([x4, canvas_h - h_right, canvas_w, canvas_h], fill=(0, 0, 0))

    # --- c. 绘制丝滑过渡区 (关键：贝塞尔曲线模拟) ---
    # 我们在 3 到 4 之间生成 20个点，连成一个平滑的填充区域
    curve_points = []
    for i in range(21):
        t = i / 20
        # 二次方贝塞尔公式：(1-t)^2*P0 + 2t(1-t)*P1 + t^2*P2
        # 这里我们简化处理，让它形成一个 S 形
        curr_x = x3 + (x4 - x3) * t
        # 使用 smoothstep 函数使 y 的变化更平滑
        t_smooth = t * t * (3 - 2 * t) 
        curr_y = y3 + (y4 - y3) * t_smooth
        curve_points.append((curr_x, curr_y))

    # 将曲线点与底部封口，形成封闭图形填充
    curve_fill_path = curve_points + [(x4, canvas_h), (x3, canvas_h)]
    draw.polygon(curve_fill_path, fill=(0, 0, 0))
    
    # B. 粘贴公司信息 Logo
    icon_x = margin_1cm
    icon_y = canvas_h - bottom_bg_h
    canvas.paste(icon_company_res, (icon_x, icon_y), mask=icon_company_res)
    
    # C. 粘贴左下角箱号信息
    icon_box_h = int( h_right * 1/4)  # 高度为底框高度的25%
    icon_box_res = scale_by_height(icon_box_number, icon_box_h)
    icon_box_w, icon_box_h = icon_box_res.size
    icon_box_x = margin_1cm
    icon_box_y = int(canvas_h - h_left + (h_left - icon_box_h) // 2)  # 垂直居中
    canvas.paste(icon_box_res, (icon_box_x, icon_box_y), mask=icon_box_res)
    
    # --- 4. 动态 SKU 文字 (带自动缩放) ---
    # 可用宽度：从 margin_1cm + icon_company_w 到 canvas_w - margin_3cm
    max_sku_w = canvas_w - (margin_1cm + icon_company_w) - margin_3cm
    max_sku_h = margin_8cm  # 文字高度不超过 8cm（增大以让文字更显眼）
    # 初始字号应该根据高度动态计算（字号单位是像素）
    current_sku_size = int(max_sku_h * 1.2)  # 初始为最大高度的1.2倍
    min_sku_size = int(max_sku_h * 0.15)  # 最小字号为最大高度的15%
    
    print(f"[正唛SKU调试] 画布宽度: {canvas_w}px ({canvas_w/sku_config.dpi:.1f}cm)")
    print(f"[正唛SKU调试] 可用SKU宽度: {max_sku_w}px ({max_sku_w/sku_config.dpi:.1f}cm)")
    print(f"[正唛SKU调试] 可用SKU高度: {max_sku_h}px ({max_sku_h/sku_config.dpi:.1f}cm)")
    print(f"[正唛SKU调试] 初始字号: {current_sku_size}pt, 最小字号: {min_sku_size}pt")
    
    # 自动减小字号直到宽度和高度都满足要求
    sku_font = None
    while current_sku_size > min_sku_size:
        test_font = ImageFont.truetype(font_paths['calibri_bold'], size=current_sku_size)
        bbox = draw.textbbox((0, 0), sku_config.sku_name, font=test_font)
        sw = bbox[2] - bbox[0]
        sh = bbox[3] - bbox[1]
        
        # 检查宽度和高度是否都符合要求
        if sw <= max_sku_w and sh <= max_sku_h:
            sku_font = test_font
            sku_w, sku_h = sw, sh
            print(f"[正唛SKU调试] 最终字号: {current_sku_size}pt, 文字尺寸: {sw}x{sh}px ({sw/sku_config.dpi:.1f}x{sh/sku_config.dpi:.1f}cm)")
            break
        current_sku_size -= 5
    
    # 如果没有找到合适的字号，使用最小字号
    if sku_font is None:
        sku_font = ImageFont.truetype(font_paths['calibri_bold'], size=min_sku_size)
        bbox = draw.textbbox((0, 0), sku_config.sku_name, font=sku_font)
        sku_w = bbox[2] - bbox[0]
        sku_h = bbox[3] - bbox[1]

    # 绘制 SKU (在底框右侧区域中居中)
    # 计算 SKU 可用区域的中心点
    sku_area_left = margin_1cm + icon_company_w + margin_3cm
    sku_area_right = canvas_w - margin_3cm
    sku_center_x = (sku_area_left + sku_area_right) // 2
    
    # 底框高度区域的垂直中心，稍微向下偏移
    offset_y = int(0.3 * sku_config.dpi)  # 向下偏移 0.3cm
    sku_center_y = canvas_h - h_right // 2 + offset_y
    
    # 使用 "mm" anchor 让文字的中心点对齐到区域中心
    draw.text((sku_center_x, sku_center_y), sku_config.sku_name, font=sku_font, fill=(161, 142, 102), anchor="mm")

    
    
def draw_side_dynamic_bottom_bg(canvas, sku_config, icon_company, font_paths):
    draw = ImageDraw.Draw(canvas)
    canvas_w, canvas_h = canvas.size
    bottom_bg_h = int(sku_config.bottom_gb_h * sku_config.dpi)
    # --- 1. 计算基础尺寸 ---
    h_left = int( sku_config.dpi * sku_config.bottom_gb_h)  # 10 cm 高的黑色底框  
    h_right =  int( h_left * 0.5) # 右侧侧底框高度为左侧的50%
    
    margin_1cm = int( 1 * sku_config.dpi)
    margin_2cm = int( 2 * sku_config.dpi)  
    margin_3cm = int( 3 * sku_config.dpi)
    margin_4cm = int( 4 * sku_config.dpi)
    margin_6cm = int( 6 * sku_config.dpi)
    margin_8cm = int( 8 * sku_config.dpi)
    margin_10cm = int( 10 * sku_config.dpi)  
    
    # --- 2. 处理公司信息 Logo 并确定右侧宽度 ---
    # Logo 与底框上边缘平齐，高度设为 1.6 cm
    icon_h = int(1.6 * sku_config.dpi) 
    icon_company_res = scale_by_height(icon_company, icon_h)
    icon_company_w, _ = icon_company_res.size
    
    # 侧唛SKU黑框部分长度与正唛设计相同，即左侧“弧头”总宽度 = 1cm + Logo宽 + 4cm。sku_config.l_px - 该值就是右侧底框宽度
    left_section_w = sku_config.l_px - (margin_1cm + icon_company_w + margin_4cm)
    
    # 边界检查：如果正唛太宽，需要限制 left_section_w 不超过侧唛宽度
    # 确保至少留出过渡区域（10cm）和右侧一些空间
    max_left_section_w = canvas_w - margin_10cm - margin_4cm  # 留出过渡区和右侧边距
    if left_section_w > max_left_section_w:
        left_section_w = max_left_section_w
        print(f"警告：正唛宽度过大，侧唛SKU黑框已自动调整为 {left_section_w / sku_config.dpi:.1f}cm")
    
    # --- 3. 绘制异形底框 (黑色) ---
    # A. 左侧小矩形 + 右侧大矩形 + 中间连接部分
    # 绘制贝塞尔曲线过渡部分
    
    # --- a. 准备工作 ---
    # 过渡区的起点 (x3, y3) 和 终点 (x4, y4)
    x3, y3 = left_section_w, canvas_h - h_left
    x4, y4 = min(left_section_w + margin_10cm, canvas_w - margin_1cm), canvas_h - h_right  # 确保 x4 不超过画布宽度

    # --- b. 绘制左侧和右侧的方块 ---
    # 左侧高块
    draw.rectangle([0, canvas_h - h_left, x3, canvas_h], fill=(0, 0, 0))
    # 右侧矮块
    draw.rectangle([x4, canvas_h - h_right, canvas_w, canvas_h], fill=(0, 0, 0))

    # --- c. 绘制丝滑过渡区 (关键：贝塞尔曲线模拟) ---
    # 我们在 3 到 4 之间生成 20个点，连成一个平滑的填充区域
    curve_points = []
    for i in range(21):
        t = i / 20
        # 二次方贝塞尔公式：(1-t)^2*P0 + 2t(1-t)*P1 + t^2*P2
        # 这里我们简化处理，让它形成一个 S 形
        curr_x = x3 + (x4 - x3) * t
        # 使用 smoothstep 函数使 y 的变化更平滑
        t_smooth = t * t * (3 - 2 * t) 
        curr_y = y3 + (y4 - y3) * t_smooth
        curve_points.append((curr_x, curr_y))

    # 将曲线点与底部封口，形成封闭图形填充
    curve_fill_path = curve_points + [(x4, canvas_h), (x3, canvas_h)]
    draw.polygon(curve_fill_path, fill=(0, 0, 0))
    

    
    # --- 4. 动态 SKU 文字 (带自动缩放) ---
    # 可用宽度：从 margin_1cm + icon_company_w 到 canvas_w - margin_3cm
    max_sku_w = left_section_w
    max_sku_h = margin_8cm  # 文字高度不超过 8cm
    # 初始字号应该根据高度动态计算（字号单位是像素）
    current_sku_size = int(max_sku_h * 1.2)  # 初始为最大高度的1.2倍
    min_sku_size = int(max_sku_h * 0.15)  # 最小字号为最大高度的15%
    
    # 自动减小字号直到宽度和高度都满足要求
    sku_font = None
    while current_sku_size > min_sku_size:
        test_font = ImageFont.truetype(font_paths['calibri_bold'], size=current_sku_size)
        bbox = draw.textbbox((0, 0), sku_config.sku_name, font=test_font)
        sw = bbox[2] - bbox[0]
        sh = bbox[3] - bbox[1]
        
        # 检查宽度和高度是否都符合要求
        if sw <= max_sku_w and sh <= max_sku_h:
            sku_font = test_font
            sku_w, sku_h = sw, sh
            break
        current_sku_size -= 5
    
    # 如果没有找到合适的字号，使用最小字号
    if sku_font is None:
        sku_font = ImageFont.truetype(font_paths['calibri_bold'], size=min_sku_size)
        bbox = draw.textbbox((0, 0), sku_config.sku_name, font=sku_font)
        sku_w = bbox[2] - bbox[0]
        sku_h = bbox[3] - bbox[1]

    # 绘制 SKU (在底框左侧区域中居中)
    # 计算 SKU 可用区域的中心点
    sku_area_left = margin_3cm 
    sku_area_right = left_section_w
    sku_center_x = (sku_area_left + sku_area_right) // 2
    
    # 底框高度区域的垂直中心，稍微向下偏移
    offset_y = int(0.3 * sku_config.dpi)  # 向下偏移 0.3cm
    sku_center_y = canvas_h - h_left // 2 + offset_y
    
    # 使用 "mm" anchor 让文字的中心点对齐到区域中心
    draw.text((sku_center_x, sku_center_y), sku_config.sku_name, font=sku_font, fill=(161, 142, 102), anchor="mm")
    pass

def fill_sidepanel_text(icon_side_text_box_resized, sku_config, fonts_paths):
    """
    Mcombo 两种样式专用
    用于给侧唛表格区域填充动态文字和条码 
    在侧唛的右侧表格区域内绘制动态文字和条码
    然后返回给调用者进行粘贴
    """
    # 此时 tw, th 仅代表右侧那个格子的宽高
    tw, th = icon_side_text_box_resized.size
    draw = ImageDraw.Draw(icon_side_text_box_resized)
    
    # 1. 准备字体 (保持比例科学)
    side_font_bold_path = fonts_paths['side_font_bold']
    side_font_label_path = fonts_paths['side_font_label']
    side_font_barcode_path = fonts_paths['side_font_barcode']
    
    # 比例字号：th 为 8cm 对应的像素
    font_size_label = int(th * 0.081)   # G.W./Box Size
    font_size_bold = int(th * 0.095)    # MADE IN CHINA
    font_size_barcode = int(th * 0.058) # 条码下方的数字
    
    side_font_label = ImageFont.truetype(side_font_label_path, size=font_size_label)
    side_font_bold = ImageFont.truetype(side_font_bold_path, size=font_size_bold)
    side_font_barcode_text = ImageFont.truetype(side_font_barcode_path, size=font_size_barcode)
    
    # --- 区域 1: 右上角文字区 (注意：X 轴起点要落在最右边那个格子里) ---
    # 根据目标图，右上角单元格起点大约在表格总宽的 65% 处
    text_x_start = tw * 0.651
    side_weight_text = f'G.W./N.W.: {sku_config.side_text["gw_value"]} / {sku_config.side_text["nw_value"]} lbs'
    side_dimention_text = f'BOX SIZE: {sku_config.l_in:.1f}\'\' x {sku_config.w_in:.1f}\'\' x {sku_config.h_in:.1f}\'\''
    draw.text((text_x_start, th * 0.044), side_weight_text, font=side_font_label, fill=(0,0,0))
    draw.text((text_x_start, th * 0.214), side_dimention_text, font=side_font_label, fill=(0,0,0))
    
    # --- 区域 2: 条形码区 (分为左右两个子区域) ---
    # 定义在这个局部表格内的中轴线
    left_zone_center = tw * 0.46   # 左半区中心
    right_zone_center = tw * 0.847  # 右半区中心
    
    barcode_y = th * 0.42          # 条码顶部起始，避开上方图标的横线
    barcode_text_y = th * 0.76     # 条码下方文字起始位置
    barcode_h_px = int(th * 0.35)  # 条码高度 35%
    
    # A. 左侧 SKU 条码
    # 宽度大约占局部表格的 46%，高度 35%
    sku_barcode_img = generate_barcode_image(sku_config.sku_name, width=int(tw * 0.46), height=barcode_h_px)
    sku_x = int(left_zone_center - sku_barcode_img.width / 2)
    icon_side_text_box_resized.paste(sku_barcode_img, (sku_x, int(barcode_y)))
    
    # SKU 文本文字居中
    sku_w = draw.textlength(sku_config.sku_name, font=side_font_barcode_text)
    draw.text((left_zone_center - sku_w/2, barcode_text_y), sku_config.sku_name, font=side_font_barcode_text, fill=(0,0,0))
    
    # B. 右侧 SN 条码
    sn_code = sku_config.side_text['sn_code']
    sn_barcode_img = generate_barcode_image(sn_code, width=int(tw * 0.28), height=barcode_h_px)
    sn_x = int(right_zone_center - sn_barcode_img.width / 2)
    icon_side_text_box_resized.paste(sn_barcode_img, (sn_x, int(barcode_y)))
    
    # SN 文本文字居中
    sn_w = draw.textlength(sn_code, font=side_font_barcode_text)
    draw.text((right_zone_center - sn_w/2, barcode_text_y), sn_code, font=side_font_barcode_text, fill=(0,0,0))
    
    # --- 区域 3: 底部 MADE IN CHINA (在当前局部表格内绝对居中) ---
    made_text = sku_config.side_text['origin_text']
    made_w = draw.textlength(made_text, font=side_font_bold)
    draw.text(( tw * 0.51 , th * 0.87 ), made_text, font=side_font_bold, fill=(0,0,0))
    
    return icon_side_text_box_resized

def generate_barcode_image(code_str, width, height):
    """生成透明背景的条形码图片，并强制缩放到指定尺寸"""
    Code128 = barcode.get_barcode_class("code128")
    bar = Code128(code_str, writer=ImageWriter())
    # 渲染成 PIL Image (不显示文字，透明背景)
    options = {"write_text": False, "module_height": 15.0, "quiet_zone": 1.0}
    img = bar.render(writer_options=options)
    
    # 将白色背景转换为透明
    img = img.convert("RGBA")
    datas = img.getdata()
    new_data = []
    for item in datas:
        # 将白色（255, 255, 255）转换为透明
        if item[0] > 250 and item[1] > 250 and item[2] > 250:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    
    return img.resize((width, height), Image.LANCZOS)

def generate_barcode_with_text(code_str, width, height):
    """
    生成带文字的透明背景条形码，根据目标尺寸动态调整参数避免变形
    这个函数不推荐使用，自带的文本字体非常古早
    建议使用 generate_barcode_image 生成纯条码后手动绘制文字
    """
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image

    Code128 = barcode.get_barcode_class("code128")
    bar = Code128(code_str, writer=ImageWriter())
    
    # 根据目标尺寸动态计算参数
    # 字体大小约为高度的14%
    font_size = max(12, int(height * 0.14))
    # 条码高度大幅减小到35%（为文字留出充足空间）
    module_height = max(6.0, height * 0.35 / 10)  # module_height单位是mm
    # 文字和条码之间的距离大幅增加到15%
    text_distance = max(5.0, height * 0.15 / 10)
    
    options = {
        "write_text": True,           # 开启底部文字
        "font_size": font_size,       # 动态字体大小
        "text_distance": text_distance, # 动态文字距离（增大）
        "module_height": module_height, # 动态条码高度（减小）
        "quiet_zone": 2.0,            # 左右留白宽度
        "background": 'white',        # 显式指定背景白
        "foreground": 'black'         # 显式指定前景色黑
    }
    
    # 渲染原始图片
    img = bar.render(writer_options=options)
    
    # 转换为透明背景
    img = img.convert("RGBA")
    datas = img.getdata()
    new_data = []
    
    for item in datas:
        # 将白色背景转为透明
        if item[0] > 220 and item[1] > 220 and item[2] > 220:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    # 使用高质量缩放，保持长宽比
    return img.resize((width, height), Image.LANCZOS)


def get_max_font_size(text, font_path, target_width, max_height=None, min_size=10, max_size=1000):
    """
    动态寻找能让文字适应目标宽度的最大字号
    
    参数:
        text: 要绘制的文字
        font_path: 字体文件路径
        target_width: 目标宽度（像素）
        max_height: 最大高度限制（像素），可选
        min_size: 最小字号
        max_size: 最大字号
    
    返回:
        适合的字号大小
    """
    # 创建临时绘图对象用于测量
    temp_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(temp_img)
    
    # 二分查找最佳字号
    best_size = min_size
    low, high = min_size, max_size
    
    while low <= high:
        mid = (low + high) // 2
        font = ImageFont.truetype(font_path, mid)
        
        # 获取文字的边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 检查宽度是否符合
        width_ok = text_width <= target_width
        # 检查高度是否符合（如果有高度限制）
        height_ok = max_height is None or text_height <= max_height
        
        if width_ok and height_ok:
            best_size = mid
            low = mid + 1  # 尝试更大的字号
        else:
            high = mid - 1  # 字号太大，减小
    
    return best_size
    
def fill_left_and_right_label_barberpub_topandbottom(sku_config, img_label_resized, fonts_paths):
    """
    填充 Barberpub 天地盖样式左右侧面板的标签区域
    
    功能：只填充顶部的两个条形码（SKU + SN码），底部4个运输标识图片自带
    使用 generate_barcode_image 生成纯条形码，然后手动绘制文字
    """
    tw, th = img_label_resized.size
    draw = ImageDraw.Draw(img_label_resized)
    
    # 加载字体
    font_path = fonts_paths['CentSchbook BT']
    
    # ========== 顶部条形码区域（约35%高度）==========
    barcode_zone_h = int(th * 0.35)
    
    # 纯条形码高度（不含文字）：占条形码区域的89%（增大）
    barcode_only_h = int(barcode_zone_h * 0.89)
    # 条形码顶部间距：10% 
    barcode_y = int(barcode_zone_h * 0.10)
    
    # 文字高度：占条形码区域的22%（增大）
    text_font_size = int(barcode_zone_h * 0.22)
    text_font = ImageFont.truetype(font_path, text_font_size)
    # 文字位置：条形码下方，留出2%的小间距，让文字更靠近底部
    text_y = barcode_y + barcode_only_h + int(barcode_zone_h * 0.01)
    
    # ========== 左侧 SKU 条形码（占宽度的52%，比SN更宽）==========
    sku_name = sku_config.sku_name
    sku_barcode_w = int(tw * 0.52)
    sku_barcode_x = int(tw * 0.01)  # 左边距1%
    
    # 生成纯条形码（不带文字）
    sku_barcode_img = generate_barcode_image(sku_name, width=sku_barcode_w, height=barcode_only_h)
    img_label_resized.paste(sku_barcode_img, (sku_barcode_x, barcode_y), mask=sku_barcode_img)
    
    # 在条形码下方居中绘制文字
    sku_text_w = draw.textlength(sku_name, font=text_font)
    sku_text_x = sku_barcode_x + (sku_barcode_w - sku_text_w) // 2
    draw.text((sku_text_x, text_y), sku_name, font=text_font, fill=(0, 0, 0))
    
    # ========== 右侧 SN 条形码（占宽度的42%）==========
    sn_code = sku_config.side_text['sn_code']
    sn_barcode_w = int(tw * 0.42)
    sn_barcode_x = int(tw * 0.56)  # 从56%位置开始（留4%间距）
    
    # 生成纯条形码（不带文字）
    sn_barcode_img = generate_barcode_image(sn_code, width=sn_barcode_w, height=barcode_only_h)
    img_label_resized.paste(sn_barcode_img, (sn_barcode_x, barcode_y), mask=sn_barcode_img)
    
    # 在条形码下方居中绘制文字
    sn_text_w = draw.textlength(sn_code, font=text_font)
    sn_text_x = sn_barcode_x + (sn_barcode_w - sn_text_w) // 2
    draw.text((sn_text_x, text_y), sn_code, font=text_font, fill=(0, 0, 0))
    
    return img_label_resized

def draw_diagonal_stripes(canvas, stripe_height_cm, dpi, bottom_margin_cm=0, stripe_width_px=30, stripe_color=(0, 0, 0), bg_color=(255, 255, 255)):
    """
    在画布底部绘制黑白斜纹条块（通用函数）
    
    参数：
        canvas: PIL Image对象
        stripe_height_cm: 条纹区域的高度（厘米）
        dpi: 分辨率
        bottom_margin_cm: 底部留白高度（厘米），默认0
        stripe_width_px: 每条斜纹的宽度（像素），默认30
        stripe_color: 斜纹颜色，默认黑色
        bg_color: 背景颜色，默认白色
    
    返回：
        修改后的canvas
    """
    canvas_w, canvas_h = canvas.size
    draw = ImageDraw.Draw(canvas)
    
    # 计算条纹区域高度（像素）
    stripe_h_px = int(stripe_height_cm * dpi)
    bottom_margin_px = int(bottom_margin_cm * dpi)
    stripe_y_start = canvas_h - stripe_h_px - bottom_margin_px
    stripe_y_end = canvas_h - bottom_margin_px
    
    # 先绘制背景色
    draw.rectangle([0, stripe_y_start, canvas_w, stripe_y_end], fill=bg_color)
    
    # 绘制斜纹：从左到右，每个斜纹从左下到右上
    # 斜纹角度约45度
    stripe_offset = int(stripe_width_px * 1.5)  # 每条斜纹的间距（一黑一白）
    
    # 计算需要多少条斜纹（覆盖整个宽度+高度对角线）
    num_stripes = (canvas_w + stripe_h_px) // stripe_offset + 2
    
    for i in range(num_stripes):
        # 计算斜纹起始x坐标
        start_x = i * stripe_offset - stripe_h_px
        
        # 绘制斜纹：一个平行四边形
        # 左下、右下、右上、左上四个点
        points = [
            (start_x, stripe_y_end),                           # 左下
            (start_x + stripe_width_px, stripe_y_end),         # 右下
            (start_x + stripe_width_px + stripe_h_px, stripe_y_start),  # 右上
            (start_x + stripe_h_px, stripe_y_start)        # 左上
        ]
        draw.polygon(points, fill=stripe_color)
    
    return canvas

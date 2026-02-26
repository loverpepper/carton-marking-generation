# -*- coding: utf-8 -*-
"""
新版核心生成引擎 - 使用样式注册系统
"""
from PIL import Image, ImageDraw
import pathlib as Path
from style_base import StyleRegistry

# 导入所有样式模块以自动注册
import style_mcombo_standard
import style_barberpub_topandbottom
import style_barberpub_doubleopening
import style_barberpub_fulloverlap
import style_exacme_fulloverlap
import style_exacme_doubleopening
# 未来在这里导入更多样式:
# import style_simple
# import style_premium
# import style_custom_a
# etc.
#测试一下


class SKUConfig:
    """SKU 配置类 - 保持不变"""
    
    def __init__(self, sku_name, length_cm, width_cm, height_cm, 
                 style_name="mcombo_standard", 
                 bottom_gb_h_cm=10, ppi=300, **style_params):
        """
        Args:
            sku_name: SKU 名称
            length_cm, width_cm, height_cm: 箱子尺寸（厘米）
            style_name: 样式名称，默认 "exacme_fulloverlap"
            bottom_gb_h_cm: 底部黑色底框高度（厘米）
            ppi: 分辨率
            **style_params: 样式特定参数，如 color, product, size, side_text, box_number, sponge_verified 等
        """
        self.sku_name = sku_name
        self.l_cm = length_cm
        self.w_cm = width_cm
        self.h_cm = height_cm
        self.l_in = length_cm / 2.54
        self.w_in = width_cm / 2.54
        self.h_in = height_cm / 2.54
        self.bottom_gb_h = bottom_gb_h_cm
        self.style_name = style_name
        self.dpi = ppi / 2.54
        self.ppi = ppi
        self.color_mode = 'RGB'  # 默认颜色模式
        self.background_color = (161, 142, 102)  # 默认RGB背景色
        # self.background_color = (0, 12, 37, 37)  # 默认CMYK背景色，颜色设置还有问题
        
        # 预计算像素值
        self.l_px = int(length_cm * self.dpi)
        self.w_px = int(width_cm * self.dpi)
        self.h_px = int(height_cm * self.dpi)
        self.half_w_px = int(self.w_px / 2)
        self.bottom_gb_h_px = int(self.bottom_gb_h * self.dpi)
        
        # 存储样式特定参数
        for key, value in style_params.items():
            setattr(self, key, value)


class BoxMarkGenerator:
    """箱唛生成器 - 使用样式系统"""
    
    def __init__(self, base_dir, style_name="mcombo_standard", ppi=300):
        """
        Args:
            base_dir: 资源基础目录
            style_name: 使用的样式名称
            ppi: 分辨率
        """
        self.base_dir = base_dir
        self.style_name = style_name
        self.ppi = ppi
        self.style = StyleRegistry.get_style(style_name, base_dir, ppi)
    
    def generate_complete_layout(self, sku_config):
        """生成完整的箱唛布局 - 动态适配不同样式的布局"""
        # 1. 从样式获取布局配置
        layout = self.style.get_layout_config(sku_config)
        panels_mapping = self.style.get_panels_mapping(sku_config)
        
        # 2. 计算画布总尺寸（根据布局的最大范围）
        max_x = max(x + w for x, y, w, h in layout.values())
        max_y = max(y + h for x, y, w, h in layout.values())
        
        # 创建画布（白色背景，未填充的区域将显示为白色）
   
        canvas = Image.new(sku_config.color_mode, (int(max_x), int(max_y)), (255, 255, 255)) # RGB白色背景
        # canvas = Image.new('CMYK', (int(max_x), int(max_y)), (0,0,0,0))  # CMYK透明背景（未填充区域为白色）
        # 3. 让样式生成它需要的所有面板（动态适配不同样式）
        panels_dict = self.style.generate_all_panels(sku_config)
        
        # 4. 根据映射关系动态粘贴面板
        for region_name, panel_type in panels_mapping.items():
            if region_name in layout and panel_type in panels_dict:
                x, y, w, h = layout[region_name]
                panel = panels_dict[panel_type]
                canvas.paste(panel, (int(x), int(y)))
        
        # 6. 画出所有格子的边框（用于调试和验证）
        draw = ImageDraw.Draw(canvas)
        for name, (x, y, w, h) in layout.items():
            shape = [x, y, x + w, y + h]
            draw.rectangle(shape, outline=(0,0,0), width=3)
        
        return canvas
    
    def save_as_pdf(self, canvas, output_path, sku_config):
        """保存为 PDF 格式（与旧版保持一致：先转CMYK再转回RGB）"""
        canvas.show()
        
        # 由RGB转CMYK以便印刷（用于颜色校准）
        # canvas_cmyk = canvas.convert('CMYK')
        # PDF需要RGB模式
        # canvas_rgb = canvas_cmyk.convert('RGB')
        canvas.save(output_path, "PDF", resolution=sku_config.ppi, quality=100)
        # canvas_rgb.save(output_path, "PDF", resolution=sku_config.ppi, quality=100)
        
        
        
        total_width, total_height = canvas.size
        print(f"✅ 箱唛已生成为PDF！文件: {output_path}")
        print(f"   样式: {self.style_name}")
        print(f"   尺寸: {total_width}x{total_height}px ({total_width/sku_config.dpi:.1f}cm x {total_height/sku_config.dpi:.1f}cm)")
        print(f"   分辨率: {sku_config.ppi} PPI")
    
    @staticmethod
    def list_available_styles():
        """列出所有可用的样式"""
        return StyleRegistry.get_all_styles()


def visualize_layout(sku_config, generator):
    """可视化布局（兼容旧接口）"""
    canvas = generator.generate_complete_layout(sku_config)
    output_filename = f"{sku_config.sku_name}_carton_marking.pdf"
    generator.save_as_pdf(canvas, output_filename, sku_config)


# --- 测试运行 ---
if __name__ == "__main__":
    # 使用新框架生成箱唛
    sku_text = {
        'gw_value': 30.9, #LBS 毛重
        'nw_value': 24.7, #LBS 净重
        'sn_code': '09429381135347',
        'origin_text':'MADE IN CHINA',
    }

    box_number = {
        'total_boxes': 3,
        'current_box': 2
    }
    
    # 创建 SKU 配置（使用新方式）
    test_sku = SKUConfig(
        sku_name="6180-CP12G",
        length_cm=97.5,
        width_cm=39.5,
        height_cm=18.0,
        style_name="exacme_doubleopening",  # 指定样式
        ppi=150,

        color='Seafoam Green',
        product='TRAMPOLINE PAD',
        product_fullname = 'TRAMPOLINE\nPREMIUM SPRING COVER',
        size='(Medium-Wide)', # 可选参数，MCombo 标准样式的特定参数
        side_text=sku_text,
        box_number=box_number,
        sponge_verified=True # 是否通过海绵测试, 可选参数, 有些样式会用到
    )
    
    # 创建生成器
    base_dir = Path.Path(__file__).parent
    generator = BoxMarkGenerator(base_dir=base_dir, style_name="exacme_doubleopening", ppi=150)
    
    # 生成箱唛
    visualize_layout(test_sku, generator)
    
    # 列出所有可用样式
    print("\n📋 所有可用样式:")
    for style_info in BoxMarkGenerator.list_available_styles():
        print(f"  - {style_info['name']}: {style_info['description']}")
        print(f"    必需参数: {', '.join(style_info['required_params'])}")

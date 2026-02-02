# -*- coding: utf-8 -*-
import streamlit as st
from PIL import Image, ImageDraw
import pathlib as Path
import io
import tempfile
from generation_core import SKUConfig, BoxMarkEngine, visualize_layout

# 设置页面配置
st.set_page_config(
    page_title="箱唛生成器",
    page_icon="📦",
    layout="wide"
)

# 初始化 session state
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None

# 页面标题
st.title("📦 MCombo 箱唛生成器")

# 添加示例预览图
try:
    preview_image_path = Path.Path(__file__).parent /  'layout_validation.jpg'
    if preview_image_path.exists():
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            preview_img = Image.open(preview_image_path)
            st.image(preview_img, caption="箱唛示例预览", width="stretch")
except:
    pass

st.markdown("---")

# 创建两列布局
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 基本信息")
    
    # SKU 名称
    sku_name = st.text_input("SKU 名称", value="CA-6160-OE678BR-1", help="例如: CA-6160-OE678BR-1")
    
    # 尺寸信息
    st.subheader("箱子尺寸 (cm)")
    col_l, col_w, col_h = st.columns(3)
    with col_l:
        length_cm = st.number_input("长度", min_value=1.0, value=77.0, step=0.5)
    with col_w:
        width_cm = st.number_input("宽度", min_value=1.0, value=67.5, step=0.5)
    with col_h:
        height_cm = st.number_input("高度", min_value=1.0, value=47.0, step=0.5)
    
    # 产品信息
    st.subheader("产品信息")
    color = st.text_input("颜色", value="Beige", help="例如: Beige, Brown")
    product = st.text_input("产品名称", value="Lift Recliner", help="例如: Lift Recliner")
    size = st.text_input("尺寸标注", value="(Oversize)", help="例如: (Oversize), (Standard)")
    
    # 箱号信息
    st.subheader("箱号信息")
    col_total, col_current = st.columns(2)
    with col_total:
        total_boxes = st.number_input("总箱数", min_value=1, value=3, step=1)
    with col_current:
        current_box = st.number_input("当前箱号", min_value=1, value=1, step=1)
    
    # 海绵认证
    sponge_verified = st.selectbox("海绵认证", options=["否", "是"], index=1) == "是"
    
    # PPI 设置
    ppi = st.selectbox("分辨率 (PPI)", options=[72, 150, 300], index=1, help="150适合屏幕预览，300适合印刷")

with col2:
    st.header("📋 侧唛信息")
    st.info("💡 **侧唛元素高度**：文字信息框 8cm | 标签框 5cm | Logo 5cm  都固定不变")
    
    # 重量信息
    st.subheader("重量信息")
    col_gw, col_nw = st.columns(2)
    with col_gw:
        gross_weight = st.number_input("毛重 (lbs)", min_value=0.0, value=106.9, step=0.1)
    with col_nw:
        net_weight = st.number_input("净重 (lbs)", min_value=0.0, value=94.4, step=0.1)
    
    # 箱子尺寸（英寸）
    st.subheader("箱子尺寸标注 (英寸)")
    col_l_in, col_w_in, col_h_in = st.columns(3)
    with col_l_in:
        length_in = st.number_input("长 (in)", min_value=0.0, value=30.3, step=0.1)
    with col_w_in:
        width_in = st.number_input("宽 (in)", min_value=0.0, value=26.6, step=0.1)
    with col_h_in:
        height_in = st.number_input("高 (in)", min_value=0.0, value=18.5, step=0.1)
    
    # SN 码
    sn_code = st.text_input("SN 码", value="08429381073953", help="条形码序列号")

# 生成按钮区域
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    generate_preview = st.button("🖼️ 生成预览", type="primary")

with col_btn2:
    # 确保文件名有效，防止为空
    current_sku = sku_name.strip() if sku_name and sku_name.strip() else "carton_marking"
    
    if st.session_state.pdf_bytes:
        st.download_button(
            label="📥 下载 PDF",
            data=st.session_state.pdf_bytes,
            file_name=f"{current_sku}.pdf",
            mime="application/pdf"
        )
    else:
        st.button("📥 下载 PDF (请先生成预览)", disabled=True)

# 生成逻辑
if generate_preview:
    with st.spinner("正在生成箱唛..."):
        try:
            # 准备侧唛文本信息
            sku_text = {
                'gw_value': gross_weight,
                'nw_value': net_weight,
                'dimention_text': f'BOX SIZE: {length_in}\'\' x {width_in}\'\' x {height_in}\'\'',
                'sn_code': sn_code
            }
            
            # 准备箱号信息
            box_number = {
                'total_boxes': int(total_boxes),
                'current_box': int(current_box)
            }
            
            # 创建 SKUConfig
            test_sku = SKUConfig(
                sku_name=sku_name,
                length_cm=length_cm,
                width_cm=width_cm,
                height_cm=height_cm,
                color=color,
                product=product,
                size=size,
                side_text=sku_text,
                box_number=box_number,
                sponge_verified=sponge_verified,
                ppi=ppi
            )
            
            # 创建 BoxMarkEngine
            base_dir = Path.Path(__file__).parent
            boxengine = BoxMarkEngine(base_dir=base_dir, ppi=ppi)
            
            # 生成布局
            layout = test_sku.get_layout_config()
            total_width = (test_sku.l_px * 2) + (test_sku.w_px * 2)
            total_height = test_sku.h_px + test_sku.w_px
            
            # 创建画布
            canvas = Image.new('RGB', (total_width, total_height), (161, 142, 102))
            
            # 生成各个面板
            canvas_left_up, canvas_left_down = boxengine.generate_left_panel(test_sku)
            canvas_right_up, canvas_right_down = boxengine.generate_right_panel(test_sku)
            canvas_front = boxengine.generate_front_panel(test_sku)
            canvas_side = boxengine.generate_side_panel(test_sku)
            
            # 粘贴面板
            canvas.paste(canvas_left_up, (int(layout["flap_top_front1"][0]), int(layout["flap_top_front1"][1])))
            canvas.paste(canvas_right_up, (int(layout["flap_top_front2"][0]), int(layout["flap_top_front2"][1])))
            canvas.paste(canvas_front, (int(layout["panel_front1"][0]), int(layout["panel_front1"][1])))
            canvas.paste(canvas_side, (int(layout["panel_side1"][0]), int(layout["panel_side1"][1])))
            canvas.paste(canvas_front, (int(layout["panel_front2"][0]), int(layout["panel_front2"][1])))
            canvas.paste(canvas_side, (int(layout["panel_side2"][0]), int(layout["panel_side2"][1])))
            canvas.paste(canvas_left_down, (int(layout["flap_btm_front1"][0]), int(layout["flap_btm_front1"][1])))
            canvas.paste(canvas_right_down, (int(layout["flap_btm_front2"][0]), int(layout["flap_btm_front2"][1])))
            
            # 画出所有格子的边框（用于调试和验证）
            draw = ImageDraw.Draw(canvas)
            for name, (x, y, w, h) in layout.items():
                shape = [x, y, x + w, y + h]
                draw.rectangle(shape, outline=(0, 0, 0), width=3)
            
            # 转换为 RGB 用于显示和保存
            canvas_rgb = canvas.convert('RGB')
            
            # 生成 PDF 到内存（高分辨率）
            pdf_buffer = io.BytesIO()
            canvas_rgb.save(pdf_buffer, "PDF", resolution=ppi, quality=100)
            st.session_state.pdf_bytes = pdf_buffer.getvalue()
            
            # 创建缩略图用于网页预览（最大宽度 2000px，避免 PIL 限制）
            max_preview_width = 2000
            if canvas_rgb.width > max_preview_width:
                preview_ratio = max_preview_width / canvas_rgb.width
                preview_size = (max_preview_width, int(canvas_rgb.height * preview_ratio))
                preview_image = canvas_rgb.resize(preview_size, Image.Resampling.LANCZOS)
            else:
                preview_image = canvas_rgb
            
            # 保存预览图到内存
            st.session_state.generated_image = preview_image
            
            st.success("✅ 箱唛生成成功！")
            st.info(f"📐 PDF尺寸: {total_width}x{total_height}px ({total_width/test_sku.dpi:.1f}cm x {total_height/test_sku.dpi:.1f}cm) | 🎨 分辨率: {ppi} PPI | 预览图已自动缩放")
            
        except Exception as e:
            st.error(f"❌ 生成失败: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# 显示预览（始终显示，只要有生成的图片）
if st.session_state.generated_image:
    st.markdown("---")
    st.header("🖼️ 预览")
    st.image(st.session_state.generated_image, width='stretch')
    
    # 显示提示信息
    if st.session_state.pdf_bytes:
        st.info("💡 提示：预览图已生成，点击上方'下载 PDF'按钮保存文件")

# 页面底部说明
st.markdown("---")
st.markdown("""
### 💡 使用说明
1. 在左侧填写箱唛基本信息（尺寸、颜色、产品名称等）
2. 在右侧填写侧唛信息（重量、箱子尺寸标注、SN码等）
3. 可选：上传自定义的顶部右侧图片
4. 点击"生成预览"按钮查看效果
5. 点击"下载 PDF"按钮保存文件

### 🌐 局域网访问
其他设备访问此页面的方法：
连接公司WIFI【tomorrow】后，打开设备浏览器访问: `http://192.168.1.54:8501`
"""
)
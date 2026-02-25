# -*- coding: utf-8 -*-
"""
Streamlit 应用 - 新版，支持多样式选择
"""
import streamlit as st
from PIL import Image, ImageDraw
import pathlib as Path
import io

# 导入新版生成核心
from generation_core_v3 import SKUConfig, BoxMarkGenerator

# 导入所有样式以自动注册
import style_mcombo_standard
import style_simple
# 未来添加更多样式时在这里导入

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
st.title("📦 MCombo 箱唛生成器 V2")
st.caption("🎨 支持多样式切换的新版箱唛生成系统")

# 添加示例预览图
try:
    preview_image_path = Path.Path(__file__).parent / 'layout_validation.jpg'
    if preview_image_path.exists():
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            preview_img = Image.open(preview_image_path)
            st.image(preview_img, caption="箱唛示例预览", width="stretch")
except:
    pass

st.markdown("---")

# 获取所有可用样式
available_styles = BoxMarkGenerator.list_available_styles()
style_names = [s['name'] for s in available_styles]
style_descriptions = {s['name']: s['description'] for s in available_styles}

# 样式选择器（放在最上方）
st.header("🎨 样式选择")
selected_style = st.selectbox(
    "选择箱唛样式",
    options=style_names,
    format_func=lambda x: f"{x} - {style_descriptions[x]}",
    index=0
)

st.info(f"当前样式: **{selected_style}** - {style_descriptions[selected_style]}")

# 获取当前样式所需的参数
current_style_info = next((s for s in available_styles if s['name'] == selected_style), None)
required_params = current_style_info['required_params'] if current_style_info else []

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
    
    # PPI 设置
    ppi = st.selectbox("分辨率 (PPI)", options=[72, 150, 300], index=1, help="150适合屏幕预览，300适合印刷")

with col2:
    st.header("📋 样式特定参数")
    
    # 根据选择的样式显示不同的参数输入框
    style_params = {}
    
    # 通用参数（大多数样式都需要）
    if 'product' in required_params:
        product = st.text_input("产品名称", value="Lift Recliner", help="例如: Lift Recliner")
        style_params['product'] = product
    
    if 'box_number' in required_params:
        st.subheader("箱号信息")
        col_total, col_current = st.columns(2)
        with col_total:
            total_boxes = st.number_input("总箱数", min_value=1, value=3, step=1)
        with col_current:
            current_box = st.number_input("当前箱号", min_value=1, value=1, step=1)
        style_params['box_number'] = {
            'total_boxes': int(total_boxes),
            'current_box': int(current_box)
        }
    
    # MCombo 标准样式的额外参数
    if selected_style == "mcombo_standard":
        st.subheader("MCombo 标准样式参数")
        
        color = st.text_input("颜色", value="Beige", help="例如: Beige, Brown")
        size = st.text_input("尺寸标注", value="(Oversize)", help="例如: (Oversize), (Standard)")
        
        st.subheader("重量信息")
        col_gw, col_nw = st.columns(2)
        with col_gw:
            gross_weight = st.number_input("毛重 (lbs)", min_value=0.0, value=106.9, step=0.1)
        with col_nw:
            net_weight = st.number_input("净重 (lbs)", min_value=0.0, value=94.4, step=0.1)
        
        st.subheader("箱子尺寸标注 (英寸)")
        col_l_in, col_w_in, col_h_in = st.columns(3)
        with col_l_in:
            length_in = st.number_input("长 (in)", min_value=0.0, value=30.3, step=0.1)
        with col_w_in:
            width_in = st.number_input("宽 (in)", min_value=0.0, value=26.6, step=0.1)
        with col_h_in:
            height_in = st.number_input("高 (in)", min_value=0.0, value=18.5, step=0.1)
        
        sn_code = st.text_input("SN 码", value="08429381073953", help="条形码序列号")
        sponge_verified = st.selectbox("海绵认证", options=["否", "是"], index=1) == "是"
        
        style_params.update({
            'color': color,
            'size': size,
            'side_text': {
                'gw_value': gross_weight,
                'nw_value': net_weight,
                'dimention_text': f'BOX SIZE: {length_in}\'\' x {width_in}\'\' x {height_in}\'\'',
                'sn_code': sn_code
            },
            'sponge_verified': sponge_verified
        })

# 生成按钮区域
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    generate_preview = st.button("🖼️ 生成预览", type="primary")

with col_btn2:
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
    with st.spinner(f"正在使用 {selected_style} 样式生成箱唛..."):
        try:
            # 创建 SKU 配置
            test_sku = SKUConfig(
                sku_name=sku_name,
                length_cm=length_cm,
                width_cm=width_cm,
                height_cm=height_cm,
                style_name=selected_style,
                ppi=ppi,
                **style_params
            )
            
            # 创建生成器
            base_dir = Path.Path(__file__).parent
            generator = BoxMarkGenerator(base_dir=base_dir, style_name=selected_style, ppi=ppi)
            
            # 生成完整布局
            canvas = generator.generate_complete_layout(test_sku)
            
            # 转换为 RGB 用于显示和保存
            canvas_rgb = canvas.convert('RGB')
            
            # 生成 PDF 到内存（高分辨率）
            pdf_buffer = io.BytesIO()
            canvas_rgb.save(pdf_buffer, "PDF", resolution=ppi, quality=100)
            st.session_state.pdf_bytes = pdf_buffer.getvalue()
            
            # 创建缩略图用于网页预览
            max_preview_width = 2000
            if canvas_rgb.width > max_preview_width:
                preview_ratio = max_preview_width / canvas_rgb.width
                preview_size = (max_preview_width, int(canvas_rgb.height * preview_ratio))
                preview_image = canvas_rgb.resize(preview_size, Image.Resampling.LANCZOS)
            else:
                preview_image = canvas_rgb
            
            # 保存预览图到内存
            st.session_state.generated_image = preview_image
            
            total_width, total_height = canvas.size
            st.success(f"✅ 箱唛生成成功！（样式: {selected_style}）")
            st.info(f"📐 PDF尺寸: {total_width}x{total_height}px ({total_width/test_sku.dpi:.1f}cm x {total_height/test_sku.dpi:.1f}cm) | 🎨 分辨率: {ppi} PPI | 预览图已自动缩放")
            
        except Exception as e:
            st.error(f"❌ 生成失败: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# 显示预览
if st.session_state.generated_image:
    st.markdown("---")
    st.header("🖼️ 预览")
    st.image(st.session_state.generated_image, use_container_width=True)
    
    if st.session_state.pdf_bytes:
        st.info("💡 提示：预览图已生成，点击上方'下载 PDF'按钮保存文件")

# 页面底部说明
st.markdown("---")
st.markdown(f"""
### 💡 使用说明
1. **选择样式**：在顶部选择要使用的箱唛样式
2. **填写基本信息**：在左侧填写箱唛基本信息（尺寸、SKU名称等）
3. **填写样式参数**：在右侧填写当前样式所需的特定参数
4. **生成预览**：点击"生成预览"按钮查看效果
5. **下载 PDF**：点击"下载 PDF"按钮保存文件

### 🎨 当前可用样式
""")

for style_info in available_styles:
    st.markdown(f"- **{style_info['name']}**: {style_info['description']}")
    if style_info['required_params']:
        st.markdown(f"  - 必需参数: `{', '.join(style_info['required_params'])}`")

st.markdown("""
### 🌐 局域网访问
其他设备访问此页面的方法：
连接公司WIFI【tomorrow】后，打开设备浏览器访问: `http://192.168.1.54:8501`
"""
)

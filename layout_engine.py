from PIL import Image as PILImage, ImageDraw, ImageFont
from abc import ABC, abstractmethod
class Element(ABC):
    def __init__(self, width, height, nudge_x=0, nudge_y=0, padding = 0, padding_x=None, padding_y=None):
        self.width = width
        self.height = height
        self.padding_x = padding if padding_x is None else padding_x
        self.padding_y = padding if padding_y is None else padding_y
        self.nudge_x = nudge_x
        self.nudge_y = nudge_y
        self.x = 0
        self.y = 0
        
    @abstractmethod
    def layout(self, x, y, max_width=0):
        """
        核心方法1：计算位置
        父容器会告诉子元素："你的起点是 (x, y)"
        子元素记录下这个位置。
        """
        self.x = x + self.padding_x + self.nudge_x
        self.y = y + self.padding_y + self.nudge_y
        return self.width + 2 * self.padding_x, self.height + 2 * self.padding_y
    
    @abstractmethod
    def render(self, draw: ImageDraw.ImageDraw):
        """
        核心方法2：绘制
        拿着计算好的 self.x 和 self.y，把自己画在画布上。
        """
        pass


# 占位组件（隐形砖块，用于撑开间距或缩进对齐）
class Spacer(Element):
    def __init__(self, width=0, height=0):
        super().__init__(width=width, height=height)

    def layout(self, x, y, max_width=0):
        return super().layout(x, y, max_width)

    def render(self, draw: ImageDraw.ImageDraw):
        pass  # 不画任何东西


# 文本组件
class Text(Element):
    def __init__(self, text, font, color = (0, 0, 0), draw_background=False, background_color=(0, 0, 0), border_radius = 16, **kwargs):
        left, top, right, bottom = font.getbbox(text)
        width = right - left
        height = bottom - top
        
        self.offset_y = -top  # 记录字体的垂直偏移量
        
        super().__init__( width=width, height=height, **kwargs )
        
        self.text = text
        self.font = font
        self.color = color
        # 文本背景的两个参数
        self.draw_background = draw_background
        self.background_color = background_color
        self.border_radius = border_radius
        
    def layout(self, x, y, max_width=0):
        return super().layout(x, y, max_width)
    
    def render(self, draw: ImageDraw.ImageDraw):
        if self.draw_background:
            # 画文本背景：在文本周围画一个矩形框，框的大小和文本一样
            bg_left = self.x - self.padding_x
            bg_top = self.y - self.padding_y
            bg_right = self.x + self.width + self.padding_x
            bg_bottom = self.y + self.height + self.padding_y
            draw.rounded_rectangle([bg_left, bg_top, bg_right, bg_bottom], radius=self.border_radius,
                fill=self.background_color)
        draw.text((self.x, self.y + self.offset_y), self.text, font=self.font, fill=self.color)
        

# 图片组件
class Image(Element):
    def __init__(self, image: PILImage.Image, width=None, height=None, **kwargs):
        
        # 魔法升级：自动计算等比例缩放！
        if width is not None and height is None:
            # 只传了宽，自动算高
            height = int(width * image.height / image.width)
        elif height is not None and width is None:
            # 只传了高，自动算宽
            width = int(height * image.width / image.height)
            
        # 如果宽高都有了，就执行缩放
        if width is not None and height is not None:
            self.image = image.resize((int(width), int(height)), PILImage.Resampling.LANCZOS)
        else:
            self.image = image
            
        # 剩下的全丢给老祖宗
        super().__init__(width=self.image.width, height=self.image.height, **kwargs)

    def layout(self, x, y, max_width=0):
        return super().layout(x, y, max_width)
    
    def render(self, draw: ImageDraw.ImageDraw):
        canvas = draw._image
        
        # 粘贴图片，如果带透明通道(RGBA)需要使用 mask，保证透明背景正常
        if self.image.mode == 'RGBA':
            canvas.paste(self.image, (int(self.x), int(self.y)), mask=self.image)
        else:
            canvas.paste(self.image, (int(self.x), int(self.y)))
            

class Column(Element):
    """垂直堆叠容器 (VStack) 🥞"""
    def __init__(self, children, spacing=0, align='center', padding=0, padding_x=None, padding_y=None,
                 justify='start',   # 新增：垂直分布方式，默认靠上(start)
                 fixed_height=None, # 新增：是否锁死高度
                 fixed_width=None,  # 新增：是否锁死宽度，如果锁死宽度则不根据孩子自动调整宽度，而是使用这个固定宽度
                 **kwargs):
        
        padding_x = padding if padding_x is None else padding_x
        padding_y = padding if padding_y is None else padding_y
        
        # 1. 先算出如果不锁死高度，原来需要多高 (动态高度)
        total_children_height = sum([child.height for child in children]) 
        total_spacing = spacing * (len(children) - 1) if len(children) > 1 else 0
        dynamic_height = total_children_height + total_spacing + 2 * padding_y
        
        # 2. 高度的完美二选一逻辑
        if fixed_height is not None:
            height = fixed_height
        else:
            height = dynamic_height

        # 3. 宽度逻辑保持不变 (依然由最宽的孩子决定)
        if fixed_width is not None:
            width = fixed_width
        else:
            width = max([child.width for child in children]) if children else 0
            width += 2 * padding_x
        
        super().__init__(width=width, height=height, padding=padding, padding_x=padding_x, padding_y=padding_y)
        
        self.children = children
        self.spacing = spacing
        self.align = align
        self.justify = justify # 保存排版模式

    def layout(self, x, y, max_width=None):
        super().layout(x, y, max_width)
        
        current_y = self.y
        
        # 【核心魔法：动态计算垂直间距】
        actual_spacing = self.spacing # 默认使用传入的固定 spacing
        
        if self.justify == 'space-between' and len(self.children) > 1:
            # 剩余的动态空白 = 容器内壁总高 - 所有孩子的纯高度
            total_children_height = sum([child.height for child in self.children])
            remaining_space = self.height - 2 * self.padding_y - total_children_height
            # 把空白平均分给孩子们中间的空隙
            actual_spacing = remaining_space / (len(self.children) - 1)
        
        for child in self.children:
            # --- 处理水平对齐 (居中、靠左、靠右) ---
            offset_x = 0
            if self.align == 'center':
                offset_x = (self.width - 2 * self.padding_x - child.width) // 2
            elif self.align == 'right':
                offset_x = self.width - 2 * self.padding_x - child.width
            elif self.align == 'left':
                offset_x = 0
            
            child_x = self.x + offset_x
            
            # 3. 告诉孩子它的确切坐标
            child.layout(child_x, current_y)
            
            # 4. 光标往下移：加上当前孩子的高度，以及刚才算出来的“动态垂直间距”！
            current_y += child.height + actual_spacing

    def render(self, draw: ImageDraw.ImageDraw):
        for child in self.children:
            child.render(draw)


class Row(Element):
    """水平堆叠容器 (HStack) 🥞"""
    def __init__(self, children, spacing=0, align='center', padding=0, padding_x=None, padding_y=None,
                 justify='start', # 新增：排列方式，默认靠左(start)，可选 'space-between'
                 fixed_width=None, # 新增：是否锁死宽度，如果锁死宽度则不根据孩子自动调整宽度，而是使用这个固定宽度
                 fixed_height=None, # 新增：是否锁死高度
                 ):
        
        padding_x = padding if padding_x is None else padding_x
        padding_y = padding if padding_y is None else padding_y
        
        # 1. 容器需要先知道自己有多大
        # 容器的高度：由肚子里最高的那个孩子决定（动态高度）
        dynamic_height = max([child.height for child in children]) if children else 0
        dynamic_height += 2 * padding_y
        
        if fixed_height is not None:
            height = fixed_height
        else:
            height = dynamic_height
        
        # 容器的宽度：所有孩子的宽度总和 + 它们之间的间距总和
        total_children_width = sum([child.width for child in children])
        total_spacing = spacing * (len(children) - 1) if len(children) > 1 else 0
        dynamic_width = total_children_width + total_spacing + 2 * padding_x
        
        if fixed_width is not None:
            width = fixed_width
        else:
            width = dynamic_width
        
        super().__init__(width=width, height=height, padding=padding, padding_x=padding_x, padding_y=padding_y)
        
        self.children = children
        self.spacing = spacing
        self.align = align
        self.justify = justify

    def layout(self, x, y, max_width=0):
        # 1. 记录容器自己的起始位置
        super().layout(x, y, max_width)
        
        # 2. 这就是你刚才算出来的逻辑！定义一个不断往右走的 current_x
        current_x = self.x
        
        # 【核心魔法：动态计算间距】
        actual_spacing = self.spacing # 默认用传入的固定 spacing
        
        if self.justify == 'space-between' and len(self.children) > 1:
            # 剩余的动态空白 = 容器内壁总宽 - 所有孩子的纯宽度
            total_children_width = sum([child.width for child in self.children])
            remaining_space = self.width - 2 * self.padding_x - total_children_width
            # 把空白平均分给孩子们中间的空隙
            actual_spacing = remaining_space / (len(self.children) - 1)
        
        for child in self.children:
            # --- 处理垂直对齐 (居中、靠上、靠下) ---
            offset_y = 0
            if self.align == 'top':
                offset_y = 0
            elif self.align == 'center':
                # 居中偏移量 = (容器可用高度 - 孩子高度) / 2
                offset_y = (self.height - 2 * self.padding_y - child.height) // 2
            elif self.align == 'bottom':
                offset_y = self.height - 2 * self.padding_y - child.height
            
            child_y = self.y + offset_y
            
            # 3. 告诉孩子它的确切坐标
            child.layout(current_x, child_y)
            
            # 4. 光标往右移：加上当前孩子的宽度和间距
            current_x += child.width + actual_spacing

    def render(self, draw: ImageDraw.ImageDraw):
        # 容器自己不画画，只负责让肚子里的孩子们挨个把自己画出来
        for child in self.children:
            child.render(draw)

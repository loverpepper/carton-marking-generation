from PIL import Image, ImageDraw, ImageFont
from abc import ABC, abstractmethod
class Element(ABC):
    def __init__(self, width, height, padding = 0):
        self.width = width
        self.height = height
        self.padding = padding
        self.x = 0
        self.y = 0
        
    @abstractmethod
    def layout(self, x, y, max_width):
        """
        核心方法1：计算位置
        父容器会告诉子元素："你的起点是 (x, y)"
        子元素记录下这个位置。
        """
        self.x = x + self.padding
        self.y = y + self.padding
        return self.width + 2 * self.padding, self.height + 2 * self.padding
    
    @abstractmethod
    def render(self, draw: ImageDraw.ImageDraw):
        """
        核心方法2：绘制
        拿着计算好的 self.x 和 self.y，把自己画在画布上。
        """
        pass
    

# 文本组件
class Text(Element):
    def __init__(self, text, font, color = (0, 0, 0), padding = 0, **kwargs):
        super().__init__( **kwargs )
        self.text = text
        self.font = font
        self.color = color
        width, height = font.getsize(text)
        
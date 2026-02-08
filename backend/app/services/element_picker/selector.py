"""选择器生成器"""


class SelectorGenerator:
    """生成CSS选择器"""
    
    @staticmethod
    def generate_selector(info: dict) -> str:
        if info.get('selector'):
            return info['selector']
        return info.get('tagName', 'div')

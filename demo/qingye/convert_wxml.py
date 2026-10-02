"""Build a browser view from the repository's trusted WXML/WXSS sources."""
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

TAGS = {'view': 'div', 'text': 'span', 'image': 'img', 'block': 'template', 'scroll-view': 'div', 'picker': 'qy-picker', 'switch': 'input'}
VOID = {'input', 'img', 'br', 'hr'}
IGNORED = {'wx:key', 'wx:for-item', 'wx:for-index', 'hover-class', 'hover-stop-propagation', 'scroll-x', 'scroll-y', 'adjust-position', 'cursor-spacing', 'show-confirm-bar', 'auto-height', 'loading', 'enable-flex', 'bindkeyboardheightchange', 'catchtouchmove'}

def expression(value):
    if re.fullmatch(r'\s*{{[\s\S]*}}\s*', value) and len(re.findall(r'{{', value)) == 1:
        return value.strip()[2:-2].strip()
    pieces = []
    for piece in re.split(r'({{[\s\S]*?}})', value):
        if piece.startswith('{{'):
            pieces.append('(' + piece[2:-2].strip() + ')')
        elif piece:
            pieces.append(json.dumps(piece, ensure_ascii=False))
    return '[' + ','.join(pieces) + "].join('')"

class Converter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        output_tag = TAGS.get(tag, tag)
        converted = []
        if tag == 'switch': converted.append(('type', 'checkbox'))
        for key, value in attrs.items():
            value = value or ''
            if key in IGNORED: continue
            if key == 'wx:for':
                item = attrs.get('wx:for-item', 'item'); index = attrs.get('wx:for-index', 'index')
                converted.append(('v-for', f'({item}, {index}) in {expression(value)}'))
                identity = attrs.get('wx:key', '')
                if identity and identity != '*this': converted.append((':key', f'{item}.{identity}'))
                else: converted.append((':key', index))
            elif key in ('wx:if', 'wx:elif'): converted.append(('v-if' if key == 'wx:if' else 'v-else-if', expression(value)))
            elif key == 'wx:else': converted.append(('v-else', ''))
            elif key.startswith(('bind', 'catch')):
                event = key.split(':')[-1] if ':' in key else re.sub(r'^(bind|catch)', '', key)
                event = {'tap': 'click', 'confirm': 'keydown.enter.prevent', 'longpress': 'contextmenu.prevent'}.get(event, event)
                if key.startswith('catch'): event += '.stop'
                converted.append(('@' + event, f'__event({json.dumps(value)}, $event)'))
            elif key == 'aria-role': converted.append(('role', value))
            elif key in ('confirm-type', 'focus', 'mode') and tag != 'picker': continue
            elif key == 'src' and tag == 'image':
                source = expression(value) if '{{' in value else json.dumps(value)
                converted.append((':src', '__asset(' + source + ')'))
            elif '{{' in value: converted.append((':' + key, expression(value)))
            else: converted.append((key, value))
        if tag == 'image': converted.append(('style', 'object-fit:' + ('contain' if attrs.get('mode') == 'aspectFit' else 'cover')))
        if tag == 'scroll-view': converted.append(('style', 'overflow:auto;white-space:nowrap'))
        encoded = ' '.join(f'{key}="{html.escape(value, quote=True).replace("&#x27;", "&#39;")}"' for key, value in converted)
        self.output.append('<' + output_tag + (' ' + encoded if encoded else '') + '>')
    def handle_endtag(self, tag):
        output_tag = TAGS.get(tag, tag)
        if output_tag not in VOID: self.output.append('</' + output_tag + '>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)
    def handle_data(self, data): self.output.append(html.escape(data, quote=False))

def css(source):
    source = re.sub(r'(-?\d+(?:\.\d+)?)rpx', r'calc(\1 * var(--rpx))', source)
    for original, target in [('page', '.qy-surface'), ('view', 'div'), ('text', 'span'), ('image', 'img')]:
        source = re.sub(r'\b' + original + r'\b(?=[\s,.:#>{\[])', target, source)
    return source

def convert(path):
    source = path.read_text(encoding='utf-8-sig')
    parser = Converter(); parser.feed(source)
    expressions = re.findall(r'{{([\s\S]*?)}}', source)
    keys = set()
    for expr in expressions:
        expr = re.sub(r"'[^']*'|\"[^\"]*\"", '', expr)
        keys.update(re.findall(r'(?<![\w$.])\b[a-zA-Z_$][\w$]*', expr))
    aliases = set(re.findall(r'wx:for-(?:item|index)="([^"]+)"', source)) | {'item', 'index', 'true', 'false', 'null', 'undefined', 'Math', 'Date', 'Number'}
    return {'template': '<div class="qy-page">' + ''.join(parser.output) + '</div>', 'keys': sorted(keys - aliases), 'css': css(path.with_suffix('.wxss').read_text(encoding='utf-8-sig'))}

if __name__ == '__main__':
    source, dest = map(Path, sys.argv[1:3])
    pages = {path.parent.name: convert(path) for path in (source / 'pages').glob('*/index.wxml')}
    pages['activity-card'] = convert(source / 'components/activity-card/index.wxml')
    pages['globalCSS'] = css((source / 'app.wxss').read_text(encoding='utf-8-sig'))
    dest.write_text('window.QingyeTemplates = ' + json.dumps(pages, ensure_ascii=False) + ';', encoding='utf-8')

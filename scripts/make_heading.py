from __future__ import annotations
import base64
from pathlib import Path
import html

ROOT=Path(__file__).resolve().parents[1]
FONT=base64.b64encode((ROOT/'assets/fonts/basic.woff2').read_bytes()).decode()
FG='#242424'

def make(text):
    width=max(250, 18*len(text)+390)
    y=18
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="30" viewBox="0 0 {width} 30" role="img" aria-label="{html.escape(text.title())}">
<style>@font-face{{font-family:NotoMono;src:url(data:font/woff2;base64,{FONT}) format("woff2")}}text{{font-family:NotoMono,monospace}}</style>
<text x="0" y="{y}" font-size="13" fill="{FG}">{html.escape(text)}</text>
<line x1="{18*len(text)+35}" y1="14" x2="{width}" y2="14" stroke="{FG}" stroke-width="0.8"/>
</svg>'''

for t in ['about','selected work','stack','github activity','elsewhere']:
    (ROOT/f'heading-{t.replace(" ","-")}.svg').write_text(make(t),encoding='utf-8')

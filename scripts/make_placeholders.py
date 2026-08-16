from pathlib import Path
import base64
ROOT=Path(__file__).resolve().parents[1]
fd=base64.b64encode((ROOT/'assets/fonts/basic.woff2').read_bytes()).decode()
items={'stats.svg':('github activity','refreshing contribution data…',620,100),'streak.svg':('streaks','refreshing streak data…',620,95),'langs.svg':('languages · bytes / repositories','refreshing language data…',620,90),'year.svg':('one character per day · contribution year','refreshing contribution year…',620,75)}
for fn,(title,msg,w,h) in items.items():
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}"><style>@font-face{{font-family:NotoMono;src:url(data:font/woff2;base64,{fd}) format("woff2")}}text{{font-family:NotoMono,monospace;fill:#6b6b6b}}</style><text x="0" y="20" font-size="12">{title}</text><text x="0" y="55" font-size="12">{msg}</text></svg>'
    (ROOT/fn).write_text(svg)

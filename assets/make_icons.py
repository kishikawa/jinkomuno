"""アイコン（色違い）の SVG を生成する。

CRT ターミナル風アイコンのフォスファー色を差し替えた配色を定義し、
1 配色につき 1 つの SVG を assets/ に書き出す。PNG への変換は
qlmanage（macOS）で別途行う（README/コマンド参照）。
    python assets/make_icons.py
"""
import os

# 各配色。bg* は背景グラデーション、glow* は画面のグロー、
# accent が顔の蛍光色、accent_dark がプロンプト、bubble_text は吹き出し内の文字。
PALETTES = {
    "green": {
        "bg": ("#16241d", "#0c1812", "#05100a"),
        "glow": ("#0b2417", "#04110a"),
        "bezel": "#13261c",
        "bezel_stroke": "#2c5a40",
        "accent": "#3df08a",
        "accent_dark": "#2bd673",
        "bubble_text": "#06241a",
    },
    "amber": {
        "bg": ("#241d12", "#181208", "#0f0a04"),
        "glow": ("#241a0b", "#110b04"),
        "bezel": "#2a2113",
        "bezel_stroke": "#6e5226",
        "accent": "#ffbf45",
        "accent_dark": "#e89a2b",
        "bubble_text": "#2a1602",
    },
    "red": {
        "bg": ("#241616", "#180c0c", "#100505"),
        "glow": ("#240b0b", "#110404"),
        "bezel": "#2a1414",
        "bezel_stroke": "#6e2c2c",
        "accent": "#ff5a52",
        "accent_dark": "#e23b34",
        "bubble_text": "#2a0606",
    },
    "cyan": {
        "bg": ("#16222a", "#0c1418", "#050e10"),
        "glow": ("#0b1e24", "#040f12"),
        "bezel": "#132429",
        "bezel_stroke": "#2c5560",
        "accent": "#4fd6ff",
        "accent_dark": "#2bb8e6",
        "bubble_text": "#03222a",
    },
    "magenta": {
        "bg": ("#241624", "#180c18", "#100510"),
        "glow": ("#240b22", "#110410"),
        "bezel": "#261327",
        "bezel_stroke": "#5e2c60",
        "accent": "#ff6fd8",
        "accent_dark": "#e64ab8",
        "bubble_text": "#2a0622",
    },
}

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{bg0}"/>
      <stop offset="0.55" stop-color="{bg1}"/>
      <stop offset="1" stop-color="{bg2}"/>
    </linearGradient>
    <radialGradient id="screenGlow" cx="0.5" cy="0.42" r="0.75">
      <stop offset="0" stop-color="{glow0}"/>
      <stop offset="1" stop-color="{glow1}"/>
    </radialGradient>
    <!-- 走査線（スキャンライン）パターンでCRTっぽさを出す -->
    <pattern id="scan" width="6" height="6" patternUnits="userSpaceOnUse">
      <rect width="6" height="6" fill="none"/>
      <rect width="6" height="3" fill="#000000" opacity="0.18"/>
    </pattern>
  </defs>

  <!-- 背景（角丸スクエア） -->
  <rect x="0" y="0" width="512" height="512" rx="112" fill="url(#bg)"/>

  <!-- モニタのベゼル -->
  <rect x="74" y="92" width="364" height="312" rx="46" fill="{bezel}" stroke="{bezel_stroke}" stroke-width="3"/>
  <!-- 画面 -->
  <rect x="100" y="116" width="312" height="264" rx="26" fill="url(#screenGlow)"/>

  <!-- 顔。半目のジト目＋小馬鹿にした口元 -->
  <g fill="{accent}">
    <g>
      <path d="M150 214 q42 -8 84 0 v8 q-42 10 -84 0 z"/>
      <circle cx="192" cy="232" r="17"/>
    </g>
    <g>
      <path d="M278 214 q42 -8 84 0 v8 q-42 10 -84 0 z"/>
      <circle cx="320" cy="232" r="17"/>
    </g>
  </g>

  <!-- 口元：への字＋わずかな片側上げのスマーク -->
  <path d="M196 312 q40 -22 80 -8 q22 8 44 -6"
        fill="none" stroke="{accent}" stroke-width="11" stroke-linecap="round"/>

  <!-- プロンプト記号と点滅カーソル -->
  <text x="132" y="356" font-family="'Courier New', monospace" font-size="34"
        font-weight="bold" fill="{accent_dark}">&gt;</text>
  <rect x="158" y="332" width="22" height="30" rx="2" fill="{accent}" opacity="0.9"/>

  <!-- 「は？」吹き出し -->
  <g>
    <rect x="300" y="320" width="104" height="56" rx="16" fill="{accent}"/>
    <path d="M322 372 l-2 22 22 -16 z" fill="{accent}"/>
    <text x="352" y="358" text-anchor="middle"
          font-family="'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans CJK JP','Yu Gothic',sans-serif"
          font-size="34" font-weight="bold" fill="{bubble_text}">は？</text>
  </g>

  <!-- 走査線オーバーレイ -->
  <rect x="100" y="116" width="312" height="264" rx="26" fill="url(#scan)"/>

  <!-- 電源LED -->
  <circle cx="256" cy="392" r="5" fill="{accent}" opacity="0.8"/>
</svg>
"""


def build_svg(palette: dict) -> str:
    """配色からSVG文字列を組み立てる。"""
    return TEMPLATE.format(
        bg0=palette["bg"][0],
        bg1=palette["bg"][1],
        bg2=palette["bg"][2],
        glow0=palette["glow"][0],
        glow1=palette["glow"][1],
        bezel=palette["bezel"],
        bezel_stroke=palette["bezel_stroke"],
        accent=palette["accent"],
        accent_dark=palette["accent_dark"],
        bubble_text=palette["bubble_text"],
    )


def main() -> None:
    here = os.path.dirname(__file__)
    for name, palette in PALETTES.items():
        path = os.path.join(here, f"icon-{name}.svg")
        with open(path, "w", encoding="utf-8") as file:
            file.write(build_svg(palette))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()

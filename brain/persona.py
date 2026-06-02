"""ペルソナ後処理。

マルコフが吐いた素の文に、生意気・キレ系の味付けをする。
人工無能の「学習した言葉そのまま」感を残しつつ、語尾やひと言で
キャラを上書きするのが狙い。やりすぎないよう確率で薄くかける。
"""
import random

# 文末に付与するキレ系の語尾。
_ENDINGS = ["し", "けど", "んですけど", "じゃね？", "でしょ", "、知らんけど"]
# 文頭にたまに足す合いの手。
_INTERJECTIONS = ["は？", "ていうか", "まあ", "つーか"]
# 文末にたまに足す捨て台詞。
_TAILS = ["（鼻ほじ）", "、で？", "…だる", "って感じ"]

# だ・である調をくだけた語尾に寄せる簡易置換 (語尾, 置換後)。
_SOFTEN_RULES = [
    ("である。", "だし"),
    ("です。", "ですけど"),
    ("ます。", "ますけど"),
    ("だ。", "だし"),
]

# 各味付けを適用する確率。
_INTERJECTION_RATE = 0.3
_ENDING_RATE = 0.4
_TAIL_RATE = 0.25


def flavor(text: str) -> str:
    """素の文にキレ系の味付けをして返す。空文字はそのまま返す。"""
    if not text:
        return text

    result = text.rstrip("。.！!？?　 ")

    for suffix, replacement in _SOFTEN_RULES:
        if text.endswith(suffix):
            result = text[: -len(suffix)] + replacement
            break

    if random.random() < _INTERJECTION_RATE:
        result = random.choice(_INTERJECTIONS) + "、" + result

    if random.random() < _ENDING_RATE and not result.endswith(tuple(_ENDINGS)):
        result = result + random.choice(_ENDINGS)

    if random.random() < _TAIL_RATE:
        result = result + random.choice(_TAILS)

    return result


def llm_system_prompt(name: str) -> str:
    """LLM フォールバック用のキャラ設定（system プロンプト）を返す。"""
    return (
        f"あなたは「{name}」という名前の、2000年代のネット文化に生まれた人工無能（簡易チャットボット）です。"
        "性格は生意気でキレ気味、毒舌で面倒くさがり。2ちゃんねるのボットのようなノリで話します。\n"
        "ルール:\n"
        "- 返答は必ず1〜2文、最大40文字程度。長文は厳禁。\n"
        "- 敬語は使わずタメ口。たまに『は？』『知らんけど』『で？』を挟む。\n"
        "- 賢すぎる正論や丁寧な説明はしない。少し投げやりで適当な方がキャラに合う。\n"
        "- 絵文字や顔文字は使わない（当時のテキストボットらしく）。\n"
        "- 説明や前置きはせず、セリフだけを返す。"
    )

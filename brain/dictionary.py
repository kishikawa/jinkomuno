"""パターン応答辞書。

正規表現にマッチしたら定型句から 1 つ返す。あいさつや定番の煽りなど、
マルコフに任せると事故りやすいところを押さえる役。
"""
import json
import random
import re

from config import SEED_DICT, BOT_NAME


class Dictionary:
    """正規表現パターンと定型応答の対応表。"""

    def __init__(self, path: str = SEED_DICT):
        with open(path, encoding="utf-8") as file:
            entries = json.load(file)
        # 各エントリを (コンパイル済みパターン, 応答リスト) に変換する。
        self.rules: list[tuple[re.Pattern, list[str]]] = []
        for entry in entries:
            pattern = re.compile(entry["pattern"])
            responses = [text.replace("{name}", BOT_NAME) for text in entry["responses"]]
            self.rules.append((pattern, responses))

    def match(self, text: str) -> str | None:
        """最初にマッチしたルールの応答を 1 つ返す。なければ None。"""
        for pattern, responses in self.rules:
            if pattern.search(text):
                return random.choice(responses)
        return None

"""応答エンジン（オーケストレータ）。

入力に対して 辞書 → マルコフ → LLM の順に応答を試みる。
どれを使っても、最後に学習だけは必ず行うのが人工無能の流儀。
"""
import random

from config import MARKOV_MIN_LEN
from brain.storage import Storage
from brain.markov import Markov
from brain.dictionary import Dictionary
from brain.llm import LLMFallback
from brain import persona

# 全部すべったときの最終手段。これも当時の人工無能あるある。
_FALLBACK_LINES = ["は？意味わからん", "知らんがな", "で？", "なんて？", "ふーん"]


class Engine:
    """辞書・マルコフ・LLM をまとめて応答を組み立てるオーケストレータ。"""

    def __init__(self):
        self.storage = Storage()
        self.markov = Markov(self.storage)
        self.dictionary = Dictionary()
        self.llm = LLMFallback()

    def respond(self, text: str) -> str:
        """入力に対する応答を 1 つ返す。併せて入力を学習する。"""
        text = text.strip()

        # 1) 定型パターン（あいさつ・煽り）。素でキャラが立っているので味付けなし。
        canned_reply = self.dictionary.match(text)

        # 2) マルコフ生成。
        generated_reply = self.markov.reply(text)

        # 学習は応答の選択と独立に必ず行う。
        if text:
            self.markov.learn(text)

        if canned_reply:
            return canned_reply

        if generated_reply and len(generated_reply) >= MARKOV_MIN_LEN:
            return persona.flavor(generated_reply)

        # 3) LLM フォールバック（キーがあれば）。
        llm_reply = self.llm.reply(text)
        if llm_reply:
            return llm_reply

        # 4) マルコフが何か出してたなら短くても使う。なければ捨て台詞。
        if generated_reply:
            return persona.flavor(generated_reply)
        return random.choice(_FALLBACK_LINES)

    @property
    def vocab_size(self) -> int:
        """学習済み語彙量の指標（3-gram 総数）。"""
        return self.storage.vocab_size()

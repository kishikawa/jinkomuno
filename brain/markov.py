"""マルコフ連鎖エンジン。

janome で形態素解析して 3-gram を学習し、相手の発言中の単語を
「お題」にして文を再構成する。人工無能の中核。
"""
import random

from janome.tokenizer import Tokenizer

from brain.storage import Storage, BEGIN, END

# お題に向く品詞（名詞・動詞・形容詞）。助詞などはお題にしない。
_TOPIC_POS_TAGS = ("名詞", "動詞", "形容詞")
# 学習・お題から除外する、短すぎる/記号的なトークン。
_IGNORED_TOKENS = {"", " ", "　", "\n", "\t"}


class Markov:
    """3-gram によるマルコフ連鎖の学習と文生成。"""

    def __init__(self, storage: Storage):
        self.storage = storage
        self.tokenizer = Tokenizer()

    # ---- 学習 ----------------------------------------------------------

    def tokenize(self, text: str) -> list[tuple[str, str]]:
        """テキストを (表層形, 品詞) のタプル列に分解する。"""
        tokens = []
        for token in self.tokenizer.tokenize(text):
            surface = token.surface.strip()
            if surface in _IGNORED_TOKENS:
                continue
            part_of_speech = token.part_of_speech.split(",")[0]
            tokens.append((surface, part_of_speech))
        return tokens

    def learn(self, text: str) -> None:
        """1 発言を学習する。3-gram とキーワード索引を更新する。"""
        tokens = self.tokenize(text)
        if not tokens:
            return
        words = [surface for surface, _ in tokens]
        topics = [
            surface
            for surface, part_of_speech in tokens
            if part_of_speech in _TOPIC_POS_TAGS and len(surface) > 1
        ]

        sequence = [BEGIN, BEGIN] + words + [END]
        for index in range(len(sequence) - 2):
            self.storage.add_trigram(
                sequence[index], sequence[index + 1], sequence[index + 2]
            )

        # 文頭 2-gram を、文中の各お題語に紐づけて索引する。
        if len(words) >= 2:
            first_word, second_word = words[0], words[1]
            for keyword in set(topics):
                self.storage.add_keyword_start(keyword, first_word, second_word)

    # ---- 生成 ----------------------------------------------------------

    def _weighted_choice(self, candidates: list[tuple[str, int]]) -> str:
        """[(token, count), ...] から count を重みに 1 つ選ぶ。"""
        tokens = [token for token, _ in candidates]
        weights = [count for _, count in candidates]
        return random.choices(tokens, weights=weights, k=1)[0]

    def _generate_from(self, w1: str, w2: str, max_words: int = 40) -> str:
        """文頭 2-gram から END まで（または上限まで）単語をつないで文を作る。"""
        result = [w1, w2]
        for _ in range(max_words):
            candidates = self.storage.next_candidates(w1, w2)
            if not candidates:
                break
            next_word = self._weighted_choice(candidates)
            if next_word == END:
                break
            result.append(next_word)
            w1, w2 = w2, next_word
        return "".join(word for word in result if word not in (BEGIN, END))

    def reply(self, text: str) -> str:
        """相手の発言からお題を拾って 1 文返す。生成できなければ空文字。"""
        tokens = self.tokenize(text)
        topics = [
            surface
            for surface, part_of_speech in tokens
            if part_of_speech in _TOPIC_POS_TAGS and len(surface) > 1
        ]
        random.shuffle(topics)

        # お題に紐づく文頭から生成を試す。
        for keyword in topics:
            starts = self.storage.starts_for_keyword(keyword)
            if starts:
                first_word, second_word, _ = random.choice(starts)
                generated = self._generate_from(first_word, second_word)
                if generated:
                    return generated

        # お題が刺さらなければ、覚えている適当な文頭から。
        starts = self.storage.random_starts()
        if starts:
            first_word, second_word, _ = random.choice(starts)
            generated = self._generate_from(first_word, second_word)
            if generated:
                return generated

        return ""

"""設定の読み込み。環境変数（.env）からまとめて取得する。"""
import os

from dotenv import load_dotenv

load_dotenv()


def _read_float(key: str, default: float) -> float:
    """環境変数を float として読む。未設定・不正値なら default。"""
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


def _read_int(key: str, default: int) -> int:
    """環境変数を int として読む。未設定・不正値なら default。"""
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

BOT_NAME = os.getenv("MUNO_NAME", "ムノ")

# メンションされていなくても、この確率でランダムに口を挟む（人工無能っぽさの肝）。
RANDOM_REPLY_RATE = _read_float("MUNO_RANDOM_REPLY_RATE", 0.15)

# マルコフ生成がこの文字数未満なら LLM フォールバックを試みる。
MARKOV_MIN_LEN = _read_int("MUNO_MARKOV_MIN_LEN", 6)

# 学習データの保存先。テスト等では MUNO_BRAIN_DB で別ファイルに差し替えられる。
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRAIN_DB = os.getenv("MUNO_BRAIN_DB") or os.path.join(DATA_DIR, "brain.sqlite3")
SEED_DICT = os.path.join(DATA_DIR, "seed_dictionary.json")

# LLM フォールバックが使えるか。
LLM_ENABLED = bool(ANTHROPIC_API_KEY)

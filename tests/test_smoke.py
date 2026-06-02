"""スモークテスト。

エンジンが「落ちずに何か返す」ことと、辞書・マルコフの基本経路が
生きていることを確認する。LLM フォールバックは API キー無しでも
動く（呼ばれない）ことが前提。

学習データは一時 DB に隔離するため、config を import する前に
環境変数 MUNO_BRAIN_DB を設定しておく。
"""
import os
import tempfile

# config が import 時に環境変数を読むので、それより前に上書きする。
_TMP_DB = os.path.join(tempfile.mkdtemp(prefix="muno-test-"), "brain.sqlite3")
os.environ["MUNO_BRAIN_DB"] = _TMP_DB
os.environ.pop("ANTHROPIC_API_KEY", None)  # LLM フォールバックを無効化して決定的にする。

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from brain.engine import Engine  # noqa: E402
from seed_corpus import CORPUS  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="module")
def engine() -> Engine:
    instance = Engine()
    for line in CORPUS:
        instance.markov.learn(line)
    return instance


def test_seed_corpus_increases_vocab(engine: Engine) -> None:
    """種コーパス投入後は語彙が貯まっている。"""
    assert engine.vocab_size > 0


def test_dictionary_path_responds(engine: Engine) -> None:
    """辞書にマッチする入力（あいさつ）は定型句を返す。"""
    reply = engine.respond("おはよう")
    assert isinstance(reply, str) and reply.strip()


def test_markov_path_responds(engine: Engine) -> None:
    """辞書に無い入力でも、空文字ではない応答を返す。"""
    reply = engine.respond("プログラミングって難しいよね")
    assert isinstance(reply, str) and reply.strip()


def test_never_crashes_on_varied_input(engine: Engine) -> None:
    """記号・空白・絵文字など雑多な入力でも例外を出さず文字列を返す。"""
    for text in ["", "   ", "？？？", "あ", "🍣🍣", "a" * 200]:
        reply = engine.respond(text)
        assert isinstance(reply, str)


def test_llm_fallback_disabled_without_key(engine: Engine) -> None:
    """API キーが無ければ LLM フォールバックは無効。"""
    assert engine.llm.enabled is False

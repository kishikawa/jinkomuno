"""コマンドルーターのテスト（discord 非依存）。"""
import os
import tempfile

# config が import 時に環境変数を読むので、それより前に上書きする。
_TMP_DB = os.path.join(tempfile.mkdtemp(prefix="muno-cmd-test-"), "brain.sqlite3")
os.environ["MUNO_BRAIN_DB"] = _TMP_DB
os.environ.pop("ANTHROPIC_API_KEY", None)

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from brain.engine import Engine  # noqa: E402
from brain.commands import CommandRouter  # noqa: E402

import pytest  # noqa: E402

CHANNEL = 12345


@pytest.fixture
def router() -> CommandRouter:
    return CommandRouter(Engine())


def test_is_command_detects_prefix(router: CommandRouter) -> None:
    assert router.is_command("!muno help") is True
    assert router.is_command("こんにちは") is False


def test_help_lists_commands(router: CommandRouter) -> None:
    reply = router.handle("!muno help", CHANNEL, is_admin=False)
    assert "!muno" in reply and "teach" in reply


def test_teach_increases_vocab(router: CommandRouter) -> None:
    before = router.engine.vocab_size
    reply = router.handle("!muno teach 今日はいい天気だね", CHANNEL, is_admin=False)
    assert router.engine.vocab_size > before
    assert reply  # 何か返す


def test_teach_without_text_complains(router: CommandRouter) -> None:
    reply = router.handle("!muno teach", CHANNEL, is_admin=False)
    assert isinstance(reply, str) and reply.strip()


def test_mute_requires_admin(router: CommandRouter) -> None:
    # 非管理者は拒否され、ミュートされない。
    router.handle("!muno mute", CHANNEL, is_admin=False)
    assert router.is_muted(CHANNEL) is False
    # 管理者ならミュートされる。
    router.handle("!muno mute", CHANNEL, is_admin=True)
    assert router.is_muted(CHANNEL) is True
    # 解除も管理者なら可能。
    router.handle("!muno unmute", CHANNEL, is_admin=True)
    assert router.is_muted(CHANNEL) is False


def test_forget_clears_learning(router: CommandRouter) -> None:
    router.handle("!muno teach 覚えるための文章だよ", CHANNEL, is_admin=True)
    assert router.engine.vocab_size > 0
    router.handle("!muno forget", CHANNEL, is_admin=True)
    assert router.engine.vocab_size == 0


def test_unknown_command_is_handled(router: CommandRouter) -> None:
    reply = router.handle("!muno hogehoge", CHANNEL, is_admin=False)
    assert isinstance(reply, str) and reply.strip()

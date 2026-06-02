"""LLM フォールバック。

マルコフが詰まったときだけ呼ばれる助け舟。キャラ設定（system）は
プロンプトキャッシュに載せて、毎回のトークンを節約する。
API キーが無ければ常に None を返し、マルコフのみで動く。
"""
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, LLM_ENABLED, BOT_NAME
from brain.persona import llm_system_prompt

_MODEL = "claude-haiku-4-5-20251001"  # 軽量・高速。相づち程度なら十分。


class LLMFallback:
    """マルコフが詰まったときだけ呼ぶ LLM の助け舟。"""

    def __init__(self):
        self.enabled = LLM_ENABLED
        self._client = Anthropic(api_key=ANTHROPIC_API_KEY) if self.enabled else None
        self._system = llm_system_prompt(BOT_NAME)

    def reply(self, text: str) -> str | None:
        """キャラを保った短い応答を返す。無効・失敗時は None。"""
        if not self.enabled:
            return None
        try:
            msg = self._client.messages.create(
                model=_MODEL,
                max_tokens=80,
                system=[
                    {
                        "type": "text",
                        "text": self._system,
                        # 固定のキャラ設定をキャッシュしてヒット率を上げる。
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": text}],
            )
            parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
            out = "".join(parts).strip()
            return out or None
        except Exception:
            # フォールバックが落ちても本体は止めない。
            return None

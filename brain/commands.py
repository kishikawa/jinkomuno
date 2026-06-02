"""コマンドの解釈と振り分け。

`!muno <コマンド>` 形式のテキストを受け取り、応答文字列を返す。
discord に依存しないので単体テストできる。Discord 固有の処理
（権限判定・送信）は bot.py 側が担当する。

ミュート状態（チャンネルごとの自発発言停止）はメモリ上にだけ持つ。
ボットを再起動すると解除される点に注意。
"""
from config import BOT_NAME, LLM_ENABLED
from brain.engine import Engine

PREFIX = "!muno"

# キレ系の口調で書いたヘルプ。
_HELP_TEXT = (
    f"**{BOT_NAME} のコマンド一覧**（前置きは `!muno`）\n"
    "`!muno help` … これ。見れば分かるでしょ\n"
    "`!muno ping` … 生きてるか確認したいわけ？\n"
    "`!muno stats` … どんだけ覚えたか見せてやる\n"
    "`!muno say` … お題なしでひとこと吐く\n"
    "`!muno teach <文>` … 言葉を仕込む。変なこと教えないでよ\n"
    "`!muno mute` … このチャンネルで黙る（要・管理権限）\n"
    "`!muno unmute` … しゃべり再開（要・管理権限）\n"
    "`!muno forget` … 記憶を全消去（要・管理権限。戻せないから）"
)

# 管理権限が要るコマンド。
_ADMIN_COMMANDS = {"mute", "unmute", "forget"}


class CommandRouter:
    """テキストコマンドを解釈して応答を組み立てる。"""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.muted_channels: set[int] = set()

    def is_command(self, text: str) -> bool:
        """先頭が `!muno` ならコマンドとみなす。"""
        return text.strip().lower().startswith(PREFIX)

    def is_muted(self, channel_id: int) -> bool:
        """指定チャンネルで自発発言が止められているか。"""
        return channel_id in self.muted_channels

    def handle(self, text: str, channel_id: int, is_admin: bool) -> str:
        """`!muno ...` 形式のテキストを解釈して実行し、応答を返す。"""
        body = text.strip()[len(PREFIX):].strip()
        name, _, argument = body.partition(" ")
        return self.execute(name.lower() or "help", argument.strip(), channel_id, is_admin)

    def execute(self, name: str, argument: str, channel_id: int, is_admin: bool) -> str:
        """コマンド名と引数から応答を組み立てる（テキスト/スラッシュ共通）。"""
        if name in _ADMIN_COMMANDS and not is_admin:
            return "は？権限ないでしょ。管理者にでも言って"

        if name == "help":
            return _HELP_TEXT
        if name == "ping":
            return "生きてるけど。で、何？"
        if name == "stats":
            llm_state = "ON" if LLM_ENABLED else "OFF"
            mute_state = "黙ってる" if self.is_muted(channel_id) else "通常"
            return f"語彙 {self.engine.vocab_size} / LLM {llm_state} / ここでは「{mute_state}」"
        if name == "say":
            return self.engine.generate()
        if name == "teach":
            if not argument:
                return "何を覚えろっての？文を続けて書きな"
            self.engine.teach(argument)
            return "覚えた。記憶力には期待しないでよ"
        if name == "mute":
            self.muted_channels.add(channel_id)
            return "はいはい、黙ればいいんでしょ。呼ばれたら出てくるけど"
        if name == "unmute":
            self.muted_channels.discard(channel_id)
            return "しゃべっていいんだ。我慢してたんだけど"
        if name == "forget":
            self.engine.reset()
            return "全部忘れた。せいせいした"

        return "そんなコマンド知らない。`!muno help` でも見れば？"

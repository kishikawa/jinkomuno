"""Discord 常駐ボット本体。

メンションされたら必ず、それ以外でも一定確率で口を挟む。
発言は片っ端から学習して、育つほど"それっぽく"なる。
`!muno` で始まる発言はコマンドとして処理する（学習はしない）。
"""
import asyncio
import random

import discord

from config import DISCORD_TOKEN, RANDOM_REPLY_RATE, BOT_NAME, LLM_ENABLED
from brain.engine import Engine
from brain.commands import CommandRouter

intents = discord.Intents.default()
intents.message_content = True  # 発言を読んで学習するために必須（Portal でも要有効化）。

client = discord.Client(intents=intents)
engine = Engine()
router = CommandRouter(engine)


@client.event
async def on_ready() -> None:
    llm_state = "ON" if LLM_ENABLED else "OFF"
    print(f"[{BOT_NAME}] ログイン: {client.user}  (語彙 {engine.vocab_size} / LLM {llm_state})")


def is_admin(message: discord.Message) -> bool:
    """発言者がサーバーの管理権限を持つか（DM 等では False）。"""
    permissions = getattr(message.author, "guild_permissions", None)
    if permissions is None:
        return False
    return permissions.administrator or permissions.manage_guild


def should_reply(message: discord.Message) -> bool:
    """この発言に反応するか判定する。"""
    # 自分宛のメンション・リプライ、名前で呼ばれたら必ず反応。
    mentioned = client.user in message.mentions or BOT_NAME in message.content
    if mentioned:
        return True
    # ミュート中のチャンネルでは自発的には口を挟まない。
    if router.is_muted(message.channel.id):
        return False
    # それ以外は確率でランダムに口を挟む（人工無能の肝）。
    return random.random() < RANDOM_REPLY_RATE


def strip_mentions(message: discord.Message) -> str:
    """メンション部分を除いた本文を取り出す。"""
    text = message.content
    for mention in message.mentions:
        text = text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
    return text.strip()


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:  # 自分含むボット同士の無限ループ防止。
        return

    text = strip_mentions(message)
    if not text:
        return

    # コマンドはチャット応答・学習より優先して処理する。
    if router.is_command(text):
        reply = await asyncio.to_thread(
            router.handle, text, message.channel.id, is_admin(message)
        )
        await message.channel.send(reply)
        return

    if not should_reply(message):
        # 反応しないときも学習だけはしておく。
        engine.markov.learn(text)
        return

    async with message.channel.typing():
        # 同期処理（SQLite・LLM）をイベントループから外す。
        reply = await asyncio.to_thread(engine.respond, text)
        await asyncio.sleep(random.uniform(0.4, 1.4))  # 即レスしすぎない間。

    await message.channel.send(reply)


def main() -> None:
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN が未設定です。.env を確認してください。")
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()

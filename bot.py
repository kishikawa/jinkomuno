"""Discord 常駐ボット本体。

メンションされたら必ず、それ以外でも一定確率で口を挟む。
発言は片っ端から学習して、育つほど"それっぽく"なる。
`!muno` で始まる発言はコマンドとして処理する（学習はしない）。
"""
import asyncio
import random

import discord
from discord import app_commands

from config import DISCORD_TOKEN, RANDOM_REPLY_RATE, BOT_NAME, LLM_ENABLED, GUILD_ID
from brain.engine import Engine
from brain.commands import CommandRouter

intents = discord.Intents.default()
intents.message_content = True  # 発言を読んで学習するために必須（Portal でも要有効化）。

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
engine = Engine()
router = CommandRouter(engine)


@client.event
async def on_ready() -> None:
    # スラッシュコマンドを同期する。GUILD_ID 指定時はそのギルド限定で即時反映。
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        tree.copy_global_to(guild=guild)
        synced = await tree.sync(guild=guild)
    else:
        synced = await tree.sync()
    llm_state = "ON" if LLM_ENABLED else "OFF"
    print(
        f"[{BOT_NAME}] ログイン: {client.user}  "
        f"(語彙 {engine.vocab_size} / LLM {llm_state} / スラッシュ {len(synced)}個)"
    )


def _permissions_admin(permissions) -> bool:
    """権限オブジェクトが管理権限を含むか。"""
    if permissions is None:
        return False
    return permissions.administrator or permissions.manage_guild


def is_admin(message: discord.Message) -> bool:
    """発言者がサーバーの管理権限を持つか（DM 等では False）。"""
    return _permissions_admin(getattr(message.author, "guild_permissions", None))


def interaction_is_admin(interaction: discord.Interaction) -> bool:
    """スラッシュコマンドの実行者が管理権限を持つか。"""
    return _permissions_admin(getattr(interaction.user, "guild_permissions", None))


async def _run_slash(interaction: discord.Interaction, name: str, argument: str = "") -> None:
    """スラッシュコマンドを CommandRouter で実行して応答する。"""
    reply = await asyncio.to_thread(
        router.execute, name, argument, interaction.channel_id, interaction_is_admin(interaction)
    )
    await interaction.response.send_message(reply)


# /muno グループ。サブコマンドとしてテキスト版と同じ操作を提供する。
muno_group = app_commands.Group(name="muno", description=f"人工無能{BOT_NAME}の操作")


@muno_group.command(name="help", description="コマンド一覧を表示する")
async def slash_help(interaction: discord.Interaction) -> None:
    await _run_slash(interaction, "help")


@muno_group.command(name="ping", description="生きてるか確認する")
async def slash_ping(interaction: discord.Interaction) -> None:
    await _run_slash(interaction, "ping")


@muno_group.command(name="stats", description="学習状況を表示する")
async def slash_stats(interaction: discord.Interaction) -> None:
    await _run_slash(interaction, "stats")


@muno_group.command(name="say", description="お題なしでひとこと生成する")
async def slash_say(interaction: discord.Interaction) -> None:
    await _run_slash(interaction, "say")


@muno_group.command(name="teach", description="言葉を仕込む")
@app_commands.describe(text="覚えさせたい文")
async def slash_teach(interaction: discord.Interaction, text: str) -> None:
    await _run_slash(interaction, "teach", text)


@muno_group.command(name="mute", description="このチャンネルで自発発言を止める（要・管理権限）")
async def slash_mute(interaction: discord.Interaction) -> None:
    await _run_slash(interaction, "mute")


@muno_group.command(name="unmute", description="自発発言を再開する（要・管理権限）")
async def slash_unmute(interaction: discord.Interaction) -> None:
    await _run_slash(interaction, "unmute")


@muno_group.command(name="forget", description="学習データを全消去する（要・管理権限）")
async def slash_forget(interaction: discord.Interaction) -> None:
    await _run_slash(interaction, "forget")


tree.add_command(muno_group)


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

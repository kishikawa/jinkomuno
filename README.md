# 人工無能 ムノ（現代復活版）

2000年代に流行した「人工無能」を Discord に常駐させた現代版。
基本はあの頃と同じ **マルコフ連鎖＋辞書学習** で動き、会話が詰まったときだけ
**LLM がそっと助ける** ハイブリッド構成。性格は生意気・キレ系（2chボット風）。

## しくみ

ユーザーの発言に対して、次の順で応答を選ぶ。

1. **辞書（パターン応答）** — あいさつ・煽り・定番ネタに即レス（`data/seed_dictionary.json`）
2. **マルコフ連鎖** — janome で形態素解析して学習した 3-gram から、相手の発言中の単語を「お題」に文を生成
3. **LLM フォールバック** — マルコフが短すぎる/詰まったときだけ Anthropic API を呼ぶ（キーが無ければスキップ）

そしてどの応答を選んでも、**入力は必ず学習する**。喋らせるほど語彙が増えて"それっぽく"育つ。
最後に生成文へ生意気・キレ系の味付け（語尾「〜じゃね？」「知らんけど」など）を確率でかける。

```
入力 → [辞書] ─hit→ 応答
        └miss→ [マルコフ] ─十分な長さ→ ペルソナ後処理 → 応答
                  └短い/失敗→ [LLM] ─あれば→ 応答
                              └無ければ→ マルコフの断片 or 捨て台詞
入力 ──（常に）──→ 学習
```

## ファイル構成

| ファイル | 役割 |
|---|---|
| `bot.py` | Discord 本体。メンション必ず＋確率で口を挟む |
| `chat.py` | Discord 無しで試す REPL |
| `seed_corpus.py` | 初期学習データの投入 |
| `config.py` | `.env` から設定読み込み |
| `brain/engine.py` | 辞書→マルコフ→LLM のオーケストレータ |
| `brain/markov.py` | マルコフ連鎖（学習・生成） |
| `brain/dictionary.py` | パターン応答 |
| `brain/llm.py` | LLM フォールバック（プロンプトキャッシュ付き） |
| `brain/persona.py` | キレ系の味付け＋LLM用キャラ設定 |
| `brain/storage.py` | SQLite 永続化 |
| `data/seed_dictionary.json` | 定型応答の辞書 |

## セットアップ

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # DISCORD_TOKEN を埋める
python seed_corpus.py       # 初期語彙を投入（任意だが推奨）
```

### まず動作確認（Discord 不要）

```bash
python chat.py
```

### Discord で動かす

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリ作成 → Bot 追加
2. **Privileged Gateway Intents** の **MESSAGE CONTENT INTENT** を ON（学習に必須）
3. Bot トークンを `.env` の `DISCORD_TOKEN` に設定
4. OAuth2 で `bot` スコープ＋メッセージ送信権限を付けてサーバーに招待
5. 起動：

```bash
python bot.py
```

## 設定（`.env`）

| 変数 | 既定 | 説明 |
|---|---|---|
| `DISCORD_TOKEN` | — | Bot トークン（必須） |
| `ANTHROPIC_API_KEY` | 空 | LLM フォールバック用。空ならマルコフのみで動く |
| `MUNO_NAME` | ムノ | キャラ名 |
| `MUNO_RANDOM_REPLY_RATE` | 0.15 | メンション無しでも口を挟む確率 |
| `MUNO_MARKOV_MIN_LEN` | 6 | これ未満の生成は LLM に助けを求める |

## コマンド

Discord 上では接頭辞 `!muno` でボットを操作できる（`!muno help` で一覧）。

| コマンド | 説明 |
|---|---|
| `!muno help` / `ping` / `stats` | ヘルプ / 生存確認 / 学習状況 |
| `!muno say` | お題なしでひとこと生成 |
| `!muno teach <文>` | 指定文を学習させる |
| `!muno mute` / `unmute` | このチャンネルでの自発発言を停止 / 再開（要・管理権限） |
| `!muno forget` | 学習データを全消去（要・管理権限） |

詳細は [docs/COMMANDS.md](docs/COMMANDS.md) を参照。

## アイコン

CRT ターミナル風のアプリアイコン（512×512 PNG）を `assets/` に同梱。
フォスファー（蛍光体）の色違いを 5 パターン用意している。

| ファイル | 配色 |
|---|---|
| `assets/icon-green.png` | フォスファーグリーン（既定。`icon.png` と同じ） |
| `assets/icon-amber.png` | アンバー（当時の単色モニタ風） |
| `assets/icon-red.png` | レッド（キレ度マシマシ） |
| `assets/icon-cyan.png` | シアン |
| `assets/icon-magenta.png` | マゼンタ |

配色の調整・追加は `assets/make_icons.py` の `PALETTES` を編集して再生成する。

```bash
python assets/make_icons.py                    # SVG を生成
# PNG へ変換（macOS / qlmanage の例）
cd assets && qlmanage -t -s 512 -o . icon-green.svg && mv icon-green.svg.png icon-green.png
```

## カスタマイズ

- **口調を変える** → `data/seed_dictionary.json` の応答文と `brain/persona.py` の語尾リストを編集
- **賢さの調整** → `MUNO_MARKOV_MIN_LEN` を上げると LLM 依存↑、下げるとマルコフ純度↑（＝より無能でカオス）
- **おしゃべり度** → `MUNO_RANDOM_REPLY_RATE` で勝手に喋る頻度を調整

## 規約

本ボットを公開・運用する際は、以下を参照してください（サンプルにつき運用形態に合わせて加筆推奨）。

- [利用規約](TERMS.md)
- [プライバシーポリシー](PRIVACY.md)

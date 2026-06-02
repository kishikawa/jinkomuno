"""ターミナルで動作確認するための REPL。

Discord に繋がなくても、エンジン単体の挙動（学習＋応答）を試せる。
    python chat.py
"""
from brain.engine import Engine


def main():
    engine = Engine()
    print(f"人工無能 起動（語彙 {engine.vocab_size}）。 'q' で終了。")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text in ("q", "quit", "exit"):
            break
        if not text:
            continue
        print("muno>", engine.respond(text))


if __name__ == "__main__":
    main()

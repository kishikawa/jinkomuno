"""学習データの永続化。

マルコフ連鎖の遷移を SQLite に貯める。2000 年代の人工無能は
テキストファイルに辞書を書き出していたが、ここでは取り回しの良い
SQLite を使う（中身は単なる単語の連なりの統計なので思想は同じ）。

n-gram の慣習にならい、連続する単語を w1, w2, w3 と表記する。
"""
import sqlite3
import threading

from config import BRAIN_DB

# トークン列の先頭・末尾を表す番兵。実テキストには現れない記号にしておく。
BEGIN = "\x02"
END = "\x03"


class Storage:
    """マルコフ連鎖の統計を保持する SQLite ストア。"""

    def __init__(self, path: str = BRAIN_DB):
        # discord.py はマルチスレッドではないが、念のため直列化しておく。
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._connection:
            # 3-gram（w1, w2 -> w3）の出現回数。count を重みにして次語を選ぶ。
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS trigram (
                    w1 TEXT NOT NULL,
                    w2 TEXT NOT NULL,
                    w3 TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (w1, w2, w3)
                )
                """
            )
            # 入力に含まれる単語 -> その単語を含む文の開始 2-gram。
            # 相手の発言に出てきた単語を「お題」にして文を作るための索引。
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS keyword_start (
                    keyword TEXT NOT NULL,
                    w1 TEXT NOT NULL,
                    w2 TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (keyword, w1, w2)
                )
                """
            )

    def add_trigram(self, w1: str, w2: str, w3: str) -> None:
        """3-gram の出現回数を 1 増やす（無ければ作成）。"""
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO trigram (w1, w2, w3, count) VALUES (?, ?, ?, 1)
                ON CONFLICT(w1, w2, w3) DO UPDATE SET count = count + 1
                """,
                (w1, w2, w3),
            )

    def add_keyword_start(self, keyword: str, w1: str, w2: str) -> None:
        """キーワードと文頭 2-gram の対応の出現回数を 1 増やす。"""
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO keyword_start (keyword, w1, w2, count) VALUES (?, ?, ?, 1)
                ON CONFLICT(keyword, w1, w2) DO UPDATE SET count = count + 1
                """,
                (keyword, w1, w2),
            )

    def next_candidates(self, w1: str, w2: str) -> list[tuple[str, int]]:
        """(w1, w2) に続く w3 とその重み (count) の一覧を返す。"""
        with self._lock:
            cursor = self._connection.execute(
                "SELECT w3, count FROM trigram WHERE w1 = ? AND w2 = ?",
                (w1, w2),
            )
            return cursor.fetchall()

    def starts_for_keyword(self, keyword: str) -> list[tuple[str, str, int]]:
        """キーワードを含む文の開始 2-gram 候補を返す。"""
        with self._lock:
            cursor = self._connection.execute(
                "SELECT w1, w2, count FROM keyword_start WHERE keyword = ?",
                (keyword,),
            )
            return cursor.fetchall()

    def random_starts(self, limit: int = 50) -> list[tuple[str, str, int]]:
        """お題なしのときに使う、適当な文頭 2-gram を返す。"""
        with self._lock:
            cursor = self._connection.execute(
                "SELECT w2, w3, count FROM trigram WHERE w1 = ? ORDER BY RANDOM() LIMIT ?",
                (BEGIN, limit),
            )
            return cursor.fetchall()

    def vocab_size(self) -> int:
        """学習済み 3-gram の総数を返す（おおまかな語彙量の指標）。"""
        with self._lock:
            cursor = self._connection.execute("SELECT COUNT(*) FROM trigram")
            return cursor.fetchone()[0]

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from janome.tokenizer import Tokenizer


# ストップワードリスト（不要な助詞・助動詞・接続詞など）
STOPWORDS = {
    "の",
    "と",
    "で",
    "に",
    "は",
    "を",
    "が",
    "も",
    "や",
    "また",
    "なるほど",
    "これ",
    "それ",
    "あれ",
    "どこ",
    "なん",
    "何",
    "どう",
    "よう",
    "こと",
    "ある",
    "する",
    "いる",
    "できる",
    "ない",
    "なる",
    "言う",
    "思う",
    "行く",
    "w",
    "ww",
    "www",
    "wwww",
    "ｗ",
    "ｗｗ",
    "ｗｗｗ",
    "ｗｗｗｗ",
    "co",
    "com",
    "jp",
    "net",
    "amazon",
    "youtube",
    "status",
    "join",
    "view",
    "watch",
    "tenor",
    "tokyo",
    "md",
    "dp",
    "pd",
    "gif",
    "test",
    "discord",
    "いい",
    "な",
    "や",
    "もの",
    "ため",
    "てる",
    "いる",
    "やる",
    "みたい",
    "ところ",
    "出社",
    "ちゃん",
    "そんな",
    "むむ",
    "leave",
    "si",
    "tabelog",
    "amzn",
    "asia",
    "ANA",
    "youtube",
    "be",
    "する",
    "なる",
    "shorts",
    "ja",
    "or",
    "BC",
    "MTG",
    "PC",
    "bot",
    "article",
    "html",
    "さん",
    "https",
    "youtu",
    "そう",
}
# SQLite からメッセージデータを取得
def fetch_messages():
    conn = sqlite3.connect("messages.db")
    df = pd.read_sql_query("SELECT content FROM messages", conn)
    conn.close()
    return df


# 日本語の分かち書き（形態素解析）
def tokenize_text(text):
    tokenizer = Tokenizer()
    words = [
        token.surface
        for token in tokenizer.tokenize(text)
        if len(token.surface) > 1 and token.surface not in STOPWORDS
        # and token.part_of_speech.split(",")[0] not in ["助詞", "助動詞", "記号", "感動詞", "副詞"]
        and token.part_of_speech.split(",")[0] in ["名詞", "動詞"]  # 重要な単語のみ残す
    ]  # 1文字の単語は除外
    return " ".join(words)


# ワードクラウドを生成
def generate_wordcloud():
    df = fetch_messages()

    if df.empty:
        print("❌ データベースにメッセージがありません！")
        return

    # メッセージを一つのテキストに結合
    text = " ".join(df["content"])

    # 形態素解析で単語に分割
    tokenized_text = tokenize_text(text)

    # ワードクラウドの設定
    wordcloud = WordCloud(
        font_path="/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # 日本語フォントの指定（Mac）
        width=800,
        height=400,
        background_color="white",
        colormap="viridis",
    ).generate(tokenized_text)

    # 画像を表示
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()


# 実行
if __name__ == "__main__":
    generate_wordcloud()

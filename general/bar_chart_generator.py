import sqlite3
import pandas as pd
import bar_chart_race as bcr
import matplotlib.pyplot as plt

# フォント設定（Mac・Linux向け）
plt.rcParams["font.family"] = "IPAexGothic"  # Windowsなら "MS Gothic"

# SQLite から月ごとの累積コメント数を取得
def generate_cumulative_monthly_data():
    conn = sqlite3.connect("messages.db")

    # ユーザーごとの月ごとのコメント数を取得
    query = """
        SELECT strftime('%Y-%m', timestamp) as month, author, COUNT(*) as count
        FROM messages
        GROUP BY month, author
        ORDER BY month, count DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # データの整形（ピボットテーブルを作成）
    df_pivot = df.pivot(index="month", columns="author", values="count").fillna(0)

    # 累積値に変換（fillna の修正）
    df_cumulative = df_pivot.cumsum().ffill()

    return df_cumulative


# バーチャートレース（アニメーション）
def generate_bar_chart_race():
    df_cumulative = generate_cumulative_monthly_data()

    if df_cumulative.empty:
        print("❌ データベースにメッセージがありません！")
        return

    # アニメーション作成（累計ランキングの月次推移）
    bcr.bar_chart_race(
        df=df_cumulative,
        filename="comment_ranking.mp4",
        orientation="h",
        sort="desc",
        n_bars=10,
        fixed_order=False,
        fixed_max=True,
        steps_per_period=10,
        interpolate_period=False,
        period_length=1000,
        title="Discord 累計コメントランキング（月次推移）",
        bar_label_size=10,
        tick_label_size=10,
        filter_column_colors=True,  # ✅ カラーフィルタを追加
    )

    print("✅ アニメーション動画が 'comment_ranking.mp4' として保存されました！")


# 実行
if __name__ == "__main__":
    generate_bar_chart_race()

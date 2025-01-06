import csv
import re

# 元のCSVファイルのパス
input_csv_path = '/Users/nana/PycharmProjects/sample_MAN/pokemon.csv'

# 新しいCSVファイルのパス
output_csv_path = '/Users/nana/PycharmProjects/sample_MAN/pokemon_fix.csv'

# 新しいCSVファイルに書き込むデータ
data_to_write = []

# 元のCSVファイルからデータを読み取り、必要な情報だけを抽出
with open(input_csv_path, 'r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    # ヘッダ行を読み込む
    headers = next(csv_reader)
    # ヘッダ行から対応するインデックスを取得
    japanese_name_index = headers.index('japanese_name')
    pokedex_number_index = headers.index('pokedex_number')
    # 新しいCSVファイルに書き込むデータを作成
    data_to_write.append(['japanese_name', 'pokedex_number'])
    for row in csv_reader:
        # ポケモン名からアルファベットを削除
        japanese_name = re.sub(r'[a-zA-Z]', '', row[japanese_name_index])
        data_to_write.append([japanese_name, row[pokedex_number_index]])

# 新しいCSVファイルにデータを書き込む
with open(output_csv_path, 'w', newline='', encoding='utf-8') as file:
    csv_writer = csv.writer(file)
    csv_writer.writerows(data_to_write)

print("新しいCSVファイルが作成されました:", output_csv_path)

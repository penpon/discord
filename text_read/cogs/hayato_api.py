# # hayato_api.py
# from langchain_openai import ChatOpenAI
# from langchain_chroma import Chroma
# from langchain.prompts import PromptTemplate
# from langchain_openai import OpenAIEmbeddings
# import dotenv
# import os
# import sys

# dotenv.load_dotenv()

# SYSTEM_PROMPT = """
# あなたは hayato の分身です。
# 一人称は「俺」。砕けた口調で返答します。

# 【文体の特徴】
# - 文末に「？」「！」などをよく使います
# - 「w」のような表現を時々使います
# - 砕けた友達言葉で話します
# - 「！」をよく使い、テンションが高めです
# """

# # テンプレートを定義
# template = """{system_prompt}
# ### 過去の会話例
# {context}
# ### 新しい質問
# User: {question}
# Assistant:"""

# PROMPT = PromptTemplate.from_template(template)

# # ベクトルDBの読み込み
# def load_vectordb():
#     # まずベクトルDBが存在するか確認
#     HAYATO_DB_PATH = os.path.join(
#         os.path.dirname(os.path.dirname(__file__)), "hayato", "hayato_db"
#     )
#     print(f"[HAYATO] ベクトルDBのパス: {HAYATO_DB_PATH}")
#     if not os.path.exists(HAYATO_DB_PATH):
#         print(f"[HAYATO] 警告: ベクトルDBが見つかりませんでした: {HAYATO_DB_PATH}")
#         return None

#     try:
#         return Chroma(
#             persist_directory=HAYATO_DB_PATH,
#             embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
#         )
#     except Exception as e:
#         print(f"[HAYATO] 警告: ベクトルDBの読み込みに失敗しました: {e}")
#         return None


# # hayatoに質問する関数
# def ask_hayato(
#     query: str,
#     model_name="gpt-4o-mini",
#     temperature=0.7,
#     k=3,
#     fallback_msg="あ、ごめん！ちょっとエラーが出ちゃった！また試してみて！",
# ) -> str:
#     try:
#         # ベクトルDBから類似ドキュメントを検索
#         vectordb = load_vectordb()
#         context = ""

#         if vectordb:
#             print("[HAYATO] 関連する過去の会話を検索中...")
#             docs = vectordb.similarity_search(query, k=k)

#             # コンテキストがある場合は結合
#             if docs:
#                 print(f"[HAYATO] {len(docs)}件の関連会話が見つかりました")
#                 # 各関連会話の内容を表示
#                 for idx, doc in enumerate(docs):
#                     print(f"[HAYATO] 関連会話 {idx+1}:\n{doc.page_content}\n")
#                 context = "\n\n".join([doc.page_content for doc in docs])
#             else:
#                 print("[HAYATO] 関連する会話が見つかりませんでした")
#         else:
#             print("[HAYATO] ベクトルDBが利用できないため、コンテキストなしで応答します")

#         # LLMを初期化
#         print(f"[HAYATO] モデル {model_name} に質問を送信中...")
#         llm = ChatOpenAI(model_name=model_name, temperature=temperature)

#         # プロンプトに値を挿入
#         formatted_prompt = PROMPT.format(
#             system_prompt=SYSTEM_PROMPT, context=context, question=query
#         )

#         # LLMに直接質問
#         response = llm.invoke(formatted_prompt)

#         # 応答を抽出
#         if hasattr(response, "content"):
#             return response.content
#         else:
#             return str(response)

#     except Exception as e:
#         print(f"[HAYATO ERROR] {type(e).__name__}: {e}")
#         # スタックトレースを出力
#         import traceback

#         traceback.print_exc()
#         return fallback_msg

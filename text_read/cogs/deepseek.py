# deepseek.py
import requests
from cogs.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, CHARACTER_SETTING


def ask_deepseek(question: str) -> str:
    """DeepSeek APIへの問い合わせ"""
    print(f"[DEEPSEEK] 質問を受信しました: {question[:30]}...")
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": [
            {"role": "system", "content": CHARACTER_SETTING},
            {"role": "user", "content": question},
        ],
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 50,
    }

    try:
        print("[DEEPSEEK] APIリクエストを送信しています...")
        response = requests.post(
            DEEPSEEK_API_URL, headers=headers, json=payload, timeout=10
        )
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        print(f"[DEEPSEEK] 正常なレスポンスを受信しました: {result[:30]}...")
        return result
    except requests.Timeout:
        print("[DEEPSEEK ERROR] APIリクエストがタイムアウトしました")
        return "もう少し待ってよね！急がせないでよ！"
    except Exception as e:
        print(f"[DEEPSEEK ERROR] API処理中にエラーが発生しました: {str(e)}")
        return "え？今、ちょっと頭がぼーっとしてた..."

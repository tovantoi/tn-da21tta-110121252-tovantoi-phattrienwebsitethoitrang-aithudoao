from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import pyodbc
from datetime import datetime

app = Flask(__name__)
CORS(app)

# OpenAI API Key
openai.api_key = ''

# Kết nối SQL Server
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=VANTOI\SQLEXPRESS;'
        'DATABASE=chuyen_nganh;'
        'Trusted_Connection=yes;'  
    )
    return conn
def is_fashion_related(message):
    fashion_keywords = [
        'áo', 'quần', 'váy', 'giày', 'túi', 'phối đồ','xin chào'
        'thời trang', 'phụ kiện', 'xu hướng', 'size',
        'màu sắc', 'chọn đồ', 'phong cách', 'ootd', 'dress',
        'áo khoác', 'áo sơ mi', 'quần jean', 'giày sneaker'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in fashion_keywords)

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')

    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    # Kiểm tra có phải câu hỏi liên quan thời trang không
    if not is_fashion_related(user_message):
        reply = "Xin lỗi, tôi chỉ hỗ trợ các câu hỏi liên quan đến thời trang. Bạn có thể hỏi tôi về phối đồ, chọn size, hoặc xu hướng hiện nay nhé!"
        # Vẫn lưu vào lịch sử với phản hồi từ chối
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ChatHistory (UserMessage, BotReply) VALUES (?, ?)",
            user_message, reply
        )
        conn.commit()
        conn.close()
        return jsonify({'reply': reply})

    # Nếu hợp lệ, gọi GPT
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là chatbot tư vấn thời trang. "
                        "Chỉ trả lời các câu hỏi về quần áo, phụ kiện, phối đồ, chọn size, xu hướng... "
                        "Từ chối những câu hỏi ngoài lĩnh vực này."
                    )
                },
                {"role": "user", "content": user_message}
            ]
        )

        bot_reply = response['choices'][0]['message']['content']

        # Lưu lịch sử vào DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ChatHistory (UserMessage, BotReply) VALUES (?, ?)",
            user_message, bot_reply
        )
        conn.commit()
        conn.close()

        return jsonify({'reply': bot_reply})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

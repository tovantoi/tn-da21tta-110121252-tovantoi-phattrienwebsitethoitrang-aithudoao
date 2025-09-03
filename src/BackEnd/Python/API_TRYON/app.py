import os
import time
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS  

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['UPLOAD_FOLDER'] = 'uploads'
API_KEY = "dcbdc0576c104c5db2462b350025820583803714d191da5e21dedee2949a1e55"  # Thay bằng API Key thật của bạn

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/tryon', methods=['POST'])
def tryon():
    try:
        # 1. Nhận ảnh người và áo
        model_img = request.files.get('person')
        cloth_img = request.files.get('cloth')

        if not model_img or not cloth_img:
            return "Thiếu ảnh người hoặc quần áo", 400

        model_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(model_img.filename))
        cloth_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(cloth_img.filename))

        model_img.save(model_path)
        cloth_img.save(cloth_path)
        print("✅ Ảnh đã lưu:", model_path, cloth_path)

        # 2. Gửi tạo task đến Fitroom
        url = "https://platform.fitroom.app/api/tryon/v2/tasks"
        headers = {
            "X-API-KEY": API_KEY
        }
        files = {
            "cloth_image": open(cloth_path, "rb"),
            "model_image": open(model_path, "rb"),
            "cloth_type": (None, "full")  # "upper" | "lower" | "full" | "combo"
        }

        response = requests.post(url, headers=headers, files=files)
        print("📨 Phản hồi từ Fitroom:", response.status_code, response.text)

        if response.status_code != 200:
            return f"Lỗi khi tạo task: {response.text}", 500

        task_id = response.json().get("task_id")
        if not task_id:
            return "Không nhận được task_id từ Fitroom", 500

        print("🎯 Task ID:", task_id)

        # 3. Poll kết quả mỗi 1.5 giây
        status_url = f"https://platform.fitroom.app/api/tryon/v2/tasks/{task_id}"
        for _ in range(30):  # Tối đa 30 lần ~ 45 giây
            status_res = requests.get(status_url, headers=headers)
            data = status_res.json()
            status = data.get("status")
            print(f"⏳ Trạng thái task: {status}")

            if status == "COMPLETED":
                result_url = data.get("download_signed_url")
                print("✅ Kết quả URL:", result_url)
                return jsonify({ "result_url": result_url })

            elif status == "FAILED":
                return f"❌ Task thất bại: {data.get('error')}", 500

            time.sleep(1.5)

        return "⏰ Quá thời gian xử lý", 504

    except Exception as e:
        import traceback
        print("❌ Lỗi server:\n", traceback.format_exc())
        return f"Lỗi server: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)

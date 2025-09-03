from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pyodbc
import os
from dotenv import load_dotenv
import base64
import mimetypes
import re
# Tải các biến môi trường từ file .env
load_dotenv()
gemini_api_key = os.getenv('')

app = Flask(__name__)
CORS(app)

# Cấu hình API Key cho Gemini
genai.configure(api_key=gemini_api_key)

# Kết nối SQL Server
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=VANTOI\SQLEXPRESS;'
        'DATABASE=chuyen_nganh;'
        'Trusted_Connection=yes;'
    )
    return conn
def is_unwanted_topic(message):
    unwanted_keywords = [
        # Từ khóa tiếng Việt
        'website', 'lập trình', 'phần mềm', 'code', 'trình duyệt', 'công nghệ thông tin',
        'phát triển web', 'học lập trình', 'hướng dẫn code', 'ứng dụng', 'app', 'hệ thống',
        
        # Từ khóa tiếng Anh
        'website', 'programming', 'software', 'code', 'development', 'web development', 
        'frontend', 'backend', 'javascript', 'python', 'php', 'java', 'c++', 'c#', 
        'node.js', 'react', 'angular', 'vue', 'html', 'css', 'sql', 'database', 
        'algorithm', 'machine learning', 'artificial intelligence', 'AI', 'coding', 'developer'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in unwanted_keywords)

def is_greeting(message):
    greetings = [
        'xin chào', 'chào bạn', 'chào anh', 'chào chị', 'chào em', 'chào mọi người', 'chào mừng',
        'chào buổi sáng', 'chào buổi trưa', 'chào buổi chiều', 'chào buổi tối',
        'hello', 'hi', 'hey', 'alo', 'kính chào', 'thân chào', 'chào quý khách', 'chào thầy', 'chào cô',
        'chào ông', 'chào bà', 'chào chú', 'chào bác', 'chào cậu', 'chào dì', 'chào các bạn',
        'chào đồng chí', 'chào sếp', 'chào đồng nghiệp', 'chào thầy cô', 'chào thầy giáo', 'chào cô giáo',
        'chào anh chị em', 'chào cả nhà', 'chào các anh', 'chào các chị', 'chào các em', 'chào các cháu',
        'chào anh yêu', 'chào em yêu', 'chào bạn yêu', 'chào cưng', 'chào bé', 'chào con', 'chào cháu',
        'chào ông bà', 'chào bố', 'chào mẹ', 'chào ba', 'chào má', 'chào thím', 'chào mợ', 'chào dì ơi',
        'chào chú ơi', 'chào bác ơi', 'chào cậu ơi', 'chào anh ơi', 'chào chị ơi', 'chào em ơi',
        'chào bạn ơi', 'chào các cậu', 'chào các dì', 'chào các chú', 'chào các bác', 'chào các ông',
        'chào các bà', 'chào các cô', 'chào các thầy', 'chào các sếp', 'chào các đồng chí', 'chào các đồng nghiệp',
        'chào quý vị', 'chào quý vị và các bạn', 'chào quý khách hàng', 'chào quý thầy cô', 'chào quý anh chị',
        'chào quý ông bà', 'chào quý bà con', 'chào quý đồng nghiệp', 'chào quý đồng chí', 'chào quý sếp',
        'chào quý khách quý', 'chào quý khách thân mến', 'chào quý khách hàng thân thiết', 'chào quý khách hàng thân mến',
        'chào quý khách hàng kính mến', 'chào quý khách hàng yêu quý', 'chào quý khách hàng đáng kính',
        'chào quý khách hàng đáng mến', 'chào quý khách hàng thân yêu', 'chào quý khách hàng thân thiện',
        'chào quý khách hàng thân thương', 'chào quý khách hàng thân tình', 'chào quý khách hàng thân ái',
        'chào quý khách hàng thân cận', 'chào quý khách hàng thân thiết nhất', 'chào quý khách hàng thân mến nhất',
        'chào quý khách hàng kính mến nhất', 'chào quý khách hàng yêu quý nhất', 'chào quý khách hàng đáng kính nhất',
        'chào quý khách hàng đáng mến nhất', 'chào quý khách hàng thân yêu nhất', 'chào quý khách hàng thân thiện nhất',
        'chào quý khách hàng thân thương nhất', 'chào quý khách hàng thân tình nhất', 'chào quý khách hàng thân ái nhất',
        'chào quý khách hàng thân cận nhất', 'chào quý khách hàng thân thiết nhất của chúng tôi',
        'chào quý khách hàng thân mến nhất của chúng tôi', 'chào quý khách hàng kính mến nhất của chúng tôi',
        'chào quý khách hàng yêu quý nhất của chúng tôi', 'chào quý khách hàng đáng kính nhất của chúng tôi',
        'chào quý khách hàng đáng mến nhất của chúng tôi', 'chào quý khách hàng thân yêu nhất của chúng tôi',
        'chào quý khách hàng thân thiện nhất của chúng tôi', 'chào quý khách hàng thân thương nhất của chúng tôi',
        'chào quý khách hàng thân tình nhất của chúng tôi', 'chào quý khách hàng thân ái nhất của chúng tôi',
        'chào quý khách hàng thân cận nhất của chúng tôi'
    ]
    message_lower = message.lower()
    return any(greeting in message_lower for greeting in greetings)
def get_status_label(status):
    mapping = {
        0: "Chờ xác nhận",
        1: "Đã xác nhận",
        2: "Đang giao hàng",
        3: "Đã giao hàng",
        4: "Đã hủy"
    }
    return mapping.get(status, "Không xác định")

def is_order_question(message):
    keywords = ['đơn hàng', 'mua gì', 'đặt hàng', 'đã giao chưa', 'tình trạng đơn', 'tracking', 'vận chuyển', 'đơn số']
    message_lower = message.lower()
    return any(k in message_lower for k in keywords)


def is_fashion_related(message):
    fashion_keywords = [
        # Từ khóa cơ bản về trang phục
        'áo', 'quần', 'váy', 'giày', 'túi', 'phối đồ', 'thời trang', 'phụ kiện', 
        'xu hướng', 'size', 'màu sắc', 'chọn đồ', 'phong cách', 'ootd', 'dress', 
        'áo khoác', 'áo sơ mi', 'quần jean', 'giày sneaker', 'trang phục', 'mẫu thiết kế',
        'cách phối', 'mua sắm', 'combo', 'lookbook', 'bộ sưu tập', 'thời trang công sở',
        'sự kiện thời trang', 'red carpet', 'show diễn', 'diễn đàn thời trang', 'tư vấn thời trang',
        'thời trang đường phố', 'phong cách sống',
               
        # Từ khoá về câu hỏi
        'đi tiệc mặc gì', 'mặc gì đi đám cưới', 'trang phục đi tiệc cưới', 'mặc gì cho sang',
        'ăn mặc sang trọng', 'phối đồ đi đám cưới', 'phối đồ dự tiệc', 'trang phục dự sự kiện',
        'mặc đẹp đi tiệc', 'chọn đầm dự tiệc', 'gợi ý trang phục dự tiệc', 'phong cách sang trọng',
        'outfit đi đám cưới', 'outfit dự tiệc', 'gợi ý phối đồ đi tiệc', 'style đi đám cưới',
        'trang phục thanh lịch', 'quần áo cho tiệc cưới', 'set đồ dự tiệc', 'mặc gì đi dạ hội',
        'outfit đi dạ hội', 'mix đồ sang trọng', 'lựa chọn trang phục đi đám cưới',
        'trang điểm đi tiệc', 'phụ kiện đi tiệc cưới', 'đi ăn cưới mặc gì đẹp', 'tiệc đêm mặc gì',
        'tiệc ngày mặc gì', 'dresscode tiệc cưới', 'trang phục theo dresscode', 'trang phục phù hợp lễ cưới',
        'phù hợp hoàn cảnh', 'mặc gì để nổi bật', 'thời trang tiệc tùng', 'phối váy đi tiệc',
        'váy cưới khách mời', 'đi cưới người thân mặc gì', 'đi đám cưới người yêu cũ mặc gì',
        'đi tiệc nhà hàng mặc gì', 'mặc gì cho buổi tiệc quan trọng', 'lựa chọn váy phù hợp',
        'tư vấn trang phục dạ tiệc', 'váy dự sự kiện lớn', 'thời trang thảm đỏ', 'váy dự thảm đỏ',
        'set đồ dự lễ', 'cách phối đồ sang trọng', 'dress sang chảnh', 'thời trang quý phái',
        'quý cô dự tiệc', 'nữ tính nhưng nổi bật', 'vừa lịch sự vừa đẹp', 'vẻ ngoài thu hút',
        'ấn tượng tại tiệc cưới', 'mặc gì để ghi điểm', 'trang phục có gu', 'ăn mặc có phong cách',
        
        # Từ khóa về trang phục dự tiệc và dạ hội
        'đầm dạ hội', 'váy dạ hội', 'trang phục dạ tiệc', 'đầm dự tiệc', 'váy dự tiệc',
        'đầm tiệc cưới', 'váy tiệc cưới', 'trang phục tiệc cưới', 'đầm sang trọng',
        'váy sang trọng', 'trang phục sang trọng', 'đầm lộng lẫy', 'váy lộng lẫy',
        'trang phục lộng lẫy', 'đầm dự tiệc cưới', 'váy dự tiệc cưới', 'đầm dự tiệc sang trọng',
        'váy dự tiệc sang trọng', 'đầm dự tiệc cao cấp', 'váy dự tiệc cao cấp',
        'trang phục dự tiệc cao cấp', 'đầm dự tiệc lộng lẫy', 'váy dự tiệc lộng lẫy',
        'trang phục dự tiệc lộng lẫy', 'đầm dự tiệc cưới sang trọng', 'váy dự tiệc cưới sang trọng',
        'trang phục dự tiệc cưới sang trọng', 'đầm dự tiệc cưới cao cấp', 'váy dự tiệc cưới cao cấp',
        'trang phục dự tiệc cưới cao cấp', 'đầm dự tiệc cưới lộng lẫy', 'váy dự tiệc cưới lộng lẫy',
        'trang phục dự tiệc cưới lộng lẫy', 'đầm dự tiệc buổi tối', 'váy dự tiệc buổi tối',
        'trang phục dự tiệc buổi tối', 'đầm dự tiệc ban đêm', 'váy dự tiệc ban đêm',
        'trang phục dự tiệc ban đêm', 'đầm dự tiệc mùa hè', 'váy dự tiệc mùa hè',
        'trang phục dự tiệc mùa hè', 'đầm dự tiệc mùa đông', 'váy dự tiệc mùa đông',
        'trang phục dự tiệc mùa đông', 'đầm dự tiệc mùa thu', 'váy dự tiệc mùa thu',
        'trang phục dự tiệc mùa thu', 'đầm dự tiệc mùa xuân', 'váy dự tiệc mùa xuân',
        'trang phục dự tiệc mùa xuân', 'đầm dự tiệc ngoài trời', 'váy dự tiệc ngoài trời',
        'trang phục dự tiệc ngoài trời', 'đầm dự tiệc trong nhà', 'váy dự tiệc trong nhà',
        'trang phục dự tiệc trong nhà', 'đầm dự tiệc công sở', 'váy dự tiệc công sở',
        'trang phục dự tiệc công sở', 'đầm dự tiệc bạn bè', 'váy dự tiệc bạn bè',
        'trang phục dự tiệc bạn bè', 'đầm dự tiệc gia đình', 'váy dự tiệc gia đình',
        'trang phục dự tiệc gia đình', 'đầm dự tiệc công ty', 'váy dự tiệc công ty',
        'trang phục dự tiệc công ty', 'đầm dự tiệc sinh nhật', 'váy dự tiệc sinh nhật',
        'trang phục dự tiệc sinh nhật', 'đầm dự tiệc kỷ niệm', 'váy dự tiệc kỷ niệm',
        'trang phục dự tiệc kỷ niệm', 'đầm dự tiệc tốt nghiệp', 'váy dự tiệc tốt nghiệp',
        'trang phục dự tiệc tốt nghiệp', 'đầm dự tiệc khai trương', 'váy dự tiệc khai trương',
        'trang phục dự tiệc khai trương', 'đầm dự tiệc họp mặt', 'váy dự tiệc họp mặt',
        'trang phục dự tiệc họp mặt', 'đầm dự tiệc tất niên', 'váy dự tiệc tất niên',
        'trang phục dự tiệc tất niên', 'đầm dự tiệc tân niên', 'váy dự tiệc tân niên',
        'trang phục dự tiệc tân niên', 'đầm dự tiệc giáng sinh', 'váy dự tiệc giáng sinh',
        'trang phục dự tiệc giáng sinh', 'đầm dự tiệc năm mới', 'váy dự tiệc năm mới',
        'trang phục dự tiệc năm mới', 'đầm dự tiệc halloween', 'váy dự tiệc halloween',
        'trang phục dự tiệc halloween', 'đầm dự tiệc valentine', 'váy dự tiệc valentine',
        'trang phục dự tiệc valentine', 'đầm dự tiệc 8/3', 'váy dự tiệc 8/3',
        'trang phục dự tiệc 8/3', 'đầm dự tiệc 20/10', 'váy dự tiệc 20/10',
        'trang phục dự tiệc 20/10', 'đầm dự tiệc 1/6', 'váy dự tiệc 1/6',
        'trang phục dự tiệc 1/6', 'đầm dự tiệc trung thu', 'váy dự tiệc trung thu',
        'trang phục dự tiệc trung thu', 'đầm dự tiệc cưới ngoài trời', 'váy dự tiệc cưới ngoài trời',
        'trang phục dự tiệc cưới ngoài trời', 'đầm dự tiệc cưới trong nhà', 'váy dự tiệc cưới trong nhà',
        'trang phục dự tiệc cưới trong nhà', 'đầm dự tiệc cưới mùa hè', 'váy dự tiệc cưới mùa hè',
        'trang phục dự tiệc cưới mùa hè', 'đầm dự tiệc cưới mùa đông', 'váy dự tiệc cưới mùa đông',
        'trang phục dự tiệc cưới mùa đông', 'đầm dự tiệc cưới mùa thu', 'váy dự tiệc cưới mùa thu',
        'trang phục dự tiệc cưới mùa thu', 'đầm dự tiệc cưới mùa xuân', 'váy dự tiệc cưới mùa xuân',
        'trang phục dự tiệc cưới mùa xuân', 'đầm dự tiệc cưới ban ngày', 'váy dự tiệc cưới ban ngày',
        'trang phục dự tiệc cưới ban ngày', 'đầm dự tiệc cưới buổi tối', 'váy dự tiệc cưới buổi tối',
        'trang phục dự tiệc cưới ban đêm',

        # Từ khóa chi tiết về thời trang nam, nữ, trẻ em
        'thời trang nam', 'thời trang nữ', 'thời trang trẻ em', 'áo dài', 'đầm',
        'trang sức', 'mũ', 'kính mát', 'quần short', 'quần kaki', 'váy đầm', 'giày cao gót',
        'giày thể thao', 'áo thun', 'áo polo', 'áo phông', 'áo croptop', 'set đồ',
        'vest', 'suit', 'đồ lót', 'áo len', 'quần tây', 'đồ bơi', 'áo blouse',
        'quần ống rộng', 'áo khoác len', 'áo bomber', 'áo cardigan',

        # Từ khóa mở rộng về phụ kiện và chi tiết sản phẩm
        'túi xách', 'đồng hồ', 'dép', 'bốt', 'balo', 'móc khóa', 'khăn quàng',
        'phụ kiện tóc', 'nón', 'dây lưng', 'ví', 'giày da', 'giày slip-on', 'giày boots',

        # Từ khóa liên quan đến chất liệu và kiểu dáng
        'vải', 'chất liệu', 'sợi', 'in hoa', 'thêu', 'thêu ren', 'màu in', 'họa tiết',
        'hoạ tiết', 'pattern', 'cắt may', 'tailor', 'form dáng', 'dáng người',

        # Từ khóa liên quan đến xu hướng theo mùa và phong cách
        'xu hướng mùa đông', 'xu hướng mùa hè', 'xu hướng mùa xuân', 'xu hướng mùa thu',
        'phong cách cổ điển', 'phong cách hiện đại', 'phong cách retro', 'phong cách vintage',
        'thời trang bền vững', 'thời trang giá rẻ', 'thời trang cao cấp', 'thời trang sang trọng',
        'thời trang đường phố', 'thời trang casual', 'thời trang lễ hội',

        # Từ khóa khác liên quan đến môi trường và quảng bá thời trang
        'sàn diễn', 'show thời trang', 'trình diễn thời trang', 'tạp chí thời trang',
        'blog thời trang', 'influencer thời trang', 'thương hiệu thời trang', 'nhãn hiệu',
        'hot trend', 'xuất hiện trên tivi', 'quảng cáo thời trang'
        
        # Các câu chào hỏi và từ mở đầu câu hỏi thường gặp
        'xin chào', 'chào bạn', 'chào anh', 'chào chị', 'chào em', 'chào mọi người', 'chào mừng',
        'làm thế nào', 'làm sao', 'cách', 'tư vấn', 'hướng dẫn', 'mẹo', 'bí quyết', 'ý kiến',
        'như thế nào', 'có thể', 'cho tôi biết', 'giúp tôi', 'thông tin', 'nên làm gì',
        'gợi ý', 'đề xuất'
        
        # Từ khóa cơ bản tiếng Anh
        'fashion', 'designer', 'couture', 'haute couture', 'catwalk', 'runway',
        'accessories', 'vintage', 'street style', 'trend', 'trendsetter', 'style',
        'outfit', 'apparel', 'wardrobe', 'ensemble', 'moda', 'chic', 'boho',
        'bohemian', 'minimalist', 'luxury', 'bespoke', 'tailor', 'fashion show',
        'fashion week', 'collection', 'boutique', 'urban', 'casual', 'formal',
        'retro', 'modern', 'designer label', 'lookbook',

        # Từ khóa tiếng Anh mở rộng
        'fashionista', 'editorial', 'runway show', 'glamour', 'sequin', 'sparkle',
        'monochrome', 'pattern', 'fabric', 'silk', 'cotton', 'denim', 'leather',
        'knitwear', 'embroidered', 'sustainable', 'eco-friendly', 'ethical fashion',
        'upcycled', 'fast fashion', 'luxury fashion', 'streetwear', 'sportswear',
        'activewear', 'loungewear', 'tailored', 'fitted', 'high fashion', 'bespoke tailoring',
        'couturier',

        # Từ khóa liên quan đến văn hóa và truyền thông thời trang
        'fashion magazine', 'photoshoot', 'editorial', 'brand', 'logo', 'signature',
        'runway model', 'fashion blogger', 'influencer', 'celebrity style', 'avant-garde',
        'edgy', 'innovative', 'sartorial'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in fashion_keywords)


@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message', '').strip()
    image_file = request.files.get('image')
    user_id_raw = request.form.get("user_id")

    if not user_id_raw or not user_id_raw.isdigit():
        return jsonify({'reply': '⚠️ Bạn chưa đăng nhập. Vui lòng đăng nhập để xem đơn hàng.'}), 400

    user_id = int(user_id_raw)

    if not user_message and not image_file:
        return jsonify({'error': 'Message or image is required'}), 400

    try:
        if image_file:
            os.makedirs("uploads", exist_ok=True)
            image_path = os.path.join("uploads", image_file.filename)
            image_file.save(image_path)

            mime_type, _ = mimetypes.guess_type(image_path)
            with open(image_path, "rb") as f:
                image_data = f.read()

            model = genai.GenerativeModel("gemini-pro-vision")
            response = model.generate_content([
                {"mime_type": mime_type, "data": image_data},
                "Đây là một sản phẩm thời trang. Hãy tư vấn cách phối đồ phù hợp."
            ])
            reply = response.text.strip()

        else:
            model = genai.GenerativeModel('gemini-1.5-flash')
            chat = model.start_chat()

            if is_greeting(user_message):
                reply = "Xin chào! Mình là trợ lý thời trang của bạn. Bạn cần gợi ý outfit hay phối đồ gì hôm nay nè?"

            elif is_unwanted_topic(user_message):
                reply = "Xin lỗi, mình chỉ hỗ trợ tư vấn thời trang. Các câu hỏi về công nghệ, lập trình hiện không nằm trong phạm vi hỗ trợ nha bạn."

            elif is_order_question(user_message):
                # 👉 Xử lý xem đơn hàng
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TOP 5 OrderId, CreatedAt, TotalPrice, Status
                    FROM [Order]
                    WHERE CustomerId = ?
                    ORDER BY CreatedAt DESC
                """, user_id)
                orders = cursor.fetchall()
                conn.close()

                if not orders:
                    reply = "Hiện bạn chưa có đơn hàng nào được ghi nhận trên hệ thống."
                else:
                    reply = "📦 Đây là một vài đơn hàng gần đây của bạn:\n"
                    for o in orders:
                        status_text = get_status_label(o.Status)
                        reply += f"- Đơn #{o.OrderId} ngày {o.CreatedAt.strftime('%d/%m/%Y')}, tổng: {float(o.TotalPrice):,.0f}đ, trạng thái: {status_text}\n"

            elif is_fashion_related(user_message):
                # 👉 Tư vấn thời trang + Gợi ý sản phẩm + blog
                prompt = f"""
                Bạn là chuyên gia tư vấn thời trang. Hãy trả lời ngắn gọn, rõ ràng, không liệt kê dàn trải. Nêu 2-3 điểm nổi bật, không lan man.
                Nếu có thể, gợi ý sản phẩm phù hợp.
                Câu hỏi người dùng: \"{user_message}\"
                """
                response = chat.send_message(prompt)
                reply = response.text.strip()

                # 🔸 Gợi ý sản phẩm
                conn = get_db_connection()
                cursor = conn.cursor()
                keywords = re.findall(r'\w+', user_message.lower())[:3]
                product_types = ['áo thun', 'áo sơ mi', 'áo', 'quần', 'giày', 'váy', 'phụ kiện', 'hoodie', 'áo khoác']
                matched_type = next((t for t in product_types if t in user_message.lower()), None)

                if matched_type:
                    cursor.execute(f"""
                        SELECT TOP 5 ProductId, ProductName
                        FROM Products
                        WHERE IsActive = 1 AND LOWER(ProductName) LIKE N'%{matched_type}%'
                        ORDER BY NEWID()
                    """)
                else:
                    prod_cond = " OR ".join([f"LOWER(ProductName) LIKE '%{k}%'" for k in keywords])
                    cursor.execute(f"""
                        SELECT TOP 5 ProductId, ProductName
                        FROM Products
                        WHERE IsActive = 1 AND ({prod_cond})
                        ORDER BY NEWID()
                    """)

                products = cursor.fetchall()

                if not products:
                    cursor.execute("""
                        SELECT TOP 5 ProductId, ProductName
                        FROM Products
                        WHERE IsActive = 1
                        ORDER BY NEWID()
                    """)
                    products = cursor.fetchall()

                if products:
                    reply += f"\n\n🛍️ Một vài sản phẩm bạn có thể thích:"
                    for p in products:
                        reply += f"\n- {p.ProductName}: http://localhost:3000/product/{p.ProductId}"

                # 🔸 Gợi ý blog
                blog_cond = " OR ".join([f"LOWER(Title) LIKE '%{k}%'" for k in keywords])
                cursor.execute(f"""
                    SELECT TOP 2 Id, Title FROM Blogs
                    WHERE IsActive = 1 AND ({blog_cond})
                    ORDER BY NEWID()
                """)
                blogs = cursor.fetchall()

                if blogs:
                    reply += "\n\n📚 Bài viết liên quan bạn có thể thích:"
                    for b in blogs:
                        reply += f"\n- {b.Title}: http://localhost:3000/blogpage/{b.Id}"

                conn.close()

            else:
                prompt = f"""
                Bạn là chuyên gia thời trang. Người dùng hỏi: \"{user_message}\". Trả lời ngắn gọn, rõ ràng, thân thiện.
                Giới hạn trong thời trang. Nếu không phù hợp, từ chối lịch sự.
                """
                response = chat.send_message(prompt)
                reply = response.text.strip()

        # 👉 Lưu lịch sử hội thoại
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ChatHistory (UserMessage, BotReply, UserId) VALUES (?, ?, ?)",
            (user_message, reply, user_id)
        )
        conn.commit()
        conn.close()

        return jsonify({'reply': reply})

    except Exception as e:
        import traceback
        print("Lỗi:", e)
        traceback.print_exc()
        return jsonify({'reply': '❌ Có lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại.'}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5050)
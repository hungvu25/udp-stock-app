# 📡 Ứng dụng Client/Server UDP với Mã hóa Đầu-cuối

## 🎯 Mô tả
Ứng dụ👤 Nhập dữ liệu: AAPL
🌐 AAPL: $211.105 USD
   Công ty: Apple Inc
   Nguồn: Finnhub API

👤 Nhập dữ liệu: 25
✅ Đã nhận số 25

👤 Nhập dữ liệu: MSFT
🌐 MSFT: $511.1 USD
   Công ty: Microsoft Corp
   Nguồn: Finnhub API

👤 Nhập dữ liệu: -5
⚠️  Số âm -5 bị bỏ qua

👤 Nhập dữ liệu: 0
🎯 === KẾT QUẢ CUỐI CÙNG ===
📊 Các số đã gửi: [15, 25]
🧮 Tổng các số > 0: 40dụng giao thức UDP với mã hóa AES end-to-end encryption để:
- Xử lý số nguyên và tính tổng các số > 0
- Truy vấn giá cổ phiếu qua Finnhub.io API (với fallback data)

## 🔧 Cài đặt

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình API Key (Tùy chọn)
Để sử dụng dữ liệu cổ phiếu thời gian thực:
1. Đăng ký miễn phí tại: https://finnhub.io/register
2. Lấy API key 
3. Mở `config.py` và thay thế:
   ```python
   FINNHUB_API_KEY = "your_real_api_key_here"
   ```
4. **Lưu ý:** Gói miễn phí có giới hạn 60 calls/minute

### 3. Chạy ứng dụng

#### Cách 1: Sử dụng batch files (Khuyến nghị)
1. **Khởi động Server**: Double-click `start_server.bat`
2. **Chạy Demo**: Double-click `run_demo.bat` (để xem demo tự động)
3. **Web Client**: Double-click `start_web_client.bat` (giao diện web đẹp)
4. **Console Client**: Double-click `start_client.bat` (giao diện dòng lệnh)

#### Cách 2: Chạy trực tiếp
1. **Terminal 1 - Server**:
   ```bash
   python server.py
   ```

2. **Terminal 2 - Client**:
   ```bash
   python web_client.py      # Web UI (http://localhost:5000)
   python client.py          # Console UI
   python test_demo.py       # Demo tự động
   ```

## 📋 Cách sử dụng

### Web Client (Khuyến nghị):
1. Mở trình duyệt tại: http://localhost:5000
2. **Giao diện đẹp** với design hiện đại
3. **Session riêng biệt** cho mỗi tab/client
4. **Nhập dữ liệu** trong ô input
5. **Xem kết quả** theo thời gian thực
6. **Lịch sử phiên** với các chức năng:
   - 📨 Gửi dữ liệu
   - 📋 Xem lịch sử (chỉ của session hiện tại)
   - 🗑️ Xóa lịch sử (chỉ của session hiện tại)
   - 🆔 Hiển thị Session ID

### Console Client:
1. Nhập **số nguyên dương**: Server sẽ lưu và cộng dồn
2. Nhập **số âm**: Server sẽ bỏ qua
3. Nhập **mã cổ phiếu**: Server truy vấn giá (VD: AAPL, GOOGL, MSFT)
4. Nhập **0**: Kết thúc phiên và nhận tổng các số > 0 đã gửi

### Demo tự động:
- Chạy `run_demo.bat` hoặc `python test_demo.py`
- Xem quá trình gửi số, truy vấn cổ phiếu và nhận kết quả

### Server:
- Lắng nghe liên tục trên cổng 12345
- Giải mã và xử lý dữ liệu từ client
- Lưu các số nguyên > 0 vào danh sách
- Truy vấn giá cổ phiếu (thử Finnhub API, fallback demo data)
- Gửi tổng khi nhận được số 0

## 🔐 Mã hóa
- **Thuật toán**: AES (Fernet từ thư viện cryptography)
- **Key**: Sinh từ password chung "shared_secret_key"
- **Salt**: Cố định để đảm bảo client và server cùng key
- **Tất cả dữ liệu** gửi qua UDP đều được mã hóa

## 📊 Ví dụ sử dụng (Demo output)

```
👤 Nhập dữ liệu: 15
✅ Đã nhận số 15

👤 Nhập dữ liệu: AAPL
� AAPL: 191.45 USD
   Công ty: Apple Inc.
   Nguồn: Demo Data

👤 Nhập dữ liệu: 25
✅ Đã nhận số 25

👤 Nhập dữ liệu: VIC
� VIC: 85000 VND
   Công ty: Vingroup JSC
   Nguồn: Demo Data

👤 Nhập dữ liệu: -5
⚠️  Số âm -5 bị bỏ qua

👤 Nhập dữ liệu: 0
🎯 === KẾT QUẢ CUỐI CÙNG ===
📊 Các số đã gửi: [15, 25]
🧮 Tổng các số > 0: 40
```

## 🏗️ Cấu trúc dự án
```
baitapThanhTan/
├── server.py              # UDP Server với mã hóa
├── web_client.py          # Web Client với Flask (UI/UX đẹp)
├── client.py              # Console Client tương tác thủ công
├── test_demo.py           # Demo tự động
├── config.py              # Cấu hình API keys
├── requirements.txt       # Dependencies
├── templates/             # Templates cho web
│   └── index.html         # Giao diện web chính
├── start_server.bat       # Script khởi động server
├── start_web_client.bat   # Script khởi động web client
├── start_client.bat       # Script khởi động console client
├── run_demo.bat           # Script chạy demo
└── README.md             # Hướng dẫn này
```

## 🌟 Tính năng đã thực hiện

### ✅ Yêu cầu Client:
- ✅ **Web UI/UX đẹp** với Flask + Socket.IO
- ✅ **Multiple sessions** - mỗi client có lịch sử riêng
- ✅ **Session management** với UUID unique
- ✅ **Auto cleanup** session cũ (24h)
- ✅ **Console UI** cho terminal
- ✅ Nhập liên tục từ giao diện
- ✅ Phân biệt số nguyên vs chuỗi (mã cổ phiếu)
- ✅ Kết thúc khi nhập số 0
- ✅ Mã hóa tất cả dữ liệu trước khi gửi
- ✅ Nhận và hiển thị tổng cuối cùng
- ✅ Lịch sử phiên làm việc riêng biệt

### ✅ Yêu cầu Server:
- ✅ Lắng nghe UDP liên tục
- ✅ Giải mã dữ liệu nhận được
- ✅ Lưu số nguyên > 0, bỏ qua số âm
- ✅ Truy vấn cổ phiếu và gửi kết quả
- ✅ Tính tổng khi nhận 0 và gửi lại client
- ✅ Xử lý "Mã không tồn tại"

### ✅ Mã hóa đầu-cuối:
- ✅ AES encryption (Fernet)
- ✅ Khóa đối xứng từ password chung
- ✅ Tất cả dữ liệu UDP được mã hóa

### ✅ Xử lý cổ phiếu:
- ✅ Finnhub.io API (dữ liệu thời gian thực)
- ✅ Hỗ trợ cổ phiếu quốc tế (US stocks)
- ✅ Xử lý lỗi khi mã không tồn tại

## 🐛 Xử lý lỗi
- ✅ Timeout kết nối (10 giây)
- ✅ Lỗi mã hóa/giải mã
- ✅ Mã cổ phiếu không tồn tại
- ✅ API rate limit (60 calls/minute)
- ✅ Lỗi mạng UDP

## 🚀 Demo nhanh
1. Mở Command Prompt và chạy: `start_server.bat`
2. Mở Command Prompt khác và chạy: `start_web_client.bat`
3. Truy cập: http://localhost:5000
4. **Mở thêm tab mới** hoặc **trình duyệt khác** - mỗi tab có session riêng!
5. Thử nhập: 15, AAPL, 25, MSFT, 0 ở mỗi tab
6. Xem mỗi tab có lịch sử hoàn toàn độc lập!

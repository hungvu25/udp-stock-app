import socket
import json
import threading
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import finnhub
import time
from config import FINNHUB_API_KEY

class UDPServer:
    def __init__(self, host='localhost', port=12345, password='shared_secret_key'):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        
        # Tạo key mã hóa từ password
        self.cipher_suite = self._create_cipher(password)
        
        # Danh sách lưu các số nguyên > 0
        self.positive_numbers = []
        
        # Địa chỉ client hiện tại
        self.current_client = None
        
        # Finnhub client (đọc API key từ config)
        # Để sử dụng API thật: Đăng ký tại https://finnhub.io/register
        self.finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
        
    def _create_cipher(self, password):
        """Tạo cipher từ password"""
        password_bytes = password.encode()
        salt = b'fixed_salt_12345'  # Salt cố định để client và server cùng key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def decrypt_message(self, encrypted_data):
        """Giải mã dữ liệu"""
        try:
            return self.cipher_suite.decrypt(encrypted_data).decode()
        except Exception as e:
            print(f"Lỗi giải mã: {e}")
            return None
    
    def encrypt_message(self, message):
        """Mã hóa dữ liệu"""
        return self.cipher_suite.encrypt(message.encode())
    
    def get_stock_price(self, symbol):
        """Truy vấn giá cổ phiếu qua Finnhub API"""
        try:
            # Chuẩn hóa symbol
            original_symbol = symbol.upper()
            finnhub_symbol = original_symbol
            
            print(f"Truy vấn Finnhub API: {original_symbol}")
            
            # Gọi Finnhub API để lấy quote
            quote = self.finnhub_client.quote(finnhub_symbol)
            
            if quote and 'c' in quote and quote['c'] > 0:
                current_price = quote['c']  # Current price
                
                # Lấy thông tin công ty
                try:
                    company_profile = self.finnhub_client.company_profile2(symbol=finnhub_symbol)
                    company_name = original_symbol
                    
                    if company_profile and 'name' in company_profile and company_profile['name']:
                        company_name = company_profile['name']
                        
                except Exception as profile_error:
                    print(f"⚠️ Không lấy được profile công ty: {profile_error}")
                    company_name = original_symbol
                
                print(f"✅ Finnhub API: {original_symbol} = ${current_price} USD")
                
                return {
                    'symbol': original_symbol,
                    'price': current_price,
                    'currency': 'USD',
                    'company': company_name,
                    'status': 'success',
                    'source': 'Finnhub API'
                }
            else:
                print(f"⚠️ Finnhub: Không có dữ liệu cho {original_symbol}")
                return {
                    'symbol': original_symbol,
                    'message': 'Mã không tồn tại',
                    'status': 'error'
                }
                
        except Exception as e:
            print(f"❌ Lỗi Finnhub API cho {original_symbol}: {e}")
            return {
                'symbol': original_symbol,
                'message': f'Lỗi API: {str(e)}',
                'status': 'error'
            }
    
    def process_data(self, data_str):
        """Xử lý dữ liệu nhận được"""
        try:
            # Thử parse thành số nguyên
            number = int(data_str)
            
            if number == 0:
                # Kết thúc quá trình - tính tổng và gửi về client
                total = sum(self.positive_numbers)
                print(f"\n=== KẾT THÚC PHIÊN ===")
                print(f"Các số đã nhận: {self.positive_numbers}")
                print(f"Tổng các số > 0: {total}")
                
                response = {
                    'type': 'final_sum',
                    'data': {
                        'numbers': self.positive_numbers,
                        'total': total
                    }
                }
                
                # Reset danh sách cho phiên tiếp theo
                self.positive_numbers = []
                
                return response, True  # True = kết thúc phiên
                
            elif number > 0:
                # Số nguyên dương - lưu vào danh sách
                self.positive_numbers.append(number)
                print(f"Nhận số: {number} (Danh sách: {self.positive_numbers})")
                
                response = {
                    'type': 'number_received',
                    'data': f"Đã nhận số {number}"
                }
                
                return response, False  # False = tiếp tục
                
            else:
                # Số âm - không xử lý
                print(f"Nhận số âm: {number} (bỏ qua)")
                response = {
                    'type': 'number_ignored',
                    'data': f"Số âm {number} bị bỏ qua"
                }
                
                return response, False
                
        except ValueError:
            # Không phải số - xem như mã cổ phiếu
            symbol = data_str.strip()
            print(f"Truy vấn cổ phiếu: {symbol}")
            
            stock_info = self.get_stock_price(symbol)
            
            response = {
                'type': 'stock_info',
                'data': stock_info
            }
            
            return response, False
    
    def handle_client(self, data, client_address):
        """Xử lý yêu cầu từ client"""
        try:
            # Giải mã dữ liệu
            decrypted_data = self.decrypt_message(data)
            if not decrypted_data:
                return
            
            # Lưu địa chỉ client hiện tại
            self.current_client = client_address
            
            # Xử lý dữ liệu
            response, is_end = self.process_data(decrypted_data)
            
            # Mã hóa và gửi phản hồi
            encrypted_response = self.encrypt_message(json.dumps(response))
            self.socket.sendto(encrypted_response, client_address)
            
        except Exception as e:
            print(f"Lỗi xử lý client {client_address}: {e}")
            error_response = {'type': 'error', 'data': 'Lỗi server'}
            encrypted_error = self.encrypt_message(json.dumps(error_response))
            self.socket.sendto(encrypted_error, client_address)
    
    def start(self):
        """Khởi động server"""
        print(f"🚀 UDP Server đã khởi động tại {self.host}:{self.port}")
        print("📡 Đang lắng nghe client...")
        print("🔐 Mã hóa: Đã kích hoạt")
        print("-" * 50)
        
        while True:
            try:
                data, client_address = self.socket.recvfrom(4096)
                
                # Xử lý request trong thread riêng để hỗ trợ nhiều client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(data, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                print("\n🔴 Server đang tắt...")
                break
            except Exception as e:
                print(f"Lỗi server: {e}")
        
        self.socket.close()
        print("✅ Server đã tắt")

if __name__ == "__main__":
    server = UDPServer()
    server.start()

import socket
import json
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class TestClient:
    def __init__(self, server_host='localhost', server_port=12345, password='shared_secret_key'):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(10)
        
        # Tạo key mã hóa từ password (phải giống server)
        self.cipher_suite = self._create_cipher(password)
    
    def _create_cipher(self, password):
        """Tạo cipher từ password (giống server)"""
        password_bytes = password.encode()
        salt = b'fixed_salt_12345'  # Phải giống server
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def encrypt_message(self, message):
        """Mã hóa dữ liệu"""
        return self.cipher_suite.encrypt(message.encode())
    
    def decrypt_message(self, encrypted_data):
        """Giải mã dữ liệu"""
        try:
            return self.cipher_suite.decrypt(encrypted_data).decode()
        except Exception as e:
            print(f"Lỗi giải mã: {e}")
            return None
    
    def send_data(self, data_str):
        """Gửi dữ liệu đến server và nhận phản hồi"""
        try:
            # Mã hóa dữ liệu
            encrypted_data = self.encrypt_message(data_str)
            
            # Gửi đến server
            self.socket.sendto(encrypted_data, (self.server_host, self.server_port))
            
            # Nhận phản hồi
            encrypted_response, server_address = self.socket.recvfrom(4096)
            
            # Giải mã phản hồi
            decrypted_response = self.decrypt_message(encrypted_response)
            if decrypted_response:
                return json.loads(decrypted_response)
            else:
                return {'type': 'error', 'data': 'Không thể giải mã phản hồi'}
                
        except socket.timeout:
            return {'type': 'error', 'data': 'Timeout'}
        except Exception as e:
            return {'type': 'error', 'data': f'Lỗi: {str(e)}'}
    
    def test_demo(self):
        """Demo ứng dụng"""
        print("🧪 === DEMO ỨNG DỤNG CLIENT/SERVER UDP ===")
        print("🔐 Mã hóa: AES (Fernet)")
        print("-" * 50)
        
        # Test data - chỉ sử dụng mã có trong Finnhub
        test_cases = [
            ("15", "Gửi số nguyên dương"),
            ("AAPL", "Truy vấn cổ phiếu Apple"),
            ("25", "Gửi số nguyên dương khác"),
            ("GOOGL", "Truy vấn cổ phiếu Google"),
            ("MSFT", "Truy vấn cổ phiếu Microsoft"),
            ("-5", "Gửi số âm (sẽ bị bỏ qua)"),
            ("TSLA", "Truy vấn cổ phiếu Tesla"),
            ("10", "Gửi số nguyên cuối"),
            ("INVALID123", "Mã cổ phiếu không tồn tại"),
            ("0", "Kết thúc và nhận tổng")
        ]
        
        for data, description in test_cases:
            print(f"\n📤 {description}: '{data}'")
            response = self.send_data(data)
            
            response_type = response.get('type', 'unknown')
            response_data = response.get('data', '')
            
            if response_type == 'number_received':
                print(f"✅ {response_data}")
            elif response_type == 'number_ignored':
                print(f"⚠️  {response_data}")
            elif response_type == 'stock_info':
                stock_data = response_data
                if stock_data['status'] == 'success':
                    source_icon = "🌐" if stock_data.get('source') == 'Finnhub API' else "📊"
                    currency = stock_data['currency']
                    price = stock_data['price']
                    
                    # Format giá theo currency
                    if currency == 'USD':
                        price_str = f"${price}"
                    elif currency == 'VND':
                        price_str = f"{price:,.0f}"
                    else:
                        price_str = f"{price}"
                    
                    print(f"{source_icon} {stock_data['symbol']}: {price_str} {currency}")
                    print(f"   Công ty: {stock_data['company']}")
                    if stock_data.get('source'):
                        print(f"   Nguồn: {stock_data['source']}")
                else:
                    print(f"❌ {stock_data['message']}")
            elif response_type == 'final_sum':
                final_data = response_data
                print(f"\n🎯 === KẾT QUẢ CUỐI CÙNG ===")
                print(f"📊 Các số đã gửi: {final_data['numbers']}")
                print(f"🧮 Tổng các số > 0: {final_data['total']}")
                print("=" * 40)
            elif response_type == 'error':
                print(f"❌ Lỗi: {response_data}")
            
            time.sleep(1)  # Pause giữa các request
        
        print(f"\n✅ Demo hoàn thành!")
        self.socket.close()

if __name__ == "__main__":
    client = TestClient()
    client.test_demo()

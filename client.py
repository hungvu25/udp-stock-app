import socket
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class UDPClient:
    def __init__(self, server_host='localhost', server_port=12345, password='shared_secret_key'):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(10)  # Timeout 10 giây
        
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
            return {'type': 'error', 'data': 'Timeout - không nhận được phản hồi từ server'}
        except Exception as e:
            return {'type': 'error', 'data': f'Lỗi giao tiếp: {str(e)}'}
    
    def display_response(self, response):
        """Hiển thị phản hồi từ server"""
        response_type = response.get('type', 'unknown')
        data = response.get('data', '')
        
        if response_type == 'number_received':
            print(f"✅ {data}")
            
        elif response_type == 'number_ignored':
            print(f"⚠️  {data}")
            
        elif response_type == 'stock_info':
            stock_data = data
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
            final_data = data
            print(f"\n🎯 === KẾT QUẢ CUỐI CÙNG ===")
            print(f"📊 Các số đã gửi: {final_data['numbers']}")
            print(f"🧮 Tổng các số > 0: {final_data['total']}")
            print("=" * 40)
            
        elif response_type == 'error':
            print(f"❌ Lỗi: {data}")
            
        else:
            print(f"📄 Phản hồi: {data}")
    
    def run(self):
        """Chạy client"""
        print("🚀 UDP CLIENT - Mã hóa đầu-cuối")
        print("🔐 Đã kết nối với server")
        print("-" * 50)
        print("📝 Hướng dẫn:")
        print("   • Nhập số nguyên > 0: Server sẽ lưu và cộng dồn")
        print("   • Nhập mã cổ phiếu: Server sẽ tra cứu giá")
        print("   • Nhập 0: Kết thúc và nhận tổng các số")
        print("-" * 50)
        
        while True:
            try:
                # Nhập dữ liệu từ bàn phím
                user_input = input("\n👤 Nhập dữ liệu: ").strip()
                
                if not user_input:
                    print("⚠️  Vui lòng nhập dữ liệu!")
                    continue
                
                # Gửi dữ liệu đến server
                print("📤 Đang gửi...")
                response = self.send_data(user_input)
                
                # Hiển thị phản hồi
                self.display_response(response)
                
                # Kiểm tra nếu là kết thúc phiên (nhập 0)
                try:
                    if int(user_input) == 0:
                        print("\n🔄 Bắt đầu phiên mới? (y/n)")
                        continue_choice = input("👤 Lựa chọn: ").strip().lower()
                        
                        if continue_choice not in ['y', 'yes', 'có']:
                            print("👋 Tạm biệt!")
                            break
                        else:
                            print("\n🆕 --- PHIÊN MỚI ---")
                            
                except ValueError:
                    # Không phải số - tiếp tục
                    pass
                    
            except KeyboardInterrupt:
                print("\n\n🔴 Đang thoát...")
                break
            except Exception as e:
                print(f"❌ Lỗi client: {e}")
        
        self.close()
    
    def close(self):
        """Đóng kết nối"""
        self.socket.close()
        print("✅ Đã đóng kết nối")

def main():
    """Hàm main"""
    client = UDPClient()
    client.run()

if __name__ == "__main__":
    main()

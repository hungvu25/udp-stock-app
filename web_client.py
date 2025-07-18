from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import socket
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import threading
import time
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebUDPClient:
    def __init__(self):
        self.server_host = 'localhost'
        self.server_port = 12345  # Sửa port để khớp với server
        self.password = "shared_secret_key"  # Password khớp với server
        self.sessions = {}  # Dictionary để lưu lịch sử cho mỗi session
        
    def create_session(self, session_id):
        """Tạo session mới"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'history': [],
                'created_at': time.time(),
                'last_activity': time.time()
            }
            
    def update_session_activity(self, session_id):
        """Cập nhật thời gian hoạt động cuối của session"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = time.time()
    
    def derive_key(self, password, salt):
        """Tạo khóa mã hóa từ password"""
        password_bytes = password.encode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key

    def encrypt_data(self, data):
        """Mã hóa dữ liệu"""
        salt = b'fixed_salt_12345'  # Salt khớp với server
        key = self.derive_key(self.password, salt)
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode('utf-8'))
        return encrypted_data

    def decrypt_data(self, encrypted_data):
        """Giải mã dữ liệu"""
        salt = b'fixed_salt_12345'  # Salt khớp với server  
        key = self.derive_key(self.password, salt)
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')

    def send_data(self, session_id, data):
        """Gửi dữ liệu đến UDP server với retry mechanism"""
        self.create_session(session_id)
        self.update_session_activity(session_id)
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            sock = None
            try:
                print(f"Attempt {attempt + 1}: Gửi dữ liệu '{data}' đến server...")
                
                # Tạo socket UDP
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(10)  # Timeout 10 giây
                
                # Mã hóa dữ liệu
                encrypted_data = self.encrypt_data(data)
                
                # Gửi dữ liệu
                sock.sendto(encrypted_data, (self.server_host, self.server_port))
                print(f"Đã gửi dữ liệu mã hóa ({len(encrypted_data)} bytes)")
                
                # Nhận phản hồi
                response_data, addr = sock.recvfrom(4096)
                print(f"Nhận phản hồi từ {addr} ({len(response_data)} bytes)")
                
                # Giải mã phản hồi
                decrypted_response = self.decrypt_data(response_data)
                
                # Lưu vào lịch sử session
                self.sessions[session_id]['history'].append({
                    'input': data,
                    'output': decrypted_response,
                    'timestamp': time.strftime('%H:%M:%S')
                })
                
                print(f"Kết quả: {decrypted_response}")
                return decrypted_response
                
            except socket.timeout:
                error_msg = f"Timeout khi gửi dữ liệu (attempt {attempt + 1})"
                print(error_msg)
                if attempt == max_retries - 1:
                    return f"❌ Lỗi: {error_msg}"
                    
            except ConnectionResetError as e:
                error_msg = f"Connection reset by server (attempt {attempt + 1}): {e}"
                print(error_msg)
                if attempt == max_retries - 1:
                    return f"❌ Lỗi: Server reset connection"
                    
            except Exception as e:
                error_msg = f"Lỗi giao tiếp (attempt {attempt + 1}): {e}"
                print(error_msg)
                if attempt == max_retries - 1:
                    return f"❌ Lỗi: {error_msg}"
                    
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
            
            # Đợi trước khi retry
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
        
        return "❌ Lỗi: Không thể kết nối đến server sau nhiều lần thử"

    def get_session_history(self, session_id):
        """Lấy lịch sử của session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['history']
        return []
    
    def get_session_info(self, session_id):
        """Lấy thông tin session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                'session_id': session_id,
                'created_at': time.strftime('%H:%M:%S', time.localtime(session['created_at'])),
                'last_activity': time.strftime('%H:%M:%S', time.localtime(session['last_activity'])),
                'total_requests': len(session['history'])
            }
        return None
    
    def clear_session_history(self, session_id):
        """Xóa lịch sử của session"""
        if session_id in self.sessions:
            self.sessions[session_id]['history'] = []
            
    def cleanup_old_sessions(self, max_age_hours=24):
        """Dọn dẹp session cũ"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_activity'] > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            
        return len(sessions_to_remove)

# Tạo instance WebUDPClient
web_client = WebUDPClient()

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Thử gửi ping đến server để kiểm tra kết nối
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        # Gửi ping message
        test_data = web_client.encrypt_data("ping")
        sock.sendto(test_data, (web_client.server_host, web_client.server_port))
        
        # Nhận phản hồi
        response_data, _ = sock.recvfrom(1024)
        response = web_client.decrypt_data(response_data)
        
        sock.close()
        
        return jsonify({
            'status': 'healthy',
            'server_response': response,
            'timestamp': time.strftime('%H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.strftime('%H:%M:%S')
        }), 500

@socketio.on('send_data')
def handle_send_data(data):
    """Xử lý gửi dữ liệu từ web client"""
    try:
        user_input = data.get('input', '').strip()
        session_id = data.get('session_id')
        
        if not session_id:
            # Tạo session ID mới nếu chưa có
            session_id = str(uuid.uuid4())
            emit('session_created', {'session_id': session_id})
        
        if not user_input:
            emit('response', {
                'type': 'error', 
                'data': 'Vui lòng nhập dữ liệu!',
                'timestamp': time.strftime('%H:%M:%S'),
                'session_id': session_id
            })
            return
        
        # Gửi dữ liệu đến UDP server
        response = web_client.send_data(session_id, user_input)
        
        # Gửi phản hồi về web client
        emit('response', {
            'input': user_input,
            'response': response,
            'timestamp': time.strftime('%H:%M:%S'),
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Lỗi handle_send_data: {e}")
        emit('response', {
            'type': 'error',
            'data': f'Lỗi server: {str(e)}',
            'timestamp': time.strftime('%H:%M:%S')
        })

@socketio.on('get_history')
def handle_get_history(data):
    """Lấy lịch sử phiên"""
    try:
        session_id = data.get('session_id')
        if session_id:
            history = web_client.get_session_history(session_id)
            session_info = web_client.get_session_info(session_id)
            emit('history', {
                'history': history,
                'session_info': session_info
            })
        else:
            emit('history', {'history': [], 'session_info': None})
    except Exception as e:
        print(f"Lỗi get_history: {e}")
        emit('error', {'message': f'Lỗi lấy lịch sử: {str(e)}'})

@socketio.on('clear_history')
def handle_clear_history(data):
    """Xóa lịch sử"""
    try:
        session_id = data.get('session_id')
        if session_id:
            web_client.clear_session_history(session_id)
            emit('history_cleared', {'session_id': session_id})
    except Exception as e:
        print(f"Lỗi clear_history: {e}")
        emit('error', {'message': f'Lỗi xóa lịch sử: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    """Khi client kết nối"""
    try:
        session_id = str(uuid.uuid4())
        web_client.create_session(session_id)
        print(f'Client đã kết nối - Session: {session_id}')
        emit('status', {'message': 'Đã kết nối đến server'})
        emit('session_created', {'session_id': session_id})
    except Exception as e:
        print(f"Lỗi connect: {e}")
        emit('error', {'message': f'Lỗi kết nối: {str(e)}'})

@socketio.on('disconnect')
def handle_disconnect():
    """Khi client ngắt kết nối"""
    print('Client đã ngắt kết nối')

@socketio.on_error_default
def default_error_handler(e):
    """Xử lý lỗi Socket.IO"""
    print(f'Socket.IO Error: {e}')
    emit('error', {'message': f'Lỗi Socket.IO: {str(e)}'})

@socketio.on_error()
def error_handler(e):
    """Xử lý lỗi chung"""
    print(f'Error: {e}')
    emit('error', {'message': f'Lỗi: {str(e)}'})

# Cleanup task chạy định kỳ
def cleanup_task():
    """Task dọn dẹp session cũ"""
    while True:
        try:
            cleaned = web_client.cleanup_old_sessions(max_age_hours=24)
            if cleaned > 0:
                print(f"Đã dọn dẹp {cleaned} session cũ")
        except Exception as e:
            print(f"Lỗi cleanup task: {e}")
        
        # Nghỉ 1 giờ trước khi dọn dẹp lần tiếp theo
        time.sleep(3600)

# Khởi động cleanup task trong background
cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    print("🌐 Web Client đang khởi động...")
    print("📡 Server: http://localhost:5000")
    print("🔗 Kết nối đến UDP Server: localhost:12345")
    print("=" * 50)
    
    # Chạy Flask-SocketIO app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

#!/usr/bin/env python3
"""
Khởi động cả UDP Server và Web Client trong cùng một process
Để deploy trên Railway
"""
import threading
import time
import os
import sys
import signal

# Import các class từ server và web_client
from server import UDPServer
from web_client import app, socketio, web_client

def start_udp_server():
    """Khởi động UDP Server trong thread riêng"""
    try:
        # Sử dụng cổng khác cho UDP server (Railway cung cấp PORT cho web)
        udp_port = int(os.environ.get('UDP_PORT', 12345))
        host = '0.0.0.0'
        
        print(f"🚀 Khởi động UDP Server tại {host}:{udp_port}")
        
        server = UDPServer(host=host, port=udp_port)
        server.start()
        
    except Exception as e:
        print(f"❌ Lỗi khởi động UDP Server: {e}")
        sys.exit(1)

def start_web_client():
    """Khởi động Web Client"""
    try:
        # Railway cung cấp PORT cho web service
        port = int(os.environ.get('PORT', 5000))
        host = '0.0.0.0'
        
        print(f"🌐 Khởi động Web Client tại {host}:{port}")
        
        # Cập nhật server_host trong web_client để kết nối đến UDP server
        web_client.server_host = '127.0.0.1'  # Localhost vì cùng container
        web_client.server_port = int(os.environ.get('UDP_PORT', 12345))
        
        # Chạy Flask-SocketIO app
        socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
        
    except Exception as e:
        print(f"❌ Lỗi khởi động Web Client: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    """Xử lý tín hiệu tắt ứng dụng"""
    print("\n🔴 Đang tắt ứng dụng...")
    sys.exit(0)

def main():
    """Hàm chính khởi động cả hai service"""
    print("=" * 60)
    print("🚀 KHỞI ĐỘNG ỨNG DỤNG UDP STOCK APP")
    print("=" * 60)
    
    # Đăng ký signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Khởi động UDP Server trong thread background
        udp_thread = threading.Thread(target=start_udp_server, daemon=True)
        udp_thread.start()
        
        # Đợi một chút để UDP server khởi động
        time.sleep(2)
        
        # Khởi động Web Client (main thread)
        start_web_client()
        
    except KeyboardInterrupt:
        print("\n🔴 Đã nhận tín hiệu tắt")
    except Exception as e:
        print(f"❌ Lỗi khởi động ứng dụng: {e}")
        sys.exit(1)
    finally:
        print("✅ Ứng dụng đã tắt")

if __name__ == "__main__":
    main()

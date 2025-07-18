import os

# Cấu hình API Keys
# Để sử dụng Finnhub API thực tế, hãy:
# 1. Đăng ký miễn phí tại: https://finnhub.io/register
# 2. Lấy API key và thay thế dưới đây
# 3. Gói miễn phí: 60 calls/minute

# Sử dụng biến môi trường hoặc fallback về API key mặc định
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', "d1sat51r01qskg7sjj5gd1sat51r01qskg7sjj60")

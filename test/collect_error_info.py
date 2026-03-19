def get_422_log(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    error_lines = [line for line in lines if '422' in line or 'ValidationError' in line]
    return ''.join(error_lines[-20:])  # lấy 20 dòng cuối liên quan

def get_request_log(request_log_path):
    with open(request_log_path, 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == "__main__":
    log_422 = get_422_log('logs/backend.log')
    request = get_request_log('logs/request.log')
    print("=== Backend log 422 ===\n", log_422)
    print("=== Request thực tế ===\n", request)

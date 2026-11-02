import threading
import collections
from server import ChatServer

_server_instance = None
_server_lock = threading.Lock()
_global_logs = collections.deque(maxlen=200)
_logs_lock = threading.Lock()

def add_server_log(log_obj):
    """Menyimpan log server ke deque global."""
    with _logs_lock:
        _global_logs.append(log_obj)

def get_server_logs():
    """Mengambil seluruh log server saat ini."""
    with _logs_lock:
        return list(_global_logs)

def clear_server_logs():
    """Mengosongkan log server."""
    with _logs_lock:
        _global_logs.clear()

def get_or_create_server(host='127.0.0.1', port=8080):
    """Mengambil instance server global atau membuat baru jika belum ada."""
    global _server_instance
    with _server_lock:
        if _server_instance is None:
            _server_instance = ChatServer(host=host, port=port, log_callback=add_server_log)
        return _server_instance

def start_global_server(host='127.0.0.1', port=8080):
    """Memulai server global di background thread."""
    global _server_instance
    with _server_lock:
        if _server_instance is None or not _server_instance.is_running:
            _server_instance = ChatServer(host=host, port=port, log_callback=add_server_log)
            _server_instance.start(block=False)
            return True, f"Server berhasil dijalankan di {host}:{port}"
        return False, f"Server sudah berjalan di {_server_instance.host}:{_server_instance.port}"

def stop_global_server():
    """Menghentikan server global."""
    global _server_instance
    with _server_lock:
        if _server_instance and _server_instance.is_running:
            _server_instance.stop()
            _server_instance = None
            return True, "Server berhasil dihentikan"
        return False, "Server tidak sedang berjalan"

def is_server_running():
    """Memeriksa apakah server sedang berjalan."""
    with _server_lock:
        return _server_instance is not None and _server_instance.is_running

def get_active_connection_pool():
    """Mengambil daftar koneksi aktif dari server global."""
    with _server_lock:
        if _server_instance and _server_instance.is_running:
            return _server_instance.get_connection_pool_info()
        return []

def get_total_packets():
    """Mengambil total paket pesan yang diproses server."""
    with _server_lock:
        if _server_instance:
            return _server_instance.total_packets
        return 0

def disconnect_client_from_server(ip, port):
    """Memutuskan koneksi socket klien langsung dari sisi server."""
    with _server_lock:
        if _server_instance and _server_instance.is_running:
            return _server_instance.disconnect_client_by_key(ip, port)
        return False

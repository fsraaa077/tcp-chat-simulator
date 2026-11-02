import socket
import threading
import datetime
import time

class ChatClient:
    """
    Klien Obrolan TCP Tingkat Rendah
    Menggunakan socket AF_INET SOCK_STREAM dan threading untuk menerima pesan
    secara real-time tanpa memblokir proses pengiriman pesan.
    """
    def __init__(self, host='127.0.0.1', port=8080, on_message_callback=None, on_disconnect_callback=None):
        self.host = host
        self.port = port
        self.on_message_callback = on_message_callback
        self.on_disconnect_callback = on_disconnect_callback
        
        self.sock = None
        self.is_connected = False
        self.receive_thread = None
        self.my_ip = None
        self.my_port = None
        self.messages = []
        self._lock = threading.Lock()

    def connect(self):
        """Membuka koneksi socket TCP ke server."""
        if self.is_connected:
            return True, f"Sudah terhubung sebagai {self.my_ip}:{self.my_port}"

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)

            self.my_ip, self.my_port = self.sock.getsockname()
            self.is_connected = True

            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            return True, f"Berhasil terhubung ke {self.host}:{self.port} (Socket: {self.my_ip}:{self.my_port})"
        except Exception as e:
            self.is_connected = False
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            return False, f"Gagal terhubung ke server: {e}"

    def _receive_loop(self):
        """Loop menerima pesan broadcast dari server secara kontinu."""
        buffer = ""
        while self.is_connected:
            try:
                data = self.sock.recv(2048)
                if not data:
                    break
                
                buffer += data.decode('utf-8', errors='replace')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    msg = line.strip()
                    if msg:
                        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]
                        msg_entry = {
                            "time": now,
                            "type": "system" if "*** SISTEM" in msg else "broadcast",
                            "raw": msg,
                            "formatted": f"[{now}] {msg}"
                        }
                        with self._lock:
                            self.messages.append(msg_entry)
                        if self.on_message_callback:
                            try:
                                self.on_message_callback(msg_entry)
                            except Exception:
                                pass
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, socket.error):
                break
            except Exception:
                break

        self.disconnect(suppress_callback=False)

    def send(self, message):
        """Mengirim pesan teks ke server melalui socket TCP."""
        if not self.is_connected or not self.sock:
            return False, "Tidak terhubung ke server."
        
        try:
            now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]
            raw_text = message.strip()
            payload = (raw_text + "\n").encode('utf-8')
            self.sock.sendall(payload)

            # Catat outgoing message ke riwayat klien lokal
            sent_entry = {
                "time": now,
                "type": "outgoing",
                "raw": raw_text,
                "formatted": f'[{now}] [SENT OUTGOING] -> Server: "{raw_text}"'
            }
            with self._lock:
                self.messages.append(sent_entry)

            return True, "Terkirim"
        except Exception as e:
            self.disconnect()
            return False, f"Gagal mengirim pesan: {e}"

    def disconnect(self, suppress_callback=False):
        """Memutuskan koneksi socket TCP secara bersih (Graceful Shutdown)."""
        if not self.is_connected and not self.sock:
            return

        self.is_connected = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        if not suppress_callback and self.on_disconnect_callback:
            try:
                self.on_disconnect_callback()
            except Exception:
                pass

    def get_messages(self):
        """Mengambil salinan riwayat pesan."""
        with self._lock:
            return list(self.messages)

    @property
    def identity(self):
        if self.my_ip and self.my_port:
            return f"{self.my_ip}:{self.my_port}"
        return "Belum Terhubung"

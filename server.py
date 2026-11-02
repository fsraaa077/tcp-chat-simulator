import socket
import threading
import datetime
import time
import sys

class ChatServer:
    """
    TCP Multi-Client Chat Server
    Implementasi berbasis protokol TCP menggunakan socket AF_INET & SOCK_STREAM
    dengan konkurensi multithreading dan connection pool.
    """
    def __init__(self, host='127.0.0.1', port=8080, log_callback=None):
        self.host = host
        self.port = port
        self.log_callback = log_callback
        self.server_socket = None
        self.is_running = False
        
        # Connection Pool: dictionary menyimpan metadata koneksi aktif
        # Format: {(ip, port): {"socket": sock, "fd": logical_fd, "connected_at": time_str, "client_num": num}}
        self.connection_pool = {}
        self.pool_lock = threading.Lock()
        self.accept_thread = None
        
        # Counter untuk Logical File Descriptor & Total Packets
        self.fd_counter = 4
        self.total_packets = 0
        self.client_seq = 0

    def log(self, event_type, message, raw_spec_message=None):
        """
        Mencatat log dengan tipe event terstruktur:
        event_type: 'INFO', 'CONNECT', 'RECV', 'BROADCAST', 'DISCONNECT', 'ERROR'
        """
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log konsol standar sesuai spesifikasi UTS
        console_line = f"[{timestamp}] {raw_spec_message if raw_spec_message else f'[{event_type}] {message}'}"
        print(console_line, flush=True)

        # Log visual terstruktur untuk antarmuka web
        if self.log_callback:
            try:
                self.log_callback({
                    "time": now,
                    "type": event_type,
                    "message": message,
                    "raw": console_line
                })
            except Exception:
                pass

    def start(self, block=False):
        """Menginisialisasi socket server dan mulai mendengarkan koneksi masuk."""
        if self.is_running:
            return

        candidate_ports = [self.port, 8081, 8888, 9000, 9999, 0] if self.port == 8080 else [self.port, 0]
        last_error = None

        for candidate in candidate_ports:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if hasattr(socket, 'SO_REUSEPORT'):
                    try:
                        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    except Exception:
                        pass
                
                self.server_socket.bind((self.host, candidate))
                self.server_socket.listen(10)
                
                # Ambil port yang berhasil di-bind (berguna jika fallback ke port lain)
                self.port = self.server_socket.getsockname()[1]
                self.is_running = True
                
                self.log("INFO", f"Socket Server diinisialisasi pada {self.host}:{self.port}")
                self.log("INFO", "Listening TCP Connections ... Max backlog queue: 10")

                if block:
                    self._accept_loop()
                else:
                    self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
                    self.accept_thread.start()
                return
            except OSError as e:
                last_error = e
                if self.server_socket:
                    try:
                        self.server_socket.close()
                    except Exception:
                        pass
                    self.server_socket = None
                continue
            except Exception as e:
                last_error = e
                self.stop()
                break

        self.log("ERROR", f"Gagal memulai server di {self.host}: {last_error}")
        self.stop()
        if block and last_error:
            raise last_error

    def _accept_loop(self):
        """Loop menerima koneksi baru dari klien (non-blocking ke klien lain)."""
        while self.is_running:
            try:
                client_socket, (client_ip, client_port) = self.server_socket.accept()
                
                with self.pool_lock:
                    self.client_seq += 1
                    client_num = self.client_seq
                    logical_fd = f"FD {self.fd_counter}"
                    self.fd_counter += 1
                    
                    connected_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]
                    self.connection_pool[(client_ip, client_port)] = {
                        "socket": client_socket,
                        "fd": logical_fd,
                        "client_num": client_num,
                        "connected_at": connected_time
                    }
                
                # Spesifikasi UTS: [CONNECTED] Klien terhubung dari IP:PORT
                spec_msg = f"[CONNECTED] Klien terhubung dari {client_ip}:{client_port}"
                sim_msg = f"Client {client_num} ({client_ip}:{client_port}) terhubung ke Socket {logical_fd}"
                self.log("CONNECT", sim_msg, raw_spec_message=spec_msg)

                # Thread terpisah untuk melayani read/write klien
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_ip, client_port, logical_fd, client_num),
                    daemon=True
                )
                client_thread.start()
            except (socket.error, OSError):
                break
            except Exception as e:
                if self.is_running:
                    self.log("ERROR", f"Error pada accept loop: {e}")

    def _handle_client(self, client_socket, client_ip, client_port, logical_fd, client_num):
        """Read/write loop untuk satu klien tertentu."""
        buffer = ""
        client_id = f"{client_ip}:{client_port}"

        try:
            while self.is_running:
                data = client_socket.recv(2048)
                if not data:
                    break
                
                buffer += data.decode('utf-8', errors='replace')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    raw_msg = line.strip()
                    if raw_msg:
                        with self.pool_lock:
                            self.total_packets += 1
                        
                        # Log RECV
                        self.log("RECV", f'recv() from {client_id} ({logical_fd}): "{raw_msg}"',
                                 raw_spec_message=f"[MESSAGE] Dari {client_id}: {raw_msg}")
                        
                        # Broadcast ke seluruh klien lain
                        broadcast_payload = f"[{client_id}]: {raw_msg}\n"
                        active_count = len(self.connection_pool) - 1
                        self.log("BROADCAST", f"Looping broadcast payload ke {active_count} socket aktif ...")
                        self._broadcast(broadcast_payload, sender_socket=client_socket)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, socket.error):
            pass
        except Exception as e:
            self.log("ERROR", f"Exception pada klien {client_id}: {e}")
        finally:
            self._handle_disconnect(client_socket, client_ip, client_port, logical_fd)

    def _handle_disconnect(self, client_socket, client_ip, client_port, logical_fd=None):
        """Menangani pemutusan koneksi klien secara responsif & graceful shutdown."""
        client_id = f"{client_ip}:{client_port}"
        
        with self.pool_lock:
            info = self.connection_pool.pop((client_ip, client_port), None)
            if info and not logical_fd:
                logical_fd = info.get("fd", "FD ?")

        try:
            client_socket.close()
        except Exception:
            pass

        # Spesifikasi UTS: [DISCONNECTED] Klien IP:PORT memutuskan koneksi
        spec_msg = f"[DISCONNECTED] Klien {client_id} memutuskan koneksi"
        sim_msg = f"Klien {client_id} ({logical_fd}) memutuskan koneksi"
        self.log("DISCONNECT", sim_msg, raw_spec_message=spec_msg)

        # Spesifikasi Broadcast Sistem
        system_notification = f"*** SISTEM: Klien {client_id} telah meninggalkan obrolan ***\n"
        self._broadcast(system_notification, sender_socket=None)

    def disconnect_client_by_key(self, ip, port):
        """Memutuskan klien secara manual dari server side (untuk tombol Disconnect pada Connection Pool)."""
        with self.pool_lock:
            info = self.connection_pool.get((ip, port))
            if info:
                sock = info["socket"]
                fd = info["fd"]
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
                # Trigger pembersihan
                threading.Thread(target=self._handle_disconnect, args=(sock, ip, port, fd), daemon=True).start()
                return True
        return False

    def _broadcast(self, message_str, sender_socket=None):
        """Meneruskan pesan ke seluruh klien aktif kecuali pengirim."""
        data = message_str.encode('utf-8')
        disconnected_clients = []

        with self.pool_lock:
            for client_key, info in list(self.connection_pool.items()):
                sock = info["socket"]
                if sender_socket is not None and sock == sender_socket:
                    continue

                try:
                    sock.sendall(data)
                except (socket.error, BrokenPipeError, ConnectionResetError):
                    disconnected_clients.append((client_key, info))

            for (key, info) in disconnected_clients:
                if key in self.connection_pool:
                    try:
                        info["socket"].close()
                    except Exception:
                        pass
                    del self.connection_pool[key]

    def get_connection_pool_info(self):
        """Mengembalikan daftar koneksi aktif dengan FD, IP, Port, dan Waktu."""
        with self.pool_lock:
            return [
                {
                    "fd": info["fd"],
                    "client_num": info["client_num"],
                    "ip": ip,
                    "port": port,
                    "connected_at": info["connected_at"],
                    "status": "ESTABLISHED"
                }
                for (ip, port), info in self.connection_pool.items()
            ]

    def stop(self):
        """Mematikan server socket."""
        self.is_running = False
        with self.pool_lock:
            for (ip, port), info in list(self.connection_pool.items()):
                try:
                    info["socket"].close()
                except Exception:
                    pass
            self.connection_pool.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        self.log("INFO", "Socket Server telah dimatikan.", raw_spec_message="[SERVER STOPPED] Server telah dimatikan.")

if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 8080
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    if len(sys.argv) > 2:
        HOST = sys.argv[2]

    print("=" * 65)
    print("      SERVER OBROLAN TCP MULTI-CLIENT")
    print("=" * 65)
    print(f"Inisialisasi: socket(AF_INET, SOCK_STREAM)")
    print(f"Bind        : {HOST}:{PORT}")
    print("Tekan Ctrl+C untuk mematikan server.")
    print("=" * 65)

    server = ChatServer(host=HOST, port=PORT)
    try:
        server.start(block=True)
    except KeyboardInterrupt:
        print("\n[INFO] Menutup server...")
        server.stop()

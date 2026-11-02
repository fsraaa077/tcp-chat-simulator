import socket
import threading
import sys
import time

def receive_messages(sock, my_identity):
    """Mendengarkan broadcast pesan dari server di thread terpisah."""
    buffer = ""
    while True:
        try:
            data = sock.recv(2048)
            if not data:
                print("\n[INFO] Koneksi terputus dari server.")
                break
            
            buffer += data.decode('utf-8', errors='replace')
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                message = line.strip()
                if message:
                    # Tampilkan pesan broadcast yang diterima
                    # Format yang diharapkan:
                    # [IP_KLIEN:PORT_KLIEN]: isi_pesan
                    # atau *** SISTEM: Klien ... telah meninggalkan obrolan ***
                    print(f"\r{message}\n[Anda] > ", end="", flush=True)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, socket.error):
            print("\n[INFO] Terputus dari server.")
            break
        except Exception:
            break
    
    try:
        sock.close()
    except Exception:
        pass
    print("\n[INFO] Program klien selesai. Tekan Enter untuk keluar.")
    sys.exit(0)

def main():
    HOST = '127.0.0.1'
    PORT = 8080

    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    if len(sys.argv) > 2:
        HOST = sys.argv[2]

    print("=" * 65)
    print("      KLIEN OBROLAN TCP")
    print("=" * 65)
    print(f"Menghubungkan ke server {HOST}:{PORT}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except Exception as e:
        print(f"[ERROR] Gagal terhubung ke {HOST}:{PORT}: {e}")
        print("Pastikan server sudah berjalan terlebih dahulu.")
        return

    my_ip, my_port = sock.getsockname()
    my_identity = f"{my_ip}:{my_port}"

    print(f"[*] Terhubung dengan sukses!")
    print(f"[*] Identitas Socket Klien Anda: {my_identity}")
    print(f"[*] Format Pesan Broadcast     : [IP:PORT]: isi_pesan")
    print(f"[*] Perintah: Ketik 'exit' atau tekan Ctrl+C untuk keluar")
    print("=" * 65)

    # Jalankan thread penerima pesan
    recv_thread = threading.Thread(target=receive_messages, args=(sock, my_identity), daemon=True)
    recv_thread.start()

    try:
        while True:
            msg = input("[Anda] > ")
            if not msg:
                continue
            if msg.strip().lower() == 'exit':
                print("[INFO] Mengirim sinyal keluar ke server...")
                break
            
            # Kirim pesan diakhiri newline \n
            payload = (msg.strip() + "\n").encode('utf-8')
            sock.sendall(payload)
    except KeyboardInterrupt:
        print("\n[INFO] Terdeteksi Ctrl+C (Pemutusan koneksi spontan)...")
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
        print(f"[INFO] Socket {my_identity} telah ditutup.")

if __name__ == "__main__":
    main()

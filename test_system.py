import time
from server import ChatServer
from tcp_client import ChatClient

def test_full_scenario():
    print("=== MULAI PENGUJIAN OTOMATIS ARSITEKTUR CHAT SERVER ===")
    logs = []
    def log_catcher(msg):
        logs.append(msg)

    server = ChatServer(host='127.0.0.1', port=9999, log_callback=log_catcher)
    server.start(block=False)
    time.sleep(0.5)

    print("\n--- UJI 1: Inisialisasi & 3 Klien Terhubung ---")
    c1 = ChatClient(host='127.0.0.1', port=9999)
    c2 = ChatClient(host='127.0.0.1', port=9999)
    c3 = ChatClient(host='127.0.0.1', port=9999)

    ok1, m1 = c1.connect()
    ok2, m2 = c2.connect()
    ok3, m3 = c3.connect()

    assert ok1 and ok2 and ok3, "Semua klien harus berhasil terhubung"
    print(f"Klien 1 terhubung: {c1.identity}")
    print(f"Klien 2 terhubung: {c2.identity}")
    print(f"Klien 3 terhubung: {c3.identity}")

    assert len({c1.my_port, c2.my_port, c3.my_port}) == 3, "Port socket setiap klien harus berbeda!"
    pool = server.get_connection_pool_info()
    assert len(pool) == 3, f"Connection pool harus berisi 3 klien, tapi berisi {len(pool)}"
    print(f"[PASSED] Uji 1 Berhasil: 3 klien aktif dengan socket identitas unik!")

    print("\n--- UJI 2: Broadcast Pesan Real-time ---")
    c1.send("Halo dari Klien 1!")
    time.sleep(0.5)

    raw_c2 = [m['raw'] for m in c2.get_messages()]
    raw_c3 = [m['raw'] for m in c3.get_messages()]
    expected_broadcast = f"[{c1.identity}]: Halo dari Klien 1!"
    print(f"Pesan di Klien 2: {raw_c2}")
    print(f"Pesan di Klien 3: {raw_c3}")

    assert expected_broadcast in raw_c2, f"Klien 2 harus menerima '{expected_broadcast}'"
    assert expected_broadcast in raw_c3, f"Klien 3 harus menerima '{expected_broadcast}'"
    print(f"[PASSED] Uji 2 Berhasil: Broadcast diterima presisi dengan format [IP:PORT]: pesan!")

    print("\n--- UJI 3: Disconnect & Recovery ---")
    c2_id = c2.identity
    print(f"Memutuskan Klien 2 ({c2_id}) secara tiba-tiba...")
    c2.disconnect()
    time.sleep(0.5)

    pool_after = server.get_connection_pool_info()
    assert len(pool_after) == 2, f"Connection pool harus berkurang menjadi 2, saat ini: {len(pool_after)}"
    print(f"Connection pool setelah Klien 2 keluar: {len(pool_after)} klien")

    expected_disconnect_broadcast = f"*** SISTEM: Klien {c2_id} telah meninggalkan obrolan ***"
    c1_raw = [m['raw'] for m in c1.get_messages()]
    c3_raw = [m['raw'] for m in c3.get_messages()]
    print(f"Pesan di Klien 1: {c1_raw[-1]}")
    print(f"Pesan di Klien 3: {c3_raw[-1]}")

    assert expected_disconnect_broadcast in c1_raw, "Klien 1 harus menerima notifikasi sistem disconnect"
    assert expected_disconnect_broadcast in c3_raw, "Klien 3 harus menerima notifikasi sistem disconnect"

    # Uji komunikasi klien tersisa
    print("Menguji pengiriman pesan antar klien tersisa (Klien 3 -> Klien 1)...")
    c3.send("Klien 3 masih online!")
    time.sleep(0.5)
    c1_raw_after = [m['raw'] for m in c1.get_messages()]
    assert f"[{c3.identity}]: Klien 3 masih online!" in c1_raw_after
    print("[PASSED] Uji 3 Berhasil: Klien tersisa tetap dapat berkomunikasi dengan normal!")

    c1.disconnect()
    c3.disconnect()
    server.stop()
    print("\n=== SEMUA SKENARIO PENGUJIAN 100% SUKSES DAN MEMENUHI SPESIFIKASI! ===")

if __name__ == "__main__":
    test_full_scenario()

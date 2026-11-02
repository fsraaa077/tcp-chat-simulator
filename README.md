# Proyek Praktikum: Sistem Obrolan TCP Multi-Client

Aplikasi server dan klien obrolan terpusat berbasis protokol **TCP (Transmission Control Protocol)** dengan pustaka socket tingkat rendah bawaan Python (`socket.AF_INET`, `socket.SOCK_STREAM`), model konkurensi **Multithreading**, serta antarmuka web berbasis **Streamlit**.

---

## Fitur & Kepatuhan Spesifikasi

1. **Dukungan Multi-Client (Non-Blocking)**:
   - Server mampu melayani lebih dari 3 klien secara simultan tanpa *blocking*.
   - Setiap klien dilayani dalam thread terpisah (`threading.Thread`) untuk operasi *read/write loop*.
2. **Logging Identitas Klien Presisi**:
   - Mencatat alamat IP dan nomor *port* setiap kali klien:
     - Terhubung: `[CONNECTED] Klien terhubung dari IP_KLIEN:PORT_KLIEN`
     - Mengirim pesan: `[MESSAGE] Dari IP_KLIEN:PORT_KLIEN: isi_pesan`
     - Terputus: `[DISCONNECTED] Klien IP_KLIEN:PORT_KLIEN memutuskan koneksi`
3. **Implementasi Broadcast Real-Time**:
   - Setiap pesan yang dikirim oleh satu klien diteruskan (*broadcast*) ke seluruh klien lain yang sedang aktif.
   - Format pesan yang diterima klien lain: `[IP_KLIEN:PORT_KLIEN]: isi_pesan`.
4. **Penanganan Disconnect & Graceful Recovery**:
   - Menangani pemutusan mendadak (misal: Ctrl+C atau penutupan jendela) tanpa membuat server mengalami *crash* atau *infinite loop*.
   - Menghapus socket klien dari *Connection Pool* secara *thread-safe*.
   - Mengirim notifikasi sistem ke klien lain: `*** SISTEM: Klien IP_KLIEN:PORT_KLIEN telah meninggalkan obrolan ***`.
5. **Antarmuka Web Bersih & Mudah Digunakan**:
   - Visualisasi Connection Pool secara real-time.
   - Simulator 3 Klien Simultan langsung di browser (Node A, Node B, Node C).
   - Konsol log server mencatat aktivitas socket.
   - Validasi otomatis untuk seluruh skenario pengujian.

---

## Struktur Berkas

```
proyek/
│
├── server.py             # Server Socket TCP murni tingkat rendah (multithreaded)
├── client.py             # Klien Socket TCP murni berbasis CLI (Terminal / CMD)
├── tcp_client.py         # Modul objek klien TCP (reusable class)
├── server_manager.py     # Pengelola siklus hidup server global & log
├── app.py                # Antarmuka Web (Streamlit)
├── run.py                # Skrip peluncur dari CMD (python run.py)
├── test_system.py        # Skrip otomatisasi pengujian unit & skenario
├── run_web.bat           # File batch untuk membuka Web Streamlit
├── run_server_cmd.bat    # File batch untuk menjalankan Server di CMD
├── run_client_cmd.bat    # File batch untuk menjalankan Klien di CMD
└── README.md             # Panduan dokumentasi teknis
```

---

## Cara Menjalankan Proyek

### Opsi A: Menjalankan Antarmuka Web (Rekomendasi)

Buka **Command Prompt (CMD)** di folder proyek, lalu jalankan:
```bash
python run.py
```
*atau:*
```bash
streamlit run app.py
```
Aplikasi web akan terbuka secara otomatis di browser pada alamat `http://localhost:8501`.

Fitur pada antarmuka web:
- **Tab 1 (Multi-Client Chat Arena):** Pengujian obrolan antar-klien dan pemutusan koneksi secara simultan.
- **Tab 2 (Server Monitor & Connection Pool):** Menampilkan daftar klien yang aktif di connection pool dan log konsol server secara real-time.
- **Tab 3 (Pengujian Skenario):** Validasi otomatis untuk skenario pengujian 1, 2, dan 3.
- **Tab 4 (Panduan Terminal CMD):** Panduan perintah konsol.

---

### Opsi B: Menjalankan via Terminal CMD (4 Jendela)

Anda dapat membuka 4 jendela CMD terpisah untuk menguji skenario terminal:

#### 1. Terminal 1 (Server):
```bash
python server.py 8080
```
Server mengikat socket ke `127.0.0.1:8080` dan mendengarkan koneksi masuk.

#### 2. Terminal 2 (Klien 1):
```bash
python client.py 8080
```

#### 3. Terminal 3 (Klien 2):
```bash
python client.py 8080
```

#### 4. Terminal 4 (Klien 3):
```bash
python client.py 8080
```

---

## Panduan Verifikasi Skenario Pengujian

### Skenario 1 (Inisialisasi & Multi-Client)
1. Jalankan `server.py` di Terminal 1.
2. Buka minimal 3 terminal terpisah dan jalankan `client.py` di masing-masing terminal.
3. **Hasil:** Konsol server mencetak log terhubung dengan nomor port berbeda untuk setiap klien:
   ```text
   [CONNECTED] Klien terhubung dari 127.0.0.1:53403
   [CONNECTED] Klien terhubung dari 127.0.0.1:53404
   [CONNECTED] Klien terhubung dari 127.0.0.1:53405
   ```

### Skenario 2 (Uji Broadcast Pesan)
1. Kirim pesan dari Terminal Klien 1:
   ```text
   [Anda] > Halo kawan-kawan!
   ```
2. **Hasil:** Terminal Klien 2 dan Klien 3 secara *real-time* menerima pesan dengan identitas pengirim:
   ```text
   [127.0.0.1:53403]: Halo kawan-kawan!
   ```

### Skenario 3 (Uji Disconnect & Recovery)
1. Tutup terminal Klien 2 secara mendadak dengan menekan `Ctrl+C`.
2. **Hasil:**
   - Server tidak crash, dan mencetak:
     ```text
     [DISCONNECTED] Klien 127.0.0.1:53404 memutuskan koneksi
     ```
   - Connection pool diperbarui (berkurang dari 3 menjadi 2).
   - Klien 1 dan Klien 3 menerima notifikasi sistem:
     ```text
     *** SISTEM: Klien 127.0.0.1:53404 telah meninggalkan obrolan ***
     ```
   - Klien 1 dan Klien 3 tetap dapat saling berkirim pesan secara normal.

---

## Rincian Arsitektur Teknis

- **Pustaka Socket:** `import socket`
- **Tipe Domain:** `socket.AF_INET` (IPv4)
- **Tipe Protokol:** `socket.SOCK_STREAM` (TCP berorientasi koneksi)
- **Model Konkurensi:** `threading.Thread(target=_handle_client, daemon=True)`
- **Connection Pool:** Struktur data dictionary yang diproteksi lock (`threading.Lock()`) untuk mencegah *race condition* saat banyak thread mengakses pool secara bersamaan.

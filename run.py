import sys
import subprocess
import os

def main():
    print("=" * 70)
    print("   SISTEM OBROLAN TCP MULTI-CLIENT")
    print("=" * 70)
    print(" [*] Inisialisasi Lingkungan Python...")
    print(" [*] Membuka Antarmuka Web...")
    print("=" * 70)
    print(" Catatan Pengujian:")
    print(" - Server TCP dan Klien dapat diuji langsung dari antarmuka Web.")
    print(" - Anda juga dapat membuka CMD baru lalu jalankan 'python client.py'!")
    print("=" * 70)
    print(" Memulai Streamlit server... Tekan Ctrl+C untuk berhenti.\n")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")

    try:
        # Menjalankan streamlit run app.py
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], check=True)
    except KeyboardInterrupt:
        print("\n[INFO] Aplikasi dimatikan dengan aman. Sampai jumpa!")
    except Exception as e:
        print(f"\n[ERROR] Gagal menjalankan Streamlit: {e}")
        print("Coba jalankan secara manual menggunakan perintah: streamlit run app.py")

if __name__ == "__main__":
    main()

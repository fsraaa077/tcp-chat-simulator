import streamlit as st
import time
import datetime
import html
from server_manager import (
    start_global_server,
    stop_global_server,
    is_server_running,
    get_active_connection_pool,
    get_server_logs,
    clear_server_logs
)
from tcp_client import ChatClient

# ==============================================================================
# KONFIGURASI HALAMAN
# ==============================================================================
st.set_page_config(
    page_title="Sistem Obrolan TCP Multi-Client",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CSS BERSIH, FORMAL, DAN PROFESIONAL (TANPA AKSEN AI)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Header Formal */
    .app-header {
        background: #0f172a;
        color: #f8fafc;
        padding: 20px 24px;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #1e293b;
    }
    .app-header h1 {
        margin: 0;
        font-size: 21px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.2px;
    }
    .app-header p {
        margin: 6px 0 0 0;
        font-size: 13px;
        color: #94a3b8;
    }

    /* Status Label */
    .badge-online {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-offline {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }

    /* Client Card */
    .client-card {
        background-color: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 14px;
    }
    .client-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        padding-bottom: 8px;
        margin-bottom: 10px;
    }
    .client-title {
        font-weight: 600;
        font-size: 14px;
        color: var(--text-color, #0f172a);
    }
    .socket-info {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #0284c7;
        background: rgba(2, 132, 199, 0.08);
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
    }

    /* Chat Area */
    .chat-box {
        background-color: var(--background-color, #f8fafc);
        border: 1px solid rgba(203, 213, 225, 0.8);
        border-radius: 6px;
        padding: 10px;
        height: 250px;
        overflow-y: auto;
        font-size: 12px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .msg-item {
        padding: 6px 10px;
        border-radius: 4px;
        word-break: break-word;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11.5px;
        line-height: 1.4;
    }
    .msg-system {
        background-color: #fee2e2;
        color: #991b1b;
        border-left: 3px solid #ef4444;
        font-style: italic;
    }
    .msg-broadcast {
        background-color: #e0f2fe;
        color: #0369a1;
        border-left: 3px solid #0284c7;
    }
    .msg-own {
        background-color: #f0fdf4;
        color: #166534;
        border-left: 3px solid #22c55e;
        align-self: flex-end;
        max-width: 90%;
    }

    /* Terminal Console */
    .terminal-box {
        background-color: #090d16;
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        padding: 14px;
        border-radius: 6px;
        border: 1px solid #1e293b;
        height: 340px;
        overflow-y: auto;
        white-space: pre-wrap;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# INISIALISASI SESSION STATE
# ==============================================================================
if "server_host" not in st.session_state:
    st.session_state.server_host = "127.0.0.1"
if "server_port" not in st.session_state:
    st.session_state.server_port = 8080

if "clients" not in st.session_state:
    st.session_state.clients = {1: None, 2: None, 3: None}
if "client_history" not in st.session_state:
    st.session_state.client_history = {1: [], 2: [], 3: []}

if not is_server_running():
    start_global_server(st.session_state.server_host, st.session_state.server_port)

# ==============================================================================
# SIDEBAR KONTROL SERVER
# ==============================================================================
with st.sidebar:
    st.subheader("Konfigurasi Server")
    server_online = is_server_running()

    if server_online:
        st.markdown('<span class="badge-online">Server Aktif (TCP)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-offline">Server Nonaktif</span>', unsafe_allow_html=True)

    st.markdown("---")
    host_input = st.text_input("Server Host", value=st.session_state.server_host, disabled=server_online)
    port_input = st.number_input("Server Port", value=st.session_state.server_port, min_value=1024, max_value=65535, disabled=server_online)

    st.session_state.server_host = host_input
    st.session_state.server_port = int(port_input)

    c_s1, c_s2 = st.columns(2)
    with c_s1:
        if st.button("Mulai Server", use_container_width=True, disabled=server_online):
            ok, msg = start_global_server(st.session_state.server_host, st.session_state.server_port)
            if ok:
                st.success(msg)
            st.rerun()

    with c_s2:
        if st.button("Hentikan", use_container_width=True, disabled=not server_online):
            for cid in [1, 2, 3]:
                if st.session_state.clients[cid]:
                    st.session_state.clients[cid].disconnect()
                    st.session_state.clients[cid] = None
            stop_global_server()
            st.rerun()

    st.markdown("---")
    st.markdown("##### Spesifikasi Socket")
    st.markdown("""
    - **Protokol:** TCP (`SOCK_STREAM`)
    - **Domain:** `AF_INET` (IPv4)
    - **Konkurensi:** Multithreading
    - **Connection Pool:** Dictionary
    - **Broadcast:** Non-blocking
    """)

    st.markdown("---")
    if st.button("Bersihkan Log Konsol", use_container_width=True):
        clear_server_logs()
        st.rerun()

# ==============================================================================
# HEADER UTAMA
# ==============================================================================
st.markdown("""
<div class="app-header">
    <h1>Sistem Obrolan TCP Multi-Client</h1>
    <p>Praktikum Komunikasi Data & Arsitektur Jaringan — Server Socket Terpusat & Klien Multithreaded</p>
</div>
""", unsafe_allow_html=True)

tab_chat, tab_monitor, tab_test, tab_guide = st.tabs([
    "Multi-Client Chat Arena",
    "Server Monitor & Connection Pool",
    "Pengujian Skenario",
    "Panduan Terminal CMD"
])

# ==============================================================================
# HELPER KONEKSI KLIEN
# ==============================================================================
def connect_client(cid):
    if not is_server_running():
        st.toast("Server belum aktif. Silakan mulai server di sidebar.")
        return
    client = ChatClient(host=st.session_state.server_host, port=st.session_state.server_port)
    ok, msg = client.connect()
    if ok:
        st.session_state.clients[cid] = client
        st.toast(f"Klien {cid} terhubung: {client.identity}")
    else:
        st.toast(f"Gagal menghubungkan Klien {cid}: {msg}")

def disconnect_client(cid):
    client = st.session_state.clients.get(cid)
    if client:
        client.disconnect()
        st.session_state.clients[cid] = None
        st.toast(f"Klien {cid} telah memutuskan koneksi.")

def send_message(cid, text):
    client = st.session_state.clients.get(cid)
    if client and client.is_connected:
        client.send(text)
        my_id = client.identity
        st.session_state.client_history[cid].append({
            "type": "own",
            "content": f"[Anda ({my_id})]: {text}"
        })
    else:
        st.toast(f"Klien {cid} tidak terhubung.")

# ==============================================================================
# TAB 1: MULTI-CLIENT CHAT ARENA
# ==============================================================================
with tab_chat:
    st.caption("Menjalankan 3 instans klien socket TCP secara simultan. Setiap klien memiliki alamat port unik dari sistem operasi.")

    col_act1, col_act2, _ = st.columns([1.2, 1.2, 3])
    with col_act1:
        if st.button("Hubungkan Semua Klien", use_container_width=True):
            for cid in [1, 2, 3]:
                if not st.session_state.clients[cid] or not st.session_state.clients[cid].is_connected:
                    connect_client(cid)
            st.rerun()

    with col_act2:
        if st.button("Putuskan Semua Klien", use_container_width=True):
            for cid in [1, 2, 3]:
                if st.session_state.clients[cid]:
                    disconnect_client(cid)
            st.rerun()

    @st.fragment(run_every="1s")
    def render_chat_arena():
        cols = st.columns(3)
        client_titles = ["Klien 1 (Node A)", "Klien 2 (Node B)", "Klien 3 (Node C)"]

        for idx, col in enumerate(cols):
            cid = idx + 1
            client = st.session_state.clients.get(cid)
            is_conn = client is not None and client.is_connected
            identity = client.identity if is_conn else "Terputus"

            with col:
                st.markdown(f"""
                <div class="client-card">
                    <div class="client-header">
                        <span class="client-title">{client_titles[idx]}</span>
                        {f'<span class="badge-online">Terhubung</span>' if is_conn else '<span class="badge-offline">Terputus</span>'}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="font-size: 11px; color: #64748b;">Socket Identity:</span>
                        <span class="socket-info">{identity}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                b1, b2 = st.columns(2)
                with b1:
                    if not is_conn:
                        if st.button("Hubungkan", key=f"btn_con_{cid}", use_container_width=True):
                            connect_client(cid)
                            st.rerun()
                    else:
                        if st.button("Putuskan", key=f"btn_dis_{cid}", use_container_width=True):
                            disconnect_client(cid)
                            st.rerun()
                with b2:
                    if st.button("Hapus Chat", key=f"btn_clr_{cid}", use_container_width=True):
                        st.session_state.client_history[cid].clear()
                        if client:
                            with client._lock:
                                client.messages.clear()
                        st.rerun()

                chat_html = '<div class="chat-box">'
                
                if client:
                    incoming = client.get_messages()
                    recorded_msgs = [h["content"] for h in st.session_state.client_history[cid] if h["type"] != "own"]
                    for inc in incoming:
                        raw_text = inc.get("raw", "") if isinstance(inc, dict) else str(inc)
                        if raw_text and raw_text not in recorded_msgs:
                            m_type = "system" if "*** SISTEM" in raw_text else "broadcast"
                            st.session_state.client_history[cid].append({
                                "type": m_type,
                                "content": raw_text
                            })

                if not st.session_state.client_history[cid]:
                    chat_html += '<div style="color: #94a3b8; text-align: center; margin-top: 90px; font-size: 11.5px;">Belum ada pesan.</div>'
                else:
                    for item in st.session_state.client_history[cid]:
                        m_type = item["type"]
                        safe_text = html.escape(item["content"])
                        if m_type == "system":
                            chat_html += f'<div class="msg-item msg-system">{safe_text}</div>'
                        elif m_type == "own":
                            chat_html += f'<div class="msg-item msg-own">{safe_text}</div>'
                        else:
                            chat_html += f'<div class="msg-item msg-broadcast">{safe_text}</div>'

                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)

                with st.form(key=f"form_client_{cid}", clear_on_submit=True):
                    msg_text = st.text_input(
                        f"Pesan Klien {cid}",
                        placeholder="Ketik pesan broadcast...",
                        label_visibility="collapsed",
                        disabled=not is_conn
                    )
                    submit = st.form_submit_button("Kirim Pesan", use_container_width=True, disabled=not is_conn)
                    if submit and msg_text:
                        send_message(cid, msg_text)
                        st.rerun()

                cp1, cp2, cp3 = st.columns(3)
                with cp1:
                    if st.button('"Halo kawan!"', key=f"qc1_{cid}", use_container_width=True, disabled=not is_conn):
                        send_message(cid, "Halo kawan!")
                        st.rerun()
                with cp2:
                    if st.button('"Ping test"', key=f"qc2_{cid}", use_container_width=True, disabled=not is_conn):
                        send_message(cid, "Ping test")
                        st.rerun()
                with cp3:
                    if st.button('"Praktikum OK"', key=f"qc3_{cid}", use_container_width=True, disabled=not is_conn):
                        send_message(cid, "Praktikum OK")
                        st.rerun()

    render_chat_arena()

# ==============================================================================
# TAB 2: SERVER MONITOR & CONNECTION POOL
# ==============================================================================
with tab_monitor:
    st.subheader("Monitoring Socket Server & Connection Pool")

    @st.fragment(run_every="1s")
    def render_server_monitor():
        pool = get_active_connection_pool()
        logs = get_server_logs()
        online = is_server_running()

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Status Server", "ONLINE (TCP)" if online else "OFFLINE")
        with m2:
            st.metric("Klien Terhubung", f"{len(pool)} Klien")
        with m3:
            st.metric("Binding Address", f"{st.session_state.server_host}:{st.session_state.server_port}")
        with m4:
            st.metric("Konkurensi", "Multithreading")

        st.markdown("---")
        col_pool, col_log = st.columns([1, 1.25])

        with col_pool:
            st.markdown("##### Connection Pool Aktif")
            st.caption("Struktur data dictionary yang menyimpan daftar socket klien yang sedang terhubung:")

            if not pool:
                st.info("Saat ini belum ada klien yang terhubung ke server.")
            else:
                table_md = "| No | Socket FD | Alamat IP | Nomor Port | Waktu Terhubung | Status |\n|---|---|---|---|---|---|\n"
                for idx, c in enumerate(pool, start=1):
                    table_md += f"| {idx} | `{c.get('fd', f'FD {3+idx}')}` | `{c['ip']}` | **`{c['port']}`** | {c['connected_at']} | Aktif |\n"
                st.markdown(table_md)

        with col_log:
            st.markdown("##### Log Aktivitas Server Real-Time")
            st.caption("Pencatatan aktivitas koneksi server:")
            
            raw_lines = []
            for l in logs:
                if isinstance(l, dict):
                    raw_lines.append(l.get("raw", f"[{l.get('time')}] [{l.get('type')}] {l.get('message')}"))
                else:
                    raw_lines.append(str(l))

            log_text = "\n".join(raw_lines) if raw_lines else "[Menunggu aktivitas koneksi pada socket server]"
            safe_log = html.escape(log_text)
            st.markdown(f'<div class="terminal-box">{safe_log}</div>', unsafe_allow_html=True)

    render_server_monitor()

# ==============================================================================
# TAB 3: PENGUJIAN SKENARIO
# ==============================================================================
with tab_test:
    st.subheader("Verifikasi Skenario Pengujian Praktikum")
    st.caption("Validasi teknis untuk 3 skenario pengujian socket TCP.")

    col_t1, col_t2 = st.columns([1.2, 1])

    with col_t1:
        st.markdown("##### Skenario 1: Inisialisasi & Multi-Client")
        st.markdown("""
        - **Kriteria:** Server menerima minimal 3 klien secara simultan tanpa blocking.
        - **Log Server:** `[CONNECTED] Klien terhubung dari IP_KLIEN:PORT_KLIEN` dengan nomor port unik.
        """)

        st.markdown("##### Skenario 2: Uji Broadcast Pesan")
        st.markdown("""
        - **Kriteria:** Pesan dari satu klien diteruskan ke seluruh klien aktif lainnya.
        - **Format Pesan:** `[IP_KLIEN:PORT_KLIEN]: isi_pesan`
        """)

        st.markdown("##### Skenario 3: Uji Disconnect & Recovery")
        st.markdown("""
        - **Kriteria:** Penanganan pemutusan koneksi tanpa crash.
        - **Log Server:** `[DISCONNECTED] Klien IP_KLIEN:PORT_KLIEN memutuskan koneksi`
        - **Notifikasi Sistem:** `*** SISTEM: Klien IP_KLIEN:PORT_KLIEN telah meninggalkan obrolan ***`
        """)

    with col_t2:
        st.markdown("##### Eksekusi Pengujian Otomatis")
        st.caption("Menjalankan rangkaian pengujian socket end-to-end:")

        if st.button("Jalankan Pengujian (Skenario 1, 2, 3)", type="primary", use_container_width=True):
            test_progress = st.empty()
            test_results = st.container()

            with test_progress:
                st.info("Menjalankan pengujian socket TCP...")

            test_host = st.session_state.server_host
            test_port = st.session_state.server_port

            try:
                tc1 = ChatClient(host=test_host, port=test_port)
                tc2 = ChatClient(host=test_host, port=test_port)
                tc3 = ChatClient(host=test_host, port=test_port)

                ok1, _ = tc1.connect()
                ok2, _ = tc2.connect()
                ok3, _ = tc3.connect()
                time.sleep(0.3)

                ports_distinct = len({tc1.my_port, tc2.my_port, tc3.my_port}) == 3

                tc1.send("Pesan Uji Broadcast")
                time.sleep(0.4)
                expected_bcast = f"[{tc1.identity}]: Pesan Uji Broadcast"
                m2 = [m['raw'] if isinstance(m, dict) else m for m in tc2.get_messages()]
                m3 = [m['raw'] if isinstance(m, dict) else m for m in tc3.get_messages()]
                bcast_success = expected_bcast in m2 and expected_bcast in m3

                tc2_id = tc2.identity
                tc2.disconnect()
                time.sleep(0.4)
                expected_disc = f"*** SISTEM: Klien {tc2_id} telah meninggalkan obrolan ***"
                c1_msgs = [m['raw'] if isinstance(m, dict) else m for m in tc1.get_messages()]
                c3_msgs = [m['raw'] if isinstance(m, dict) else m for m in tc3.get_messages()]
                disc_c1 = expected_disc in c1_msgs
                disc_c3 = expected_disc in c3_msgs

                tc3.send("Klien 3 masih aktif")
                time.sleep(0.3)
                c1_msgs_after = [m['raw'] if isinstance(m, dict) else m for m in tc1.get_messages()]
                recovery_success = f"[{tc3.identity}]: Klien 3 masih aktif" in c1_msgs_after

                tc1.disconnect()
                tc3.disconnect()

                test_progress.empty()

                with test_results:
                    st.success("Rangkaian pengujian selesai dieksekusi.")
                    st.markdown(f"""
                    - **Pengujian 1 (Multi-Client):** {'LULUS (3 Klien terhubung, port unik)' if (ok1 and ok2 and ok3 and ports_distinct) else 'GAGAL'}
                    - **Pengujian 2 (Broadcast):** {'LULUS (Format [IP:PORT]: pesan presisi)' if bcast_success else 'GAGAL'}
                    - **Pengujian 3 (Graceful Disconnect):** {'LULUS (Notifikasi sistem & recovery berhasil)' if (disc_c1 and disc_c3 and recovery_success) else 'GAGAL'}
                    """)
            except Exception as e:
                test_progress.empty()
                st.error(f"Terjadi kesalahan saat pengujian: {e}")

# ==============================================================================
# TAB 4: PANDUAN RUNNING TERMINAL CMD
# ==============================================================================
with tab_guide:
    st.subheader("Panduan Eksekusi Terminal CMD")
    st.caption("Menjalankan server dan klien murni menggunakan konsol CMD / PowerShell:")

    c_g1, c_g2 = st.columns(2)

    with c_g1:
        st.markdown("##### 1. Menjalankan Server TCP di CMD")
        st.code("""# Jendela Terminal 1
python server.py 8080
""", language="bash")
        st.caption("Server melakukan bind ke 127.0.0.1:8080 dan mendengarkan koneksi masuk.")

        st.markdown("##### 2. Menjalankan Klien di 3 Terminal Terpisah")
        st.code("""# Jendela Terminal 2 (Klien 1)
python client.py 8080

# Jendela Terminal 3 (Klien 2)
python client.py 8080

# Jendela Terminal 4 (Klien 3)
python client.py 8080
""", language="bash")
        st.caption("Setiap klien mendapatkan nomor port unik dan dapat berkirim pesan secara real-time.")

    with c_g2:
        st.markdown("##### 3. Menjalankan Antarmuka Web")
        st.code("""# Terminal CMD
python run.py
# atau
streamlit run app.py
""", language="bash")

        st.markdown("##### Struktur Berkas Proyek")
        st.code("""proyek/
├── server.py           # Socket Server TCP low-level
├── client.py           # Klien Socket TCP CLI
├── tcp_client.py       # Modul klien socket OOP
├── server_manager.py   # Pengelola instance server & log
├── app.py              # Antarmuka Web Streamlit
├── run.py              # Script peluncur
├── test_system.py      # Script otomatisasi pengujian
└── README.md           # Dokumentasi teknis
""", language="text")

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #94a3b8; font-size: 12px;'>"
    "Sistem Obrolan TCP Multi-Client • Python Socket & Streamlit"
    "</div>",
    unsafe_allow_html=True
)

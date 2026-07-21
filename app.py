import os
import json
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, time, timedelta, timezone

# --- KUNCI JALUR FOLDER TEMPLATES UNTUK VERCEL ---
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'kunci_rahasia_untuk_sesi'

# Data user
users = {
    'karyawan1': 'password123',
    'karyawan2': 'password123'
}

# --- FUNGSI MENGHUBUNGKAN KE GOOGLE SHEETS ---
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    kunci_rahasia = os.environ.get('GOOGLE_CREDENTIALS')
    if not kunci_rahasia:
        raise Exception("Kunci rahasia GOOGLE_CREDENTIALS belum dipasang di Vercel!")
    
    creds_dict = json.loads(kunci_rahasia)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    return client.open("Data Absensi Karyawan").sheet1

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Username atau Password salah!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    pesan_sukses = None
    pesan_error = None
    
    if request.method == 'POST':
        wib = timezone(timedelta(hours=7))
        waktu_sekarang = datetime.now(wib)
        jam_sekarang = waktu_sekarang.time()
        waktu_str = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
        
        jenis_absen = request.form['jenis_absen']
        alasan = request.form.get('alasan', '').strip()  # Mengambil alasan dari form
        status_absen = "Tepat Waktu"
        
        batas_awal_masuk = time(6, 0)
        batas_akhir_masuk = time(7, 0)
        batas_awal_keluar = time(13, 0)
        batas_akhir_keluar = time(17, 0)

        # Cek Jam Absen
        if jenis_absen == 'Masuk':
            if jam_sekarang < batas_awal_masuk:
                pesan_error = "Belum waktunya absen masuk."
            elif jam_sekarang > batas_akhir_masuk:
                status_absen = "Terlambat"
                
                # SAKLAR VALIDASI ALASAN:
                # Jika jam > 07.00 DAN kolom alasan kosong -> DITOLAK
                if not alasan:
                    pesan_error = "Anda terlambat! Wajib mengisi kolom alasan keterlambatan sebelum absen."
                else:
                    pesan_sukses = f"Absen Masuk (Terlambat) berhasil dicatat pada {waktu_str}"
            else:
                pesan_sukses = f"Absen Masuk dicatat pada {waktu_str}"
                
        elif jenis_absen == 'Keluar':
            if jam_sekarang < batas_awal_keluar:
                pesan_error = "Belum waktunya absen keluar."
            elif jam_sekarang > batas_akhir_keluar:
                pesan_error = "Waktu absen keluar sudah habis."
            else:
                pesan_sukses = f"Absen Keluar dicatat pada {waktu_str}"

        # Jika lolos validasi (tidak ada error), simpan ke Google Sheets
        if not pesan_error:
            try:
                sheet = get_sheet()
                # Jika tepat waktu / keluar, alasan diisi tanda min (-)
                alasan_final = alasan if (jenis_absen == 'Masuk' and status_absen == 'Terlambat') else "-"
                
                # Simpan 5 data: [Waktu, Username, Jenis, Status, Alasan]
                sheet.append_row([waktu_str, username, jenis_absen, status_absen, alasan_final])
            except Exception as e:
                pesan_error = f"Gagal menyimpan ke spreadsheet: Cek Vercel Logs."
                pesan_sukses = None
                
    return render_template('dashboard.html', username=username, pesan_sukses=pesan_sukses, pesan_error=pesan_error)

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, time, timedelta, timezone # Tambahkan timedelta dan timezone

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_untuk_sesi'

# Data dummy akun karyawan Anda
users = {'Biyan': '66666', 'Pammy': '77777', 'Fakhri': '88888', 'Tommy': '99999', 'Azzam': '00000'}
absen_data = []

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
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
            error = 'Username atau password salah!'
            
    return render_template('login.html', error=error)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    pesan_sukses = None
    pesan_error = None
    
    if request.method == 'POST':
        # --- KODE BARU UNTUK MENGUNCI ZONA WAKTU WIB ---
        wib = timezone(timedelta(hours=7)) # Mengatur waktu ke UTC+7 (WIB)
        waktu_sekarang = datetime.now(wib)
        jam_sekarang = waktu_sekarang.time()
        waktu_str = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
        # -----------------------------------------------

        jenis_absen = request.form['jenis_absen']
        
        batas_awal_masuk = time(6, 0)
        batas_akhir_masuk = time(8, 0)
        batas_awal_keluar = time(6, 0)
        batas_akhir_keluar = time(8, 0)

        # Validasi Jam Absen Masuk
        if jenis_absen == 'Masuk':
            if batas_awal_masuk <= jam_sekarang <= batas_akhir_masuk:
                absen_data.append({'nama': username, 'waktu': waktu_str, 'jenis': jenis_absen})
                pesan_sukses = f"Berhasil absen MASUK pada {waktu_str}"
            else:
                pesan_error = "Gagal! Absen MASUK hanya diperbolehkan pukul 06:00 - 07:00."

        # Validasi Jam Absen Keluar
        elif jenis_absen == 'Keluar':
            if batas_awal_keluar <= jam_sekarang <= batas_akhir_keluar:
                absen_data.append({'nama': username, 'waktu': waktu_str, 'jenis': jenis_absen})
                pesan_sukses = f"Berhasil absen KELUAR pada {waktu_str}"
            else:
                pesan_error = "Gagal! Absen KELUAR hanya diperbolehkan pukul 13:00 - 17:00."
        
    riwayat_user = [data for data in absen_data if data['nama'] == username]
    
    return render_template('dashboard.html', 
                           username=username, 
                           pesan_sukses=pesan_sukses, 
                           pesan_error=pesan_error, 
                           riwayat=riwayat_user)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
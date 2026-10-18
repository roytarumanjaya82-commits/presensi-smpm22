from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import mysql.connector
from datetime import datetime
import calendar
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = "smpm22_pamulang_secret"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="db_presensi_smpm22"
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM kelas ORDER BY nama_kelas ASC")
    daftar_kelas = cursor.fetchall()
    conn.close()
    return render_template('index.html', kelas_list=daftar_kelas)

# Form Input Presensi Harian Guru Piket
@app.route('/presensi', methods=['GET', 'POST'])
def input_presensi():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    selected_kelas = request.args.get('kelas_id')
    selected_tanggal = request.args.get('tanggal', datetime.now().strftime('%Y-%m-%d'))
    
    if request.method == 'POST':
        selected_kelas = request.form.get('kelas_id')
        selected_tanggal = request.form.get('tanggal')
        
        cursor.execute("SELECT id FROM siswa WHERE kelas_id = %s", (selected_kelas,))
        siswa_list = cursor.fetchall()
        
        for siswa in siswa_list:
            status = request.form.get(f'status_{siswa["id"]}', 'Hadir')
            keterangan = request.form.get(f'ket_{siswa["id"]}', '')
            
            cursor.execute("""
                INSERT INTO presensi (siswa_id, tanggal, status, keterangan)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status), keterangan = VALUES(keterangan)
            """, (siswa['id'], selected_tanggal, status, keterangan))
            
        conn.commit()
        flash('Data presensi berhasil disimpan!', 'success')
        return redirect(url_for('input_presensi', kelas_id=selected_kelas, tanggal=selected_tanggal))

    cursor.execute("SELECT * FROM kelas ORDER BY nama_kelas ASC")
    daftar_kelas = cursor.fetchall()
    
    siswa_presensi = []
    if selected_kelas:
        cursor.execute("""
            SELECT s.id, s.nis, s.nama, s.jenis_kelamin, 
                   COALESCE(p.status, 'Hadir') as status, 
                   COALESCE(p.keterangan, '') as keterangan
            FROM siswa s
            LEFT JOIN presensi p ON s.id = p.siswa_id AND p.tanggal = %s
            WHERE s.kelas_id = %s
            ORDER BY s.nama ASC
        """, (selected_tanggal, selected_kelas))
        siswa_presensi = cursor.fetchall()
        
    conn.close()
    return render_template('presensi.html', kelas_list=daftar_kelas, siswa_list=siswa_presensi, 
                           selected_kelas=selected_kelas, selected_tanggal=selected_tanggal)

# Laporan Harian
@app.route('/laporan-harian')
def laporan_harian():
    tanggal = request.args.get('tanggal', datetime.now().strftime('%Y-%m-%d'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT k.nama_kelas, s.nis, s.nama, p.status, p.keterangan
        FROM presensi p
        JOIN siswa s ON p.siswa_id = s.id
        JOIN kelas k ON s.kelas_id = k.id
        WHERE p.tanggal = %s
        ORDER BY k.nama_kelas, s.nama
    """, (tanggal,))
    laporan = cursor.fetchall()
    conn.close()
    
    return render_template('laporan_harian.html', laporan=laporan, tanggal=tanggal)

# Laporan Rekap Bulanan per Kelas
@app.route('/rekap-bulanan')
def rekap_bulanan():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM kelas ORDER BY nama_kelas ASC")
    daftar_kelas = cursor.fetchall()
    
    kelas_id = request.args.get('kelas_id')
    bulan = int(request.args.get('bulan', datetime.now().month))
    tahun = int(request.args.get('tahun', datetime.now().year))
    
    rekap_data = []
    days_in_month = calendar.monthrange(tahun, bulan)[1]
    days = list(range(1, days_in_month + 1))
    
    if kelas_id:
        cursor.execute("SELECT id, nis, nama FROM siswa WHERE kelas_id = %s ORDER BY nama ASC", (kelas_id,))
        siswa_list = cursor.fetchall()
        
        for siswa in siswa_list:
            row = {'nama': siswa['nama'], 'nis': siswa['nis'], 'presensi': {}, 'H': 0, 'I': 0, 'S': 0, 'A': 0}
            cursor.execute("""
                SELECT DAY(tanggal) as hari, status 
                FROM presensi 
                WHERE siswa_id = %s AND MONTH(tanggal) = %s AND YEAR(tanggal) = %s
            """, (siswa['id'], bulan, tahun))
            records = cursor.fetchall()
            
            for r in records:
                st = r['status'][0] # H, I, S, A
                row['presensi'][r['hari']] = st
                if st == 'H': row['H'] += 1
                elif st == 'I': row['I'] += 1
                elif st == 'S': row['S'] += 1
                elif st == 'A': row['A'] += 1
                
            rekap_data.append(row)
            
    conn.close()
    return render_template('rekap_bulanan.html', kelas_list=daftar_kelas, rekap_data=rekap_data, 
                           days=days, selected_kelas=kelas_id, bulan=bulan, tahun=tahun)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
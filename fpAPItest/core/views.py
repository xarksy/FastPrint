import requests
import hashlib
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Produk, Kategori, Status
from .forms import ProdukForm
from .api.serializers import ProdukSerializer

# --- LOGIKA 1: SINKRONISASI DATA DARI API ---

def sinkronisasi_data(request):

    # 1. Ambil Waktu Sekarang
    now = datetime.now() # Waktu saat script dijalankan

    # 2. Generate Username Otomatis
    # Rumus: tesprogrammer + dd + mm + yy + C + HH
    # %d = tanggal (2 digit), %m = bulan (2 digit), %y = tahun (2 digit), %H = jam (24 format)
    tgl_format = now.strftime("%d%m%y") # Hasil: 050226
    jam_format = now.strftime("%H")     # Hasil: 21 (misal jam 9 malam)
    
    username_dinamis = f"tesprogrammer{tgl_format}C{jam_format}"


    # 3. Generate Password Otomatis
    # Rumus mentah: bisacoding-dd-mm-yy
    # Contoh: bisacoding-05-02-26
    password_mentah = f"bisacoding-{now.strftime('%d-%m-%y')}"

    # 4. Hashing Password ke MD5
    # hashlib butuh input berupa bytes, jadi harus di-encode() dulu
    password_md5 = hashlib.md5(password_mentah.encode('utf-8')).hexdigest()


    # Debugging (Opsional: Cek di terminal apakah hasil generate sudah benar)
    print(f"DEBUG - Username: {username_dinamis}")
    print(f"DEBUG - Pass Mentah: {password_mentah}")
    print(f"DEBUG - Pass MD5: {password_md5}")

    # 5. Kirim ke API
    url_api = "https://recruitment.fastprint.co.id/tes/api_tes_programmer"
    payload = {
        'username': username_dinamis,
        'password': password_md5
    }
    
    # PENTING: Menggunakan POST sesuai response url api.
    try:
        response = requests.post(url_api, data=payload)
        
        if response.status_code == 200:
            data_json = response.json()
            
            # Asumsi struktur JSON API memiliki key 'data' list produk
            # Anda mungkin perlu print(data_json) dulu untuk debug struktur aslinya
            list_produk = data_json.get('data', []) 

            count_sukses = 0
            
            for item in list_produk:
                # 1. Handle Relasi (Kategori & Status)
                # API biasanya mengirim string/ID, kita harus pastikan ada di DB kita
                kategori_obj, _ = Kategori.objects.get_or_create(
                    nama_kategori=item.get('kategori', 'Umum')
                )
                
                status_obj, _ = Status.objects.get_or_create(
                    nama_status=item.get('status', 'Tidak Diketahui')
                )

                # 2. Siapkan data untuk Serializer
                produk_data = {
                    'nama_produk': item.get('nama_produk'),
                    'harga': item.get('harga'),
                    'kategori': kategori_obj.id_kategori,
                    'status': status_obj.id_status,
                }
                
                # Ambil ID dari API (jika ada)
                api_id = item.get('id_produk')
                if api_id:
                    produk_data['id_produk'] = api_id
                
                # Cek apakah produk dengan ID tersebut sudah ada di DB kita?
                if api_id and Produk.objects.filter(id_produk=api_id).exists():
                    # KONDISI A: SUDAH ADA -> Lakukan UPDATE
                    # Kita panggil objek lama, lalu masukkan ke serializer
                    produk_lama = Produk.objects.get(id_produk=api_id)
                    serializer = ProdukSerializer(produk_lama, data=produk_data)
                    action = "update"
                else:
                    # KONDISI B: BELUM ADA -> Lakukan CREATE (INSERT)
                    serializer = ProdukSerializer(data=produk_data)
                    action = "create"

                # 3. Validasi & Simpan
                if serializer.is_valid():
                    serializer.save()
                    count_sukses += 1
                else:
                    print(f"Gagal {action} {item.get('nama_produk')}: {serializer.errors}")
                
                # Cek jika data valid, atau update jika sudah ada (upsert logic sederhana)
                if serializer.is_valid():
                    serializer.save()
                    count_sukses += 1
                else:
                    print(f"Gagal simpan {item.get('nama_produk')}: {serializer.errors}")

            messages.success(request, f"Berhasil sinkronisasi {count_sukses} data.")
        else:
            messages.error(request, f"Gagal ambil data. Status: {response.status_code}")
            
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan koneksi: {str(e)}")

    return redirect('index')


# --- LOGIKA 2: HALAMAN UTAMA & CRUD ---

def index(request):
    # Poin 5: Tampilkan HANYA yang statusnya "bisa dijual"
    produk_list = Produk.objects.filter(status__nama_status__iexact="bisa dijual")
    return render(request, 'core/index.html', {'produk_list': produk_list})

def tambah_produk(request):
    if request.method == 'POST':
        form = ProdukForm(request.POST)
        if form.is_valid(): # Poin 7: Validasi form
            form.save()
            messages.success(request, "Produk berhasil ditambahkan.")
            return redirect('index')
    else:
        form = ProdukForm()
    return render(request, 'core/form_produk.html', {'form': form, 'title': 'Tambah Produk'})

def edit_produk(request, id_produk):
    produk = get_object_or_404(Produk, pk=id_produk)
    if request.method == 'POST':
        form = ProdukForm(request.POST, instance=produk)
        if form.is_valid():
            form.save()
            messages.success(request, "Produk berhasil diupdate.")
            return redirect('index')
    else:
        form = ProdukForm(instance=produk)
    return render(request, 'core/form_produk.html', {'form': form, 'title': 'Edit Produk'})

def hapus_produk(request, id_produk):
    produk = get_object_or_404(Produk, pk=id_produk)
    
    # Poin 8: Proses hapus (Konfirmasi dilakukan via JS di frontend/template)
    if request.method == 'POST':
        produk.delete()
        messages.success(request, "Produk berhasil dihapus.")
        
    return redirect('index')


def kosongkan_database(request):
    if request.method == "POST":
        # Menghapus semua data Produk
        Produk.objects.all().delete()
        
        # Opsional: Jika ingin menghapus Kategori dan Status juga (Reset total)
        # Karena on_delete=models.CASCADE, menghapus kategori/status 
        # otomatis akan menghapus produk di dalamnya juga.
        Kategori.objects.all().delete() 
        Status.objects.all().delete()

        messages.success(request, "Database berhasil dikosongkan!")
        
    return redirect('index')
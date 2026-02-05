from django.urls import path
from . import views

urlpatterns = [
    # Halaman Utama
    path('', views.index, name='index'),
    
    # Trigger Sinkronisasi (Manual via URL/Tombol)
    path('sync-data/', views.sinkronisasi_data, name='sync_data'),
    
    # CRUD
    path('tambah/', views.tambah_produk, name='tambah_produk'),
    path('edit/<int:id_produk>/', views.edit_produk, name='edit_produk'),
    path('hapus/<int:id_produk>/', views.hapus_produk, name='hapus_produk'),
    path('kosongkan-db/', views.kosongkan_database, name='kosongkan_database'),
]
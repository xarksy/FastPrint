from django import forms
from .models import Produk

class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = ['nama_produk', 'harga', 'kategori', 'status']
        widgets = {
            'nama_produk': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'harga': forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    # Validasi Custom: Inputan nama harus diisi & Harga harus angka
    # (Django ModelForm sudah otomatis memvalidasi tipe data, tapi kita pastikan di sini)
    def clean_harga(self):
        harga = self.cleaned_data.get('harga')
        if harga is None:
            raise forms.ValidationError("Harga harus berupa angka.")
        return harga
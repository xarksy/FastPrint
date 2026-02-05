from rest_framework import serializers
from ..models import Produk, Kategori, Status

class ProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produk
        fields = ['id_produk', 'nama_produk', 'harga', 'kategori', 'status']

    # Validasi tambahan jika harga harus angka (sudah dihandle DecimalField, tapi bisa dipertegas)
    def validate_harga(self, value):
        if value < 0:
            raise serializers.ValidationError("Harga tidak boleh negatif.")
        return value
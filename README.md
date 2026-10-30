# ISPARTA RESCUE AI — Streamlit v1

Bu klasör, Colab projesini tarayıcıdan kullanılabilen bir Streamlit prototipine taşımak için hazırlanmıştır.

## İçerik
- `app.py`: Streamlit uygulaması
- `requirements.txt`: Python paketleri

## Windows üzerinde çalıştırma

1. Bilgisayarında Python 3.10–3.12 kurulu olsun.
2. Bu klasörü aç ve adres çubuğuna `cmd` yazıp Enter'a bas.
3. Şu komutları sırayla çalıştır:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Tarayıcıda genellikle `http://localhost:8501` açılır.

## Kullanım
- Haritaya tıklayarak varsayımsal afet noktasını seç.
- Sol panelden ekiplerin varsayımsal merkez uzaklığını ve yol ağı türünü ayarla.
- “Ekip ve rota analizi” sekmesinde rota hesapla.
- Yol kapanması ve risk analizini, rota analizi sonrasında çalıştır.
- “Ekip bölgeleri” sekmesinde geometrik Voronoi gösterimini incele.

## Önemli sınırlar
- Ekip konumları varsayımsaldır.
- Risk puanları rastgele örnek değerlerdir; gerçek tehlike/hasar verisi değildir.
- OSM yol verisi internet üzerinden alınır; ilk açılışta beklemek gerekebilir.
- Trafik, ekip kapasitesi, bina hasarı, gerçek yol kapanışları ve acil servis protokolleri modellenmez.
- Bu prototip gerçek acil çağrı, sevk veya müdahale amacıyla kullanılamaz.

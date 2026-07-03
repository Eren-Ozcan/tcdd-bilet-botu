# TCDD Bilet Takip Botu

TCDD (ebilet.tcddtasimacilik.gov.tr) uzerinde belirttigin sefer icin bos yer
acildiginda (iade, iptal vb. sebeplerle) Telegram uzerinden bildirim gonderen
ucretsiz bir bot. Telegram'a komut atarak takip ekler/silersin, arka planda
calisan bir script duzenli araliklarla kontrol edip yer bulunca sana mesaj
atar.

**Onemli uyari:** Bu proje TCDD ile resmi bir baglantisi yoktur, ebilet
sitesinin kendi frontend'inin kullandigi genel/herkese acik sorgu ucunu
kullanir (kimseye ozel bir hesap bilgisi kullanilmaz). Kisisel kullanim
icindir; makul sikilikta (varsayilan 5 dakikada bir) calisacak sekilde
ayarlanmistir, bunu arttirmak TCDD sunucularina gereksiz yuk bindirebilir.

## Onemli: GitHub Actions (bulut) calismiyor, yerelde calistirilmali

Bunu test ettim: TCDD'nin API'si, GitHub Actions runner'larinin (ve muhtemelen
her bulut/veri merkezi IP'sinin) yaptigi istekleri sessizce reddediyor -
hem istasyon listesi hem sefer sorgusu ayni sahte "405 Method Not Allowed"
hatasini donduruyor, header/istek icerigi fark etmiyor. Bu bir kod hatasi
degil, TCDD'nin IP tabanli bir bot/anti-scraping korumasi. Bu yuzden proje
**GitHub Actions cron'u kapali** geliyor (`.github/workflows/tcdd-bot.yml`
sadece elle test icin duruyor), bot **kendi bilgisayarindan** calistirilmali
- Turkiye'deki ev/mobil IP'ler bu korumaya takilmiyor. Asagidaki "Yerel
calistirma" bolumunu takip et.

## Kurulum

### 1. Telegram bot olustur

1. Telegram'da **@BotFather** ile sohbet ac.
2. `/newbot` yaz, bir isim ve kullanici adi ver (kullanici adi `bot` ile
   bitmeli, orn. `benim_tcdd_bot`).
3. BotFather sana bir **token** verecek (orn.
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`). Bunu sonraki adimda
   kullanacaksin, kimseyle paylasma (sohbete de yapistirma - bir yere gizlice
   not al).
4. Botunun kullanici adini Telegram'da arayip sohbeti ac, **/start** yaz.
   Bu sart: Telegram, bot sana ancak sen ona ilk mesaji attiktan sonra
   bildirim gonderebilir.

### 2. Yerel calistirma icin hazirla

PowerShell'de proje klasorunde:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Botu calistir

```powershell
$env:TELEGRAM_BOT_TOKEN = "<BotFather'dan aldigin token>"
python -m bot.main
```

Hata almadan biterse (konsola bir sey basmadan kapanabilir, bu normal)
kurulum dogru demektir. `data/` klasorundeki dosyalar (watches.json,
seen.json, offset.json, stations.json) durumu diskte tutar, git'e commit
etmene gerek yoktur.

### 4. Duzenli calismasi icin Gorev Zamanlayici (Task Scheduler) kur

Bot'un boslugu fark edebilmesi icin bu komutun duzenli araliklarla (ornegin
5 dakikada bir) calismasi gerekiyor. Windows'ta:

1. Baslat menusune **"Gorev Zamanlayicisi"** (Task Scheduler) yaz, ac.
2. Sag panelden **"Temel Gorev Olustur..."** (Create Basic Task) sec.
3. Isim ver, orn. `TCDD Bilet Botu`, Ileri.
4. Tetikleyici olarak **"Gunluk"** (Daily) sec, Ileri, bir baslangic saati
   ver, Ileri.
5. Eylem olarak **"Bir program baslat"** (Start a program) sec, Ileri.
6. Program/script alanina: `powershell.exe`
   Bagimsiz degiskenler (Arguments) alanina asagidakini yapistir (token ve
   proje yolunu kendine gore duzenle):
   ```
   -NoProfile -Command "$env:TELEGRAM_BOT_TOKEN='<token>'; cd 'C:\Users\ereno\OneDrive\Masaüstü\projects\TCDD'; .\.venv\Scripts\python.exe -m bot.main"
   ```
7. Sihirbazi bitir. Sonra olusturdugun gorevi bul, sag tikla **"Ozellikler"**
   (Properties) ac, **"Tetikleyiciler"** (Triggers) sekmesine git, tetikleyiciyi
   duzenle ve **"Gorevi tekrarla"** (Repeat task every) kutusunu isaretleyip
   **5 dakika** sec, sure olarak **"Sinirsiz"** (Indefinitely) sec.
8. Kaydet. Artik bilgisayarin acikken her 5 dakikada bir arka planda calisip
   Telegram komutlarini ve boslukları kontrol edecek.

*(Bilgisayarin kapaliyken bot da calismaz - bu yontemin dogasi bu. Surekli
acik kalan bir bilgisayarin/mini PC'nin varsa en guvenilir yontem budur.)*

### 5. Botu kullan

Telegram'da olusturdugun botla sohbete:

```
/izle Ankara;Istanbul;2026-07-10
/izle Ankara;Istanbul;2026-07-10;09:00   (belirli bir saat icin)
/liste
/iptal 1
/yardim
```

Istasyon adini tam yazmana gerek yok, "ankara" gibi bir parca da yeterli;
birden fazla eslesme varsa bot sana secenekleri listeler ve daha net
yazmani ister.

Bos yer bulundugunda bot sana mesaj atar; bilet almak icin
ebilet.tcddtasimacilik.gov.tr adresine gidip islemi tamamlaman gerekir (bot
bilet satin almaz, sadece haber verir), yerler cok hizli doldugu icin
bildirimi gorur gormez islem yapmalisin.

## GitHub reposu ne ise yariyor?

Kod https://github.com/Eren-Ozcan/tcdd-bilet-botu adresinde yedekli
tutuluyor ve `.github/workflows/tcdd-bot.yml` hala repoda duruyor - ama
zamanlanmis (cron) tetikleyicisi kapatildi, sadece "Run workflow" ile elle
tetiklenebiliyor (TCDD birgun bu engellemeyi kaldirirsa ya da baska bir
bulut saglayici engellenmezse diye). Gunluk kullanim tamamen yerel
bilgisayarindan, GitHub'a hic dokunmadan yapiliyor.

## Dosya yapisi

```
bot/
  config.py           TCDD/Telegram sabitleri, dosya yollari
  tcdd_client.py       TCDD API istekleri (istasyon, sefer, koltuk sorgusu)
  telegram_client.py   Telegram getUpdates/sendMessage
  commands.py          /izle /liste /iptal /yardim komutlarinin islenmesi
  main.py              Ana akis: komutlari isle, takipleri kontrol et, bildir
data/
  stations.json         Istasyon adi -> id (ilk calistirmada otomatik doldurulur)
  watches.json           Aktif takipler
  seen.json              Daha once bildirilen koltuklar (tekrar bildirim atmamak icin)
  offset.json             Son islenen Telegram update_id
.github/workflows/tcdd-bot.yml   Sadece elle (workflow_dispatch) tetiklenen test workflow'u
```

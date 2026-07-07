# TCDD Bilet Takip Botu

TCDD (ebilet.tcddtasimacilik.gov.tr) uzerinde belirttigin sefer icin bos yer
acildiginda (iade, iptal vb. sebeplerle) Telegram uzerinden bildirim gonderen
ucretsiz bir bot. Telegram'a komut atarak takip ekler/silersin, arka planda
calisan bir script duzenli araliklarla kontrol edip yer bulunca sana mesaj
atar.

**Onemli uyari:** Bu proje TCDD ile resmi bir baglantisi yoktur, ebilet
sitesini gercek bir tarayiciyla (Playwright/Chromium) acip tipki bir
kullanicinin yaptigi gibi formu doldurup sonuc sayfasini okur - hic kimseye
ozel bir hesap bilgisi kullanilmaz. Kisisel kullanim icindir; makul
sikilikta (varsayilan 5 dakikada bir) calisacak sekilde ayarlanmistir,
bunu arttirmak TCDD sunucularina gereksiz yuk bindirebilir.

## Onemli: TCDD'nin JSON API'si engelli, site tarayiciyla otomatize ediliyor

Bu proje once TCDD'nin dogrudan JSON API'sini (api-yebsp.tcddtasimacilik.gov.tr)
kullaniyordu, ama test ettikce su ortaya cikti: bu API artik tarayici
disindaki HER istemciyi (curl, requests, hatta headless bir tarayicinin
`fetch()` cagrisini bile) reddediyor - gercek bir Turkiye ev IP'sinden bile.
GitHub Actions'in bulut IP'si de ayni sekilde engelleniyor. Bu bir kod hatasi
degil, TCDD'nin bot/anti-scraping korumasi.

Cozum: gercek siteyi (ebilet.tcddtasimacilik.gov.tr) Playwright ile bir
Chromium tarayicisinda acip, "Nereden/Nereye/Tarih" formunu tipki bir insan
gibi doldurup "Sefer Ara" butonuna basiyoruz, sonucu HTML'den okuyoruz
(`bot/tcdd_browser.py`). Sade Playwright de yetmedi - otomasyon izlerini
(`navigator.webdriver` vb.) gizleyen ek onlemler gerekti, bunlar zaten
kodda var. Bu yuzden:

- GitHub Actions cron'u kapali (`.github/workflows/tcdd-bot.yml` sadece
  elle test icin duruyor, bulut IP'siyle bu yeni tarayici tabanli yontem
  test edilmedi).
- Bot **kendi bilgisayarindan**, Turkiye'deki gercek IP'nle calistirilmali.
  Asagidaki kurulumu takip et.

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
python -m playwright install chromium
```

Son satir, botun sitede gezinmek icin kullanacagi Chromium tarayicisini
indirir (~110 MB, bir kere yapman yeterli).

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
   -NoProfile -Command "$env:TELEGRAM_BOT_TOKEN='<token>'; cd 'C:\Projects\TCDD'; .\.venv\Scripts\python.exe -m bot.main"
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
tetiklenebiliyor. Yeni tarayici tabanli yontem GitHub Actions'ta hic test
edilmedi (bulut IP'siyle calisip calismayacagi bilinmiyor). Gunluk kullanim
tamamen yerel bilgisayarindan, GitHub'a hic dokunmadan yapiliyor.

`data/watches.json`, `data/seen.json` ve `data/offset.json` artik git'e
commit edilmiyor (`.gitignore`'da) - bunlar senin kisisel takip listeni ve
Telegram chat ID'ni icerdigi icin sadece yerel diskte kaliyor, public repoda
gorunmuyor.

## Dosya yapisi

```
bot/
  config.py            Telegram sabitleri, dosya yollari
  tcdd_client.py        Istasyon adi eslestirme (Turkce karakter duyarsiz arama)
  tcdd_browser.py       Playwright ile ebilet sitesini acip form doldurma, sonuc kazima
  telegram_client.py    Telegram getUpdates/sendMessage
  commands.py           /izle /liste /iptal /yardim komutlarinin islenmesi
  main.py               Ana akis: komutlari isle, takipleri kontrol et, bildir
data/
  stations.json          Istasyon adi -> id (Telegram komutlarinda ad eslestirme icin, statik)
  watches.json           Aktif takipler (git'e commit edilmiyor)
  seen.json              Daha once bildirilen yerler (git'e commit edilmiyor)
  offset.json            Son islenen Telegram update_id (git'e commit edilmiyor)
.github/workflows/tcdd-bot.yml   Sadece elle (workflow_dispatch) tetiklenen test workflow'u
```

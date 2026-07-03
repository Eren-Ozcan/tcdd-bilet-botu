# TCDD Bilet Takip Botu

TCDD (ebilet.tcddtasimacilik.gov.tr) uzerinde belirttigin sefer icin bos yer
acildiginda (iade, iptal vb. sebeplerle) Telegram uzerinden bildirim gonderen
ucretsiz bir bot. Telegram'a komut atarak takip ekler/silersin, arka planda
GitHub Actions her birkac dakikada bir kontrol edip yer bulunca sana mesaj
atar.

**Onemli uyari:** Bu proje TCDD ile resmi bir baglantisi yoktur, ebilet
sitesinin kendi frontend'inin kullandigi genel/herkese acik sorgu ucunu
kullanir (kimseye ozel bir hesap bilgisi kullanilmaz). Kisisel kullanim
icindir; makul sikilikta (varsayilan 5 dakikada bir) calisacak sekilde
ayarlanmistir, bunu arttirmak TCDD sunucularina gereksiz yuk bindirebilir.

## Bilinen kisit: GitHub Actions'in IP'si engellenmis olabilir

TCDD'nin API sunucusu bazi bulut/veri merkezi IP araliklarindan gelen
baglantilari reddediyor (bunu test ettim, TCDD'nin ana web sitesi acikken API
sunucusuyla TLS baglantisi hic kurulamiyordu). GitHub Actions runner'lari da
bulut IP'si kullandigi icin engellenmis olabilirler; bu ancak gercek bir
calistirma ile anlasilir. Bu yuzden **kurulumdan hemen sonra Actions
sekmesinden "Run workflow" ile bir kere manuel calistir** ve loglarda hata
olup olmadigina bak (asagida "Test etme" bolumune bak).

Eger GitHub Actions engellenmisse, tek satir kod degistirmeden ayni botu
kendi bilgisayarindan da calistirabilirsin (asagida "Alternatif: kendi
bilgisayarindan calistirma" bolumune bak) - cunku Turkiye'deki ev/mobil
IP'leri genellikle engellenmiyor.

## Kurulum

### 1. Telegram bot olustur

1. Telegram'da **@BotFather** ile sohbet ac.
2. `/newbot` yaz, bir isim ve kullanici adi ver (kullanici adi `bot` ile
   bitmeli, orn. `benim_tcdd_bot`).
3. BotFather sana bir **token** verecek (orn.
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`). Bunu sonraki adimda
   kullanacaksin, kimseyle paylasma.

### 2. Bu klasoru GitHub'a yukle

1. GitHub'da yeni bir repo olustur (public onerilir, asagidaki "Neden public"
   bolumune bak).
2. Bu klasordeki dosyalari o repoya push et:

   ```
   git init
   git add .
   git commit -m "TCDD bilet takip botu"
   git branch -M main
   git remote add origin <REPO_URL>
   git push -u origin main
   ```

### 3. Bot token'ini GitHub Secret olarak ekle

Repo sayfasinda: **Settings > Secrets and variables > Actions > New
repository secret**

- Name: `TELEGRAM_BOT_TOKEN`
- Value: BotFather'dan aldigin token

### 4. Test etme

Repo sayfasinda **Actions** sekmesine git, "TCDD Bilet Takip Botu"
workflow'unu sec, **Run workflow** butonuna bas. Calisma bitince loglara bak:

- Hata yoksa ve "sefer sorgusu basarisiz" gibi baglanti hatalari
  gorunmuyorsa: her sey yolunda, cron her 5 dakikada bir otomatik calisacak.
- `ConnectionError`, `timeout` veya benzeri agsal hatalar goruyorsan: GitHub
  Actions'in IP'si TCDD tarafindan engellenmis demektir, asagidaki alternatif
  yontemi kullan.

### 5. Botu kullan

Telegram'da olusturdugun bota git, `/start` yaz, sonra:

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

## Neden public repo?

GitHub Actions'in ucretsiz dakika kotasi private repo'larda ayda 2000
dakika, public repo'larda ise sinirsizdir. Her 5 dakikada bir calisan bir
cron is icin private repoda bu kota hizla dolar. Repoda TELEGRAM_BOT_TOKEN
gizli (Secret) olarak tutuldugu, `data/` klasorundeki bilgiler de (izlenen
guzergah/tarih) hassas olmadigi icin public yapmak guvenlik acisindan sorun
yaratmaz. Yine de private tutup kontrol sikligini `.github/workflows/tcdd-bot.yml`
icindeki cron degerini orn. `*/30 * * * *` yaparak kotaya sigdirabilirsin.

## Alternatif: kendi bilgisayarindan calistirma

GitHub Actions engellenirse veya hic kullanmak istemezsen, ayni kod kendi
bilgisayarinda da calisir (state `data/` klasorundeki dosyalarda tutuluyor,
git'e commit etmene gerek yok):

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:TELEGRAM_BOT_TOKEN = "<token>"
python -m bot.main
```

Bunu duzenli araliklarla calistirmak icin Windows Gorev Zamanlayicisi'nda
("Task Scheduler") her 5 dakikada bir tetiklenen bir gorev olusturabilirsin,
ya da basit bir dongu ile surekli acik birakabilirsin.

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
.github/workflows/tcdd-bot.yml   5 dakikada bir calisan GitHub Actions cron'u
```

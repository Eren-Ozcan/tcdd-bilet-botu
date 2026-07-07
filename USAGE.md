# Kullanım / Usage

Bot, Windows Görev Zamanlayıcı'daki **"TCDD Bilet Botu"** görevi ile her 5
dakikada bir otomatik çalışır. Görev, "kullanıcı oturum açmış olsun olmasın
çalıştır" (S4U) modunda olduğu için ekranda pencere açmaz.

The bot runs automatically every 5 minutes via the **"TCDD Bilet Botu"** task
in Windows Task Scheduler. The task runs in "run whether user is logged on or
not" (S4U) mode, so it never opens a visible window.

---

## Türkçe

> Aşağıdaki komutları **yönetici olarak açılmış** bir PowerShell'de çalıştırın
> (Başlat menüsünde "PowerShell" aratın → sağ tık → "Yönetici olarak çalıştır").

### Botu durdurma (geçici)

```powershell
Disable-ScheduledTask -TaskName 'TCDD Bilet Botu'
```

Görev devre dışı kalır; bot bir daha çalışmaz ama silinmez.

### Botu tekrar çalıştırma

```powershell
Enable-ScheduledTask -TaskName 'TCDD Bilet Botu'
```

Görev tekrar etkinleşir ve 5 dakikalık döngüsüne kaldığı yerden devam eder.

### Hemen bir kez çalıştırma (beklemeden test)

```powershell
Start-ScheduledTask -TaskName 'TCDD Bilet Botu'
```

### Durumunu kontrol etme

```powershell
Get-ScheduledTask -TaskName 'TCDD Bilet Botu'          # Ready = etkin, Disabled = durdurulmus
Get-ScheduledTaskInfo -TaskName 'TCDD Bilet Botu'      # son calisma zamani ve sonucu (0 = basarili)
Get-Content .\data\bot.log -Tail 20                    # botun kendi loglari
```

### Botu tamamen kaldırma (kalıcı)

```powershell
Unregister-ScheduledTask -TaskName 'TCDD Bilet Botu' -Confirm:$false
```

Görev silinir; proje klasörü (`C:\Projects\TCDD`) durur, istersen onu da
silebilirsin.

### Arayüzle (komutsuz) yönetim

Başlat menüsünde **"Görev Zamanlayıcı"** (Task Scheduler) aratıp aç →
görev listesinde **"TCDD Bilet Botu"** görevini bul → sağ tık →
**Devre dışı bırak / Etkinleştir / Çalıştır / Sil**.

---

## English

> Run the commands below in an **elevated (Run as administrator)** PowerShell
> (search "PowerShell" in the Start menu → right-click → "Run as administrator").

### Stop the bot (temporarily)

```powershell
Disable-ScheduledTask -TaskName 'TCDD Bilet Botu'
```

The task is disabled; the bot stops running but is not deleted.

### Start the bot again

```powershell
Enable-ScheduledTask -TaskName 'TCDD Bilet Botu'
```

The task is re-enabled and resumes its 5-minute schedule.

### Run once immediately (test without waiting)

```powershell
Start-ScheduledTask -TaskName 'TCDD Bilet Botu'
```

### Check its status

```powershell
Get-ScheduledTask -TaskName 'TCDD Bilet Botu'          # Ready = enabled, Disabled = stopped
Get-ScheduledTaskInfo -TaskName 'TCDD Bilet Botu'      # last run time and result (0 = success)
Get-Content .\data\bot.log -Tail 20                    # the bot's own logs
```

### Remove the bot completely (permanent)

```powershell
Unregister-ScheduledTask -TaskName 'TCDD Bilet Botu' -Confirm:$false
```

The task is deleted; the project folder (`C:\Projects\TCDD`) stays, delete it
too if you want.

### Manage via GUI (no commands)

Search **"Task Scheduler"** in the Start menu → find the **"TCDD Bilet Botu"**
task in the list → right-click → **Disable / Enable / Run / Delete**.

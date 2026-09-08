# TCDD Ticket Watch Bot

A free bot that notifies you over Telegram when a seat opens up (through
returns, cancellations, and so on) on a TCDD train you are watching
(ebilet.tcddtasimacilik.gov.tr). You add and remove watches by sending
commands to Telegram; a script running in the background checks at regular
intervals and messages you when it finds a seat.

**Important notice:** this project has no official connection to TCDD. It opens
the ebilet site in a real browser (Playwright/Chromium), fills in the form just
as a user would, and reads the results page — no one's account credentials are
used. It is for personal use and is configured to run at a reasonable interval
(every 5 minutes by default); increasing that would put unnecessary load on
TCDD's servers.

## Important: TCDD's JSON API is blocked, so the site is automated with a browser

This project originally used TCDD's JSON API directly
(api-yebsp.tcddtasimacilik.gov.tr), but testing showed that the API now rejects
EVERY client outside a browser (curl, requests, even a headless browser's
`fetch()` call) — including from a real Turkish home IP. GitHub Actions' cloud
IP is blocked the same way. This is not a bug in the code; it is TCDD's
bot/anti-scraping protection.

The workaround: open the real site (ebilet.tcddtasimacilik.gov.tr) in a
Chromium browser with Playwright, fill in the "From/To/Date" form like a human
would, press "Sefer Ara", and read the result out of the HTML
(`bot/tcdd_browser.py`). Plain Playwright was not enough either — extra
measures that hide automation traces (`navigator.webdriver` and friends) were
needed, and those are already in the code. Because of this:

- The GitHub Actions cron is disabled (`.github/workflows/tcdd-bot.yml` is kept
  for manual testing only; the new browser-based method has not been tested
  from a cloud IP).
- The bot should be run **from your own computer**, on your real IP in Turkey.
  Follow the setup below.

## Setup

### 1. Create a Telegram bot

1. Open a chat with **@BotFather** on Telegram.
2. Send `/newbot`, give it a name and a username (the username must end in
   `bot`, e.g. `benim_tcdd_bot`).
3. BotFather will give you a **token** (e.g.
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`). You will use it in the
   next step — do not share it with anyone (do not paste it into a chat either;
   note it down somewhere private).
4. Search for your bot's username on Telegram, open the chat and send
   **/start**. This is required: Telegram only lets a bot message you after you
   have messaged it first.

### 2. Prepare for local running

In the project folder, in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

The last line downloads the Chromium browser the bot uses to navigate the site
(~110 MB, once is enough).

### 3. Run the bot

```powershell
$env:TELEGRAM_BOT_TOKEN = "<the token from BotFather>"
python -m bot.main
```

If it finishes without an error (it may exit without printing anything, which
is normal) the setup is correct. The files in `data/` (watches.json, seen.json,
offset.json, stations.json) keep state on disk; you do not need to commit them
to git.

### 4. Set up Task Scheduler so it runs regularly

For the bot to notice a free seat, this command has to run at regular intervals
(for example every 5 minutes). On Windows:

1. Type **"Task Scheduler"** into the Start menu and open it.
2. In the right pane choose **"Create Basic Task..."**.
3. Give it a name, e.g. `TCDD Ticket Bot`, then Next.
4. Choose **"Daily"** as the trigger, Next, give a start time, Next.
5. Choose **"Start a program"** as the action, Next.
6. In the Program/script field: `powershell.exe`
   In the Arguments field, paste the following (adjust the token and the
   project path for your own setup):
   ```
   -NoProfile -Command "$env:TELEGRAM_BOT_TOKEN='<token>'; cd 'C:\Projects\TCDD'; .\.venv\Scripts\python.exe -m bot.main"
   ```
7. Finish the wizard. Then find the task you created, right-click
   **"Properties"**, go to the **"Triggers"** tab, edit the trigger, tick
   **"Repeat task every"** and choose **5 minutes**, with a duration of
   **"Indefinitely"**.
8. Save. From now on, while your computer is on, it will run in the background
   every 5 minutes and check Telegram commands and free seats.

*(While your computer is off the bot does not run either — that is inherent to
this approach. If you have a machine/mini PC that stays on, that is the most
reliable option.)*

### 5. Use the bot

In the Telegram chat with the bot you created:

```
/izle Ankara;Istanbul;2026-07-10
/izle Ankara;Istanbul;2026-07-10;09:00   (for a specific departure time)
/liste
/iptal 1
/yardim
```

You do not have to type the full station name; a fragment such as "ankara" is
enough. If there is more than one match, the bot lists the options and asks you
to be more specific.

When a free seat is found the bot messages you; to actually buy the ticket you
have to go to ebilet.tcddtasimacilik.gov.tr and complete the purchase yourself
(the bot does not buy tickets, it only tells you). Seats fill up very quickly,
so act as soon as you see the notification.

## What is the GitHub repo for?

The code is backed up at https://github.com/Eren-Ozcan/tcdd-bilet-botu and
`.github/workflows/tcdd-bot.yml` is still in the repo — but its scheduled
(cron) trigger is disabled, and it can only be triggered manually with "Run
workflow". The new browser-based method has never been tested on GitHub Actions
(whether it works from a cloud IP is unknown). Day-to-day use happens entirely
on your local computer, without touching GitHub at all.

`data/watches.json`, `data/seen.json` and `data/offset.json` are no longer
committed to git (they are in `.gitignore`) — they contain your personal watch
list and your Telegram chat ID, so they stay on local disk only and are not
visible in the public repo.

## File layout

```
bot/
  config.py            Telegram constants, file paths
  tcdd_client.py        Station name matching (Turkish-character-insensitive search)
  tcdd_browser.py       Opens the ebilet site with Playwright, fills the form, scrapes results
  telegram_client.py    Telegram getUpdates/sendMessage
  commands.py           Handling of the /izle /liste /iptal /yardim commands
  main.py               Main flow: process commands, check watches, notify
data/
  stations.json          Station name -> id (for name matching in Telegram commands, static)
  watches.json           Active watches (not committed to git)
  seen.json              Seats already notified about (not committed to git)
  offset.json            Last processed Telegram update_id (not committed to git)
.github/workflows/tcdd-bot.yml   Test workflow, manually triggered only (workflow_dispatch)
```

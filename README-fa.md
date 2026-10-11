# eXrelay

eXrelay یک سرور میانی (معمولاً VPS داخل ایران) را به فوروارد خام TCP/UDP جلوی یک یا چند سرور خارجی Xray تبدیل می‌کند.

سرور ایران پروتکل را **حرف نمی‌زند**. بایت‌ها را کپی می‌کند:

```
کاربر  --همان پروتکل-->  ایران:پورت‌شنود  --TCP/UDP خام-->  خارج:پورت‌اصلی
```

روی ایران Xray این‌طور ساخته می‌شود:

- اینباند `dokodemo-door` روی پورت عمومی
- اوت‌باند `freedom` با `settings.redirect` برابر `آدرس‌خارج:پورت‌خارج`

لینکی که به کاربر می‌دهید UUID، پسورد، SNI، کلید Reality، path و flow اصلی را حفظ می‌کند. فقط آدرس و پورت عوض می‌شود و می‌شود IP ایران. چون استریم دوباره بسته‌بندی نمی‌شود، سرور خارج همان هندشیک عادی کلاینت را می‌بیند.

## این ابزار چه مشکلی را حل می‌کند

خیلی از ابزارهای رله، اینباند را `dokodemo-door` می‌گذارند ولی اوت‌باند را یک کلاینت کامل VLESS/VMess می‌سازند. در آن حالت ترافیک کاربر یک بار دیگر داخل پروتکل پیچیده می‌شود و لینک اصلی کار نمی‌کند.

اشکال دوم این است که فایل‌های جدا در `conf.d` نوشته شوند ولی systemd فقط `config.json` را اجرا کند و آن فایل‌ها هیچ‌وقت لود نشوند.

eXrelay هر دو را این‌طور می‌بندد:

- اوت‌باند رله فقط `freedom` + `redirect` است
- همه اینباندها و اوت‌باندها داخل **یک** `config.json` نوشته می‌شود و قبل از ری‌استارت با خود Xray تست می‌شود

تست اتصال به سرور خارج جداست: یک کلاینت موقت ساخته می‌شود، داخل سرویس اصلی نمی‌رود، و بعد از تست بسته می‌شود.

## پیش‌نیازها

اگر نصب نباشند، `install.sh` و همچنین اولین اجرای `exrelay` خودشان نصب‌شان می‌کنند. سوال بله/خیر پرسیده نمی‌شود.

| ابزار | کاربرد |
|---|---|
| python3 | منوی مدیریت |
| curl و unzip و ca-certificates | دانلود نصب و تست |
| Xray | پروسه رله |
| systemd | سرویس `exrelay-xray` |
| proxychains4 | رد کردن تست سرعت از SOCKS موقت |
| speedtest-cli | پینگ، دانلود، آپلود |

لوکیشن و IP خروجی فقط از `https://myip.wtf/json` خوانده می‌شود. از `ipinfo.io` استفاده نمی‌شود.

سیستم‌عامل هدف اوبونتو/دبیان است. رد‌هت، آلپاین و آرچ هم برای پکیج بیس پشتیبانی می‌شوند، ولی مسیر توصیه‌شده دبیان است.

باید با کاربر root اجرا شود، چون پورت‌های زیر ۱۰۲۴، systemd و نصب پکیج لازم دارد.

## نصب

اول این پوشه را در گیت‌هاب بگذارید. روی سرور ایران:

```bash
sudo GITHUB_REPO=yourname/exrelay bash -c "$(curl -fsSL https://raw.githubusercontent.com/yourname/exrelay/main/install.sh)"
```

`yourname/exrelay` را با مسیر واقعی مخزن عوض کنید. شاخه پیش‌فرض `main` است. برای شاخه دیگر:

```bash
sudo GITHUB_REPO=yourname/exrelay BRANCH=master bash -c "$(curl -fsSL https://raw.githubusercontent.com/yourname/exrelay/master/install.sh)"
```

اگر خود فایل زیپ را دارید:

```bash
sudo ZIP_URL='https://github.com/yourname/exrelay/archive/refs/heads/main.zip' bash install.sh
```

اگر `install.sh` کنار پوشه `exrelay/` روی دیسک باشد، دانلودی انجام نمی‌شود و همان فایل‌های محلی نصب می‌شوند:

```bash
sudo bash install.sh
```

نصاب این کارها را می‌کند:

1. پکیج‌های جاافتاده را با apt (یا dnf/yum/apk/pacman) نصب می‌کند
2. اگر `speedtest-cli` در مخزن نبود با pip نصب می‌کند
3. اگر باینری Xray نبود، اسکریپت رسمی XTLS را اجرا می‌کند
4. پوشه برنامه را در `/opt/exrelay/pkg` کپی می‌کند
5. کانفیگ خالی، یونیت systemd و دستور `/usr/local/bin/exrelay` را می‌سازد

بعد:

```bash
sudo exrelay
```

## مثال کاملاً ساختگی

این لینک واقعی نیست. آدرس‌ها از بازه مستندات هستند (`203.0.113.0/24` و `198.51.100.0/24`) و به جایی وصل نمی‌شوند. فقط شکل کار را نشان می‌دهد.

لینکی که از پنل سرور آلمان گرفته‌اید:

```text
vless://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee@203.0.113.50:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.microsoft.com&fp=chrome&pbk=ExamplePublicKey_not_real_0123456789&sid=0123456789abcdef&type=tcp#Example-DE
```

| مورد | مقدار ساختگی |
|---|---|
| آدرس سرور خارج | `203.0.113.50` |
| پورت سرور خارج | `443` |
| پروتکل | VLESS + Reality + Vision |
| IP عمومی سرور ایران | `198.51.100.10` |
| پورتی که روی ایران باز می‌کنید | `8443` |

در منو **1) Add relay** را بزنید، لینک را پیست کنید، پورت شنود را `8443` بگذارید و اسم را `Example-DE` بدهید. با تأیید، برنامه اعمال می‌کند و `config.json` اوت‌باندی شبیه این دارد:

```json
{
  "tag": "out-Example-DE",
  "protocol": "freedom",
  "settings": { "redirect": "203.0.113.50:443" }
}
```

اینباند متناظر، `dokodemo-door` روی `0.0.0.0:8443` است. قانون روتینگ فقط ترافیک همین اینباند را به همین اوت‌باند می‌فرستد. چند سرور یعنی چند اینباند، چند redirect و چند قانون. ترافیک یک پورت به سرور دیگر نشت نمی‌کند.

لینکی که باید به کاربر بدهید (گزینه 5 یا `l1` در لیست):

```text
vless://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee@198.51.100.10:8443?type=tcp&security=reality&sni=www.microsoft.com&fp=chrome&pbk=ExamplePublicKey_not_real_0123456789&sid=0123456789abcdef&flow=xtls-rprx-vision#Example-DE-via-IR
```

کاربر در کلاینت (v2rayN، v2rayNG، Streisand و مانند این‌ها) همین لینک را ایمپورت می‌کند. اتصال او به `198.51.100.10:8443` می‌رسد. ایران همان جریان TCP را دست‌نخورده به `203.0.113.50:443` می‌فرستد. Reality فقط روی سرور خارج تمام می‌شود. ایران کلید خصوصی Reality را ندارد و لازم هم ندارد.

اگر IP عمومی ایران اشتباه تشخیص داده شد، از **9) Settings** گزینه Set public IP را بزنید و دوباره لینک را بگیرید. خود فوروارد به این IP وابسته نیست. فقط متن لینک کاربر به آن بستگی دارد.

## منو

| کلید | کار |
|---|---|
| 1 | افزودن رله با لینک vless / vmess / trojan / ss |
| 2 | فهرست. شماره = جزئیات، `l1` = لینک کاربر، `t1` = تست همان سرور |
| 3 | ویرایش: اسم، پورت، روشن/خاموش، تعویض لینک، حذف |
| 4 | حذف |
| 5 | چاپ همه لینک‌های فعال |
| 6 | ساخت دوباره `config.json` و ری‌استارت سرویس |
| 7 | start / stop / restart / تست صحت کانفیگ |
| 8 | بکاپ و بازگردانی دیتا و کانفیگ |
| 9 | هاست شنود، UDP، پورت پیش‌فرض، IP عمومی |
| 10 | تست یک سرور خارج: اتصال، لوکیشن، سرعت |
| 0 | خروج |

هر بار که Apply می‌زنید، حتی اگر دیتابیس نسخه قدیمی اوت‌باند پروتکلی داشته باشد، از روی فیلد `parsed` دوباره `dokodemo-door` + `freedom redirect` ساخته می‌شود.

## تست سرور خارج

گزینه **10** برای جواب این سوال است: «سرور خارجی که اضافه کردم اصلاً کانکشن می‌دهد؟»

برنامه یک کلاینت موقت Xray بالا می‌آورد که با همان پروتکل لینک (نه با فوروارد خام) به سرور خارج وصل می‌شود و روی `127.0.0.1:18999` یک SOCKS باز می‌کند.

1. **اتصال و لوکیشن**  
   `curl --socks5-hostname 127.0.0.1:18999 https://myip.wtf/json`  
   IP خروجی، شهر، کشور، ISP و hostname نشان داده می‌شود. اگر IP برگشت، یعنی سرور خارج هندشیک را قبول کرده است.
2. **سرعت**  
   فایل `/opt/exrelay/test/proxychains.conf` فقط برای همین پورت SOCKS نوشته می‌شود و این دستور اجرا می‌شود:  
   `proxychains4 -f /opt/exrelay/test/proxychains.conf speedtest-cli --simple`  
   فایل `/etc/proxychains4.conf` سیستم عوض نمی‌شود. معمولاً ۲۰ تا ۶۰ ثانیه طول می‌کشد.
3. **هر دو پشت سر هم.**

اگر proxychains4 یا speedtest-cli نباشد، همان صفحه گزینه نصب دارد و اجرای عادی `exrelay` هم پیش‌نیاز جاافتاده را نصب می‌کند.

این تست، تستِ خودِ رله ایران نیست. تستِ این است که لینک خارجی سالم است. برای دیدن اینکه پورت ایران بالا است، در فهرست شماره سرور را بزنید تا وضعیت listen را بگوید، یا با `ss -tlnp | grep 8443` چک کنید.

## فایل‌ها

```
/opt/exrelay/pkg/exrelay/          بسته پایتون
/opt/exrelay/data/servers.json     رله‌ها، شامل لینک پارس‌شده
/opt/exrelay/data/settings.json    IP عمومی و پیش‌فرض‌ها
/opt/exrelay/config/xray/config.json
/opt/exrelay/logs/
/opt/exrelay/backups/
/opt/exrelay/test/                 کانفیگ کلاینت موقت و proxychains تست
/etc/systemd/system/exrelay-xray.service
/usr/local/bin/exrelay
```

لاگ سرویس:

```bash
journalctl -u exrelay-xray -n 80 --no-pager
```

## ساختار کد

| ماژول | نقش |
|---|---|
| `parsers.py` | خواندن لینک |
| `config_builder.py` | ساخت اینباند، redirect و `config.json` |
| `store.py` | ذخیره سرورها |
| `links.py` | لینک قابل‌دادن به کاربر |
| `service.py` | Xray، systemd، پیش‌نیاز، apply |
| `testing.py` | SOCKS موقت، myip.wtf، speedtest |
| `ui.py` | منو |
| `backup.py` | بکاپ |

## حذف

```bash
sudo systemctl disable --now exrelay-xray
sudo rm -f /etc/systemd/system/exrelay-xray.service /usr/local/bin/exrelay
sudo systemctl daemon-reload
sudo rm -rf /opt/exrelay
```

خود Xray پاک نمی‌شود. اگر آن را هم نمی‌خواهید، اسکریپت رسمی XTLS گزینه `remove --purge` دارد.

نسخه انگلیسی کوتاه‌تر: [README.md](README.md).

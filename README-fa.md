# eXrelay

این اسکریپت با استفاده از یک کانفیگ xray که بین سرور ایران و خارج برقرار شده، ترافیک UDP یا TCP را بین سرور ایران و خارج انتقال میدهد.


کاربرد این اسکریپت برای ساخت تانل بین سرور ایران و خارج ( با استفاده از کانفیگ ساخته شده xray روی سرور خارج) می باشد.

بصورت پیشفرض همون پورت کانفیگ رو انتقال میده، در صورتیکه میتونید تغییرش هم بدید.


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

سیستم‌عامل هدف اوبونتو/دبیان است. رد‌هت، آلپاین و آرچ هم برای پکیج بیس پشتیبانی می‌شوند، ولی مسیر توصیه‌شده دبیان است.

باید با کاربر root اجرا شود، چون پورت‌های زیر ۱۰۲۴، systemd و نصب پکیج لازم دارد.

## نصب

اول این پوشه را در گیت‌هاب بگذارید. روی سرور ایران:

|
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

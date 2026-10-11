# eXrelay

این اسکریپت با استفاده از یک کانفیگ xray که بین سرور ایران و خارج برقرار شده، ترافیک UDP یا TCP را بین سرور ایران و خارج انتقال میدهد.


کاربرد این اسکریپت برای ساخت تانل بین سرور ایران و خارج ( با استفاده از کانفیگ ساخته شده xray روی سرور خارج) می باشد.

بصورت پیشفرض همون پورت کانفیگ رو انتقال میده، در صورتیکه میتونید تغییرش هم بدید.

این اسکریپت باید روی سرور relay ایران اجرا شود.


## پیش‌نیازها

```
apt install unzip wget curl speedtest-cli proxychains4 python3 -y
```

## نصب

```
wget https://github.com/URT19/eXtreme-Dokodemo-door-Tunnel-Creator/raw/refs/heads/main/exrelay-2.0.0.zip

sudo mkdir -p /opt/exrelay/pkg
```

```
sudo unzip exrelay-2.0.0.zip -d /opt/exrelay/pkg

```

```
sudo chmod +x /opt/exrelay/pkg/exrelay.py

sudo python3 /opt/exrelay/pkg/exrelay.py

```

اگه میخواید بصورت فایل اجرایی ساخته بشه، دستور زیر رو بزنید تا هر وقت exrelay رو اجرا کنید ، اسکریپت اجرا بشه

```
sudo ln -sf /opt/exrelay/pkg/exrelay.py /usr/local/bin/exrelay
```



## حذف

```bash
sudo systemctl disable --now exrelay-xray
sudo rm -f /etc/systemd/system/exrelay-xray.service /usr/local/bin/exrelay
sudo systemctl daemon-reload
sudo rm -rf /opt/exrelay
```

خود Xray پاک نمی‌شود. اگر آن را هم نمی‌خواهید، اسکریپت رسمی XTLS گزینه `remove --purge` دارد.

نسخه انگلیسی کوتاه‌تر: [README.md](README.md).

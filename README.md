# 🚀 Xray Multi-Channel Config Editor (Dynamic Tunneling Hub)

<img width="1744" height="923" alt="image" src="https://github.com/user-attachments/assets/869207f0-1cbf-4768-b0a5-70941b2e9826" />

---

<img width="510" height="317" alt="image" src="https://github.com/user-attachments/assets/2e61858b-70f7-4397-adb2-8e364c067341" />

---


[Config Creator page ](https://extremedot.github.io/eXtreme-Dokodemo-door-Tunnel-Creator/)


---


```
curl -H 'Cache-Control: no-cache' "https://raw.githubusercontent.com/ExtremeDot/eXtreme-Dokodemo-door-Tunnel-Creator/master/ex-relay-manager.sh?$RANDOM" -o ex-relay-manager.sh
chmod +x ex-relay-manager.sh
mv ex-relay-manager.sh /usr/local/bin/eXrelayManager && chmod +x /usr/local/bin/eXrelayManager
```

```
eXrelayManager
```

---


یک ابزار تحت وب (Single Page Application) فوق‌العاده سبک، سریع و کاربردی برای **مدیریت، ادغام و ساخت همزمان کانفیگ‌های تانل مولتی‌سرور (تا ۱۰ سرور موازی)** برای هسته Xray/V2Ray بر پایه ساختار استاندارد لودر `conf.d`.

این ابزار به شما کمک می‌کند تا بدون نیاز به درگیر شدن با ساختارهای پیچیده JSON و خطاهای سینتکس، خروجی‌های معتبر و تفکیک‌شده برای فایل‌های `01_inbounds.json`، `02_outbounds.json` و `03_routing.json` سرور ایران خود تولید کنید.

---

## ✨ ویژگی‌های کلیدی (Key Features)

* **⚡ پشتیبانی از ۱۰ سرور همزمان (۱۰ کانال مستقل):** مدیریت و کانفیگ ۱۰ تانل مختلف با ریجن‌ها و پورت‌های متفاوت در یک صفحه به صورت تب‌بندی شده (Tabs).
* **🔗 مبدل هوشمند لینک به اوتباند (Link to Outbound Converter):** پشتیبانی از پارس و تبدیل مستقیم پروتکل‌های محبوب (`VLESS` ،`VMess` ،`Trojan` ،`Shadowsocks`) از فرمت لینک (URL) یا اشتراک به سورس استاندارد JSON خروجی Xray.
* **🛡️ تفکیک خودکار و هوشمند پورت‌های ساکس (Socks Core Routing):** برای جلوگیری از نشت ترافیک (DNS/IP Leak)، ابزار به صورت خودکار برای هر پورت فوروارد شده یک پورت ساکس مِچ (`Port + 1`) ایجاد کرده و هر دو را در آرایه قوانین روتینگ (`inboundTag`) قفل می‌کند.
* **🏷️ کامنت‌گذاری ساختاری و داخلی (Inline Internal Comments):** تزریق کامنت‌های قانونی در ابتدای بلاکِ آرایه‌ها بدون آسیب زدن به ساختار استاندارد فایل‌های JSON جهت ناوبری و عیب‌یابی سریع کانفیگ‌ها در سرور.
* **🎨 طراحی مدرن با فونت زیبای وزیرمتن:** رابط کاربری دارک کاملاً ریسپانسیو، مجهز به دکمه‌های کپی سریع (One-click Copy) و بر پایه فونت فارسی Vazirmatn.
* **🚫 بدون وابستگی (Zero Dependencies):** ساخته شده با HTML5، CSS3 و Pure JavaScript بدون نیاز به هیچ کتابخانه خارجی یا سرور بک‌اند (کاملاً کلاینت‌ساید و امن).

---

## 📂 ساختار فایل‌های خروجی (Output Architecture)

این ابزار ساختار سنتی و شلوغ تک‌فایلی (`config.json`) را به معماری مدرن و ماژولار `conf.d` تبدیل می‌کند:

1. **`01_inbounds.json`**: شامل پروتکل‌های `dokodemo-door` برای گوش دادن به پورت‌های فورواردی سرور ایران و پورت‌های `mixed` (ساکس/اتچمنت) کمکی.
2. **`02_outbounds.json`**: شامل دیتای رمزنگاری شده خروجی پروتکل‌ها به همراه آدرس‌های پشت مرز، تنظیمات جریان (StreamSettings) مانند `gRPC` یا `WS` و پورت خروجی.
3. **`03_routing.json`**: هدایت‌گر اصلی ترافیک؛ متصل‌کننده دقیق پورت‌های ورودی به ساب‌تانل‌های اختصاصی سرورهای خارج بدون تداخل ترافیکی.

---

## 🚀 نحوه استفاده (Quick Start)

1. کد فایل `index.html` را دانلود کنید.
2. آن را در مرورگر خود باز کنید (یا روی یک وب‌سرور/گیت‌هاب پیج هاست کنید).
3. فایل‌های JSON فعلی سرور ایران خود را (در صورت وجود) در باکس‌های مبدا وارد کنید.
4. وارد تب‌های سرور ۱ تا ۱۰ شوید، نام، پورت فوروارد و لینک تانل خارج را پیست کنید.
5. خروجی‌های آماده شده در پایین صفحه را کپی کرده و در مسیر `/usr/local/etc/xray/conf.d/` سرور خود جایگزین کنید.
6. دستور `systemctl restart xray` را اجرا کنید. تانل شما با موفقیت آپدیت شد!

---

## 🤝 مشارکت (Contributing)

از پیشنهادها، گزارش باگ‌ها و Pull Requestهای شما برای بهبود قابلیت‌های پارسر ابزار استقبال می‌شود.

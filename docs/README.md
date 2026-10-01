# Iranian IPG Technical Documents & References (مستندات درگاه‌های پرداخت اینترنتی ایران)

این پوشه شامل مستندات فنی رسمی، فایل‌های PDF بانکی، مشخصات وب‌سرویس‌ها، نمونه مجموعه‌های Postman و راهنماهای پیاده‌سازی درگاه‌های پرداخت اینترنتی ایران (بانک‌ها، PSPها و پرداخت‌یارها) جهت توسعه و شبیه‌سازی در پروژه `ipg-sandbox` است.

---

## 1. جدول مقایسه‌ای درگاه‌های پرداخت (IPG Comparison Matrix)

| نام درگاه (فارسی / انگلیسی) | نوع درگاه | پروتکل ارتباطی | واحد پولی | روش انتقال به درگاه | متد کال‌بک (Callback) | وضعیت سندباکس در تولید |
|---|---|---|---|---|---|---|
| **به‌پرداخت ملت (Behpardakht Mellat)** | شاپرک / PSP بانکی | SOAP 1.1 (WSDL) | ریال (IRR) | فرم `POST` با `RefId` | فرم `POST` | ندارد (نیاز به سندباکس محلی) |
| **زرین‌پال (ZarinPal)** | پرداخت‌یار | REST (JSON) | ریال (IRR) / تومان | `GET` به `StartPay/{authority}` | `GET` (کوئری‌استرینگ) | دارد (`sandbox.zarinpal.com`) |
| **آیدی پی (IDPay)** | پرداخت‌یار | REST (JSON) | ریال (IRR) | `GET` به لینک اختصاصی | `POST` (یا `GET` انتخابی) | دارد (هدر `X-SANDBOX: 1`) |
| **سامان کیش (SEP)** | شاپرک / PSP بانکی | REST / SOAP (Token-based) | ریال (IRR) | فرم `POST` با `Token` | فرم `POST` | ندارد (نیاز به سندباکس محلی) |
| **سداد بانک ملی (Sadad / Melli)** | شاپرک / PSP بانکی | REST / SOAP | ریال (IRR) | فرم `POST` یا توکن | فرم `POST` | ندارد |
| **تجارت الکترونیک پارسیان (PEC)** | شاپرک / PSP بانکی | SOAP / Token REST | ریال (IRR) | فرم `POST` | فرم `POST` | ندارد |
| **پرداخت الکترونیک پاسارگاد (PEP)** | شاپرک / PSP بانکی | REST / Redirect | ریال (IRR) | `POST` / `GET` | فرم `POST` | ندارد |
| **آسان پرداخت (Asan Pardakht / آپ)** | شاپرک / PSP بانکی | REST / SOAP | ریال (IRR) | فرم `POST` | فرم `POST` | ندارد |
| **پرداخت نوین آرین (PNA / اقتصاد نوین)** | شاپرک / PSP بانکی | REST / SOAP | ریال (IRR) | فرم `POST` | فرم `POST` | ندارد |
| **ایران کیش (IranKish)** | شاپرک / PSP بانکی | REST / SOAP | ریال (IRR) | فرم `POST` | فرم `POST` | ندارد |
| **سیزپی (SizPay)** | پرداخت‌یار | REST (JSON) | ریال (IRR) | فرم `POST` / لینک | `POST` | دارد |

---

## 2. ساختار فایل‌ها و پوشه‌های مستندات (Directory Structure)

```
ipg-sandbox/docs/
├── README.md                                          # همین راهنمای جامع و فهرست مستندات
├── behpardakht/                                       # مستندات به پرداخت ملت
│   ├── mellat-technical-reference.md                 # خلاصه فنی، متدها، پارامترها و کدهای خطا
│   ├── MellatPaymentGatewayService.php                # ساختار کلاس‌های کلاینت SOAP برگرفته از WSDL رسمی
│   ├── behpardakht-implementation-ipg-fa-1403.pdf    # آخرین نسخه رسمی مستندات پیاده‌سازی درگاه ملت (۱۴۰۳)
│   ├── mellat-1.29.pdf                               # مستندات فنی به پرداخت نسخه ۱.۲۹
│   ├── mellat_pgw_tech_doc_ver_1.15_fa.pdf          # مستندات فنی و تعاریف داده نسخه ۱.۱۵
│   ├── Mellat_PGW_General_User_Manual_Ver_1.0.pdf     # راهنمای کاربری عمومی درگاه ملت
│   ├── Mellat_PGW_Dynamic_Pay_User_Manual_Ver_1.0.pdf # راهنمای متد پرداخت پویا (Dynamic Pay)
│   ├── Mellat_PGW_Refund_User_Manual_Ver_1.0.pdf      # راهنمای متدهای استرداد و عودت وجه (Refund/Reverse)
│   ├── Mellat_PGW_User_Manual_English_Ver_1.0.pdf    # راهنمای رسمی نسخه انگلیسی (English Version)
│   └── bank-mellat-shaparak.pdf                      # راهنمای اصلاحات و پروتکل‌های شاپرک درگاه ملت
├── zarinpal/                                          # مستندات زرین‌پال
│   ├── zarinpal-rest-api-v4.md                       # مشخصات کامل REST API v4، درخواست، وریفای، ریفاند و خطاها
│   ├── Doc-Persian.pdf                               # مستند رسمی زرین‌پال به زبان فارسی
│   └── Doc-English.pdf                               # مستند رسمی زرین‌پال به زبان انگلیسی
├── idpay/                                             # مستندات آیدی پی
│   ├── idpay-api-v1.1.md                             # مستندات کامل API v1.1 آیدی‌پی، کدهای وضعیت و فیلدهای کال‌بک
│   └── idpay-v1.1.postman_collection.json            # کالکشن رسمی پست‌من (Postman Collection) آیدی‌پی
├── saman-sep/                                         # مستندات پرداخت الکترونیک سامان (سپ)
│   ├── saman-sep-technical-reference.md               # خلاصه فنی وب‌سرویس توکن، کال‌بک و وریفای سامان
│   ├── saman-3.3.pdf                                 # مستندات رسمی اتصال به درگاه سامان نسخه ۳.۳
│   ├── saman-mp-specifications.pdf                   # مشخصات جدید درگاه پرداخت اینترنتی سامان
│   ├── SEP-Purchase-With-Mobile-Number.pdf           # راهنمای خرید با شماره موبایل و توکن
│   ├── sepidan-sep-docs.pdf                          # مستندات مرجع درگاه سامان
│   └── bank-saman-shaparak.pdf                       # راهنمای اصلاحات شاپرک درگاه سامان
├── sadad-melli/                                       # مستندات داده‌ورزی سداد (بانک ملی)
│   ├── melli-1.10.pdf                                # مستندات رسمی وب‌سرویس درگاه سداد ملی نسخه ۱.۱۰
│   ├── BMIEpayment_DeveloperGuide_WebService.pdf      # راهنمای توسعه‌دهندگان سداد (محیط‌های غیر دات‌نت)
│   ├── BMIEpayment_DeveloperGuide_DLL.pdf             # راهنمای توسعه‌دهندگان سداد (.NET DLL)
│   └── BMI-payment-gateway-guide.pdf                 # راهنمای عمومی اتصال به درگاه سداد
├── parsian-pec/                                       # مستندات تجارت الکترونیک پارسیان
│   ├── parsian-gateway-manual.pdf                    # راهنمای اتصال به درگاه پرداخت اینترنتی پارسیان
│   └── parsian-shaparak.pdf                          # مستندات اصلاحات شاپرک درگاه پارسیان
├── pasargad-pep/                                      # مستندات پرداخت الکترونیک پاسارگاد
│   ├── ipg-pasargad.pdf                              # راهنمای اتصال به درگاه پرداخت بانک پاسارگاد
│   └── paypaad-pardakht-amn-pasargad.pdf             # راهنمای پرداخت امن پاسارگاد (پی‌پاد)
├── asan-pardakht/                                     # مستندات آسان پرداخت (آپ)
│   ├── asanpardakht-3.6.pdf                          # مستندات فنی درگاه آسان پرداخت نسخه ۳.۶
│   └── asanpardakht-general.pdf                      # راهنمای عمومی درگاه پرداخت آسان پرداخت
├── pardakht-novin/                                    # مستندات پرداخت نوین آرین (بانک اقتصاد نوین)
│   ├── Pardakht-Novin-IPG-Service-Merchant-Guide.pdf # راهنمای پذیرندگان سرویس IPG پرداخت نوین
│   └── Pardakht-Novin-IPG-Service-Merchant-Post-Params.pdf # تعاریف پارامترهای ارسالی POST
├── irankish/                                          # مستندات ایران کیش (بانک تجارت و صادرات)
│   └── tejarat-bank-kish-credit-card.pdf             # راهنمای اتصال به درگاه پرداخت ایران‌کیش
├── sizpay/                                            # مستندات سیزپی
│   └── sizPayDocsRest.pdf                            # مستندات فنی اتصال به درگاه سیزپی با متد REST
├── fanava/                                            # مستندات فن‌آوا کارت
│   └── FanavaFCPDoc.pdf                              # راهنمای اتصال به درگاه اینترنتی فن‌آوا کارت
└── sarmayeh/                                          # مستندات بانک سرمایه
    └── sarmayeh-payment-gateway-manual.pdf           # راهنمای اتصال به درگاه اینترنتی بانک سرمایه
```

---

## 3. نکات کلیدی برای پیاده‌سازی در `ipg-sandbox`

### ۱. به پرداخت ملت (Behpardakht / Mellat)
- **نام متدهای WSDL**: متدهای استاندارد و مورد انتظار SDKها عبارتند از:
  - `bpPayRequest` (شروع تراکنش و صدور RefId)
  - `bpVerifyRequest` (تایید تراکنش)
  - `bpSettleRequest` (تسویه تراکنش)
  - `bpReversalRequest` (استرداد و برگشت تراکنش)
  - `bpInquiryRequest` (استعلام وضعیت تراکنش)
- **قالب خروجی**: درگاه به پرداخت پاسخ را به صورت یک رشته متنی کاما-جدا برمی‌گرداند (`0,<refId>` برای خرید، یا تک‌کد خطای عددی). کلاینت‌ها با `.split(',')` این مقدار را پارس می‌کنند.
- **کال‌بک**: از شاپرک به سایت پذیرنده به صورت فرم **POST** با پارامترهای `RefId`, `ResCode`, `SaleOrderId`, `SaleReferenceId` ارسال می‌گردد.

### ۲. زرین‌پال (ZarinPal)
- **آتوریتی**: شناسه مرجع (`authority`) با فرمت ۳۶ کاراکتری تولید می‌شود. در حالت سندباکس زرین‌پال با حرف `S` شروع می‌شود (`S0000...`) و در پروداکشن با حرف `A`.
- **وریفای**: اولین بار کد `100` بازمی‌گردد؛ در صورتی که مجدداً متد وریفای فراخوانی شود کد `101` (قبلاً وریفای شده) برگردانده می‌شود.
- **کال‌بک**: متد **GET** با دو پارامتر `Authority` و `Status` (`OK` یا `NOK`).

### ۳. آیدی‌پی (IDPay)
- **هدرهای اختصاصی**:
  - `X-API-KEY`: احراز هویت پذیرنده.
  - `X-SANDBOX: 1` یا `true`: فعال‌سازی محیط تست و شبیه‌سازی در خود سرور آیدی‌پی.
- **شناسه**: کلید منحصر‌به‌فرد ۳۲ کاراکتری هگزادسیمال (`id`) برمی‌گرداند.
- **کدهای وضعیت**: `1` (پرداخت نشده)، `10` (در انتظار تایید)، `100` (تایید شده)، `101` (قبلاً تایید شده).

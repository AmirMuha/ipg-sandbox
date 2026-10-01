# Zarinpal REST API v4 Documentation (مستندات درگاه پرداخت زرین‌پال نسخه ۴)

## Overview (نمای کلی)
زرین‌پال از متد استاندارد REST و تبادل داده JSON بر بستر HTTPS استفاده می‌کند.
واحد پول پیش‌فرض ریال (IRR) است، اما امکان ارسال با تومان (IRT) نیز با پارامتر `currency` پشتیبانی می‌شود.

---

## 1. درخواست پرداخت (Payment Request)

### Endpoint
- **Production**: `POST https://payment.zarinpal.com/pg/v4/payment/request.json`
- **Sandbox**: `POST https://sandbox.zarinpal.com/pg/v4/payment/request.json`

### Headers
```http
Content-Type: application/json
Accept: application/json
```

### Request Body Parameters
| فیلد | نوع | الزامی | توضیحات |
|---|---|---|---|
| `merchant_id` | String | بله | کد ۳۶ کاراکتری مرچنت پذیرنده (در سندباکس رشته UUID دلخواه) |
| `amount` | Integer | بله | مبلغ تراکنش |
| `currency` | String | خیر | واحد پول: `IRR` (ریال) یا `IRT` (تومان). پیش‌فرض: `IRR` |
| `description` | String | بله | شرح تراکنش (حداکثر ۵۰۰ کاراکتر) |
| `callback_url` | String | بله | آدرس بازگشت کاربر پس از پرداخت |
| `metadata` | Object | خیر | اطلاعات تکمیلی: `mobile`, `email`, `order_id` |
| `metadata.mobile` | String | خیر | شماره موبایل پرداخت‌کننده (مثال: `09121234567`) |
| `metadata.email` | String | خیر | ایمیل پرداخت‌کننده |
| `metadata.order_id` | String | خیر | شماره سفارش در سمت پذیرنده |

### Example Request
```json
{
  "merchant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "amount": 10000,
  "currency": "IRR",
  "description": "خرید تست",
  "callback_url": "https://example.com/callback",
  "metadata": {
    "mobile": "09121234567",
    "email": "user@example.com",
    "order_id": "order-1001"
  }
}
```

### Success Response (`200 OK`)
```json
{
  "data": {
    "code": 100,
    "message": "Success",
    "authority": "A0000000000000000000000000000wwOGYpd",
    "fee_type": "Merchant",
    "fee": 100
  },
  "errors": []
}
```
*نکته: در محیط سندباکس، Authority با حرف `S` شروع می‌شود.*

---

## 2. هدایت خریدار به صفحه پرداخت (Checkout Redirect)

خریدار باید به آدرس زیر منتقل (Redirect) شود:
- **Production**: `https://payment.zarinpal.com/pg/StartPay/{authority}`
- **Sandbox**: `https://sandbox.zarinpal.com/pg/StartPay/{authority}`

همچنین نسخه ZarinGate (بدنه مستقیم):
`https://payment.zarinpal.com/pg/StartPay/{authority}/ZarinGate`

---

## 3. بازگشت به سایت پذیرنده (Callback)

زرین‌پال پس از عملیات پرداخت خریدار را از طریق متد **GET** به `callback_url` هدایت می‌کند:
```
https://example.com/callback?Authority=A0000000000000000000000000000wwOGYpd&Status=OK
```

### Query Parameters
| پارامتر | توضیحات |
|---|---|
| `Authority` | شناسه ۳۶ کاراکتری درخواست تراکنش |
| `Status` | وضعیت بازگشت: `OK` (پرداخت موفق یا در حال بررسی) یا `NOK` (لغو یا ناموفق) |

*توجه: فقط در صورت `Status=OK` باید متد `verify` فراخوانی شود.*

---

## 4. تایید تراکنش (Verification)

### Endpoint
- **Production**: `POST https://payment.zarinpal.com/pg/v4/payment/verify.json`
- **Sandbox**: `POST https://sandbox.zarinpal.com/pg/v4/payment/verify.json`

### Request Body Parameters
| فیلد | نوع | الزامی | توضیحات |
|---|---|---|---|
| `merchant_id` | String | بله | کد ۳۶ کاراکتری مرچنت |
| `amount` | Integer | بله | مبلغ تراکنش (باید دقیقاً برابر مبلغ مرحله اول باشد) |
| `authority` | String | بله | شناسه مرجع تراکنش دریافت شده |

### Example Request
```json
{
  "merchant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "amount": 10000,
  "authority": "A0000000000000000000000000000wwOGYpd"
}
```

### Success Response (`200 OK`)
```json
{
  "data": {
    "code": 100,
    "message": "Verified",
    "card_hash": "1EBE3EBEBE35C7EC0F8D6EE4F2F859107A87822CA179BC9528767EA7B5489B69",
    "card_pan": "502229******5995",
    "ref_id": 201,
    "fee_type": "Merchant",
    "fee": 0
  },
  "errors": []
}
```

### Already Verified (`Code 101`)
اگر تراکنش قبلاً وریفای شده باشد، کد `101` بازگردانده می‌شود:
```json
{
  "data": {
    "code": 101,
    "message": "Verified",
    "card_hash": "...",
    "card_pan": "502229******5995",
    "ref_id": 201,
    "fee_type": "Merchant",
    "fee": 0
  },
  "errors": []
}
```

---

## 5. تراکنش‌های وریفای‌نشده (Unverified Transactions)

### Endpoint
- `POST https://payment.zarinpal.com/pg/v4/payment/unVerified.json`

### Request Body
```json
{
  "merchant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Response
```json
{
  "data": {
    "code": 100,
    "message": "Success",
    "authorities": [
      {
        "authority": "A0000000000000000000000000000wwOGYpd",
        "amount": 10000,
        "callback_url": "https://example.com/callback",
        "date": "2026-09-24 10:15:30"
      }
    ]
  },
  "errors": []
}
```

---

## 6. استرداد وجه (Refund)

### Endpoint
- `POST https://payment.zarinpal.com/pg/v4/payment/refund.json`

### Request Body
```json
{
  "merchant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "authority": "A0000000000000000000000000000wwOGYpd",
  "amount": 10000
}
```

---

## 7. لیست کدهای خطا (Error Codes)

| کد | پیام انگلیسی | شرح فارسی |
|---|---|---|
| -9 | Validation error | خطای اعتبارسنجی مقادیر ارسالی |
| -10 | Terminal is not valid | مرچنت‌کد یا IP پذیرنده نامعتبر است |
| -11 | Terminal is not active | ترمینال فعال نیست |
| -12 | Too many attempts | تلاش بیش از حد مجاز در بازه زمانی کوتاه |
| -13 | Terminal limit reached | محدودیت تراکنش پذیرنده |
| -14 | Callback domain does not match | دامنه callback_url با دامنه ثبت شده مغایرت دارد |
| -15 | Terminal user is suspend | ترمینال به حالت تعلیق درآمده است |
| -16 | Terminal user level is not valid | سطح تایید کاربر معتبر نیست |
| -17 | Terminal user level blue | محدودیت سطح آبی |
| -40 | Invalid extra params, expire_in is not valid | پارامتر اضافی منقضی شده |
| -41 | Maximum amount exceeded | حداکثر مبلغ پرداختی تجاوز کرده است (۱۰۰ میلیون تومان) |
| -50 | Session is not valid, amounts values is not the same | مبلغ وریفای با مبلغ پرداخت مغایرت دارد |
| -51 | Session is not valid, session is not active paid try | پرداخت ناموفق |
| -52 | Oops!!, please contact support | خطای غیرمنتظره |
| -53 | Session is not this merchant_id session | تراکنش متعلق به این مرچنت نیست |
| -54 | Invalid authority | اتوریتی نامعتبر است |
| -55 | Manual payment request not found | تراکنش یافت نشد |
| -60 | Session can not be reversed with bank | امکان ریورس تراکنش با بانک وجود ندارد |
| -61 | Session is not in success status | تراکنش در وضعیت موفق نیست یا قبلا ریورس شده |
| -62 | Terminal IP limit must be active | محدودیت IP فعال نیست |
| -63 | Maximum time for reverse expired | زمان مجاز ریورس (۳۰ دقیقه) منقضی شده است |
| 100 | Success / Verified | عملیات موفق / تراکنش تایید شد |
| 101 | Verified | تراکنش قبلاً تایید شده است |

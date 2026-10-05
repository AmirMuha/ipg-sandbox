# به‌پرداخت ملت (Behpardakht Mellat) — مرجع API

مرجع کاری برای آداپتور به‌پرداخت ملت در سندباکس درگاه. جریان سه‌مرحله‌ای است: پرداخت،
تایید، تسویه.

- مسیر پایه در سندباکس: `http://localhost:8080/behpardakht/services/pgw`
- مسیر پایه در درگاه واقعی: `https://payment.behpardakht.ir/pg/Services/pgw`
- هر دو پروتکل `SOAP` (WSDL) و `REST` قابل استفاده است
- تصدیق: `TerminalID` و `User` و `Password`

## ۱. پرداخت — `bpPayRequest`

```
POST /InitializePay/InitializePay
```

| فیلد | نوع | توضیح |
|---|---|---|
| `TerminalID` | عدد | کد پذیرنده (در سندباکس: `847120`) |
| `OrderId` | عدد یا متن | شناسه‌ی سفارش شما |
| `Amount` | عدد | مبلغ به **ریال** |
| `CallbackURL` | آدرس | آدرس بازگشت |
| `CustomerDescription` | متن | اختیاری |

پاسخ:

```json
{
  "ResCode": "0",
  "RefId": "987654321",
  "RedirectURL": "https://payment.behpardakht.ir/Payment/Verify?RefId=987654321"
}
```

کاربر را به `RedirectURL` بفرستید؛ در سندباکس این همان صفحه‌ی پرداخت میزبان است.

## ۲. تایید — `bpVerifyRequest`

```
POST /VerifyPay/VerifyPay
```

بدنه همان فیلدها به‌علاوه‌ی `RefId` برگشتی از مرحله‌ی پرداخت. پاسخ `ResCode` ملاک است:

| `ResCode` | معنی | رفتار اپلیکیشن |
|---|---|---|
| `0` | پرداخت تایید شد | سفارش را نهایی کنید |
| `41` | تراکنش ناموفق است | خطا به کاربر، امکان پرداخت دوباره |
| `43` | مبلغ با تراکنش هم‌خوانی ندارد | بررسی کنید مبلغ را از سمت خودتان تغییر نداده باشید |

## ۳. تسویه — `bpSettleRequest`

```
POST /SettlePay/SettlePay
```

این متد را بعد از تایید موفق صدا بزنید تا مبلغ برای پذیرنده تسویه شود. `ResCode` موفق
(`0`) را ثبت کنید.

## ۴. کدهای خطای متداول

| `ResCode` | معنی |
|---|---|
| `0` | موفق |
| `-1` | ورودی نامعتبر |
| `41` | تراکنش ناموفق |
| `43` | مبلغ تاییدشده با مبلغ پرداخت یکی نیست |
| `54` | آدرس بازگشت نامعتبر است |

## ۵. سناریوهای سندباکس

```
X-IPG-Scenario: approve | decline | timeout | pending_settle | verify_failed | refund
```

| سناریو | نتیجه‌ی قابل انتظار |
|---|---|
| `approve` | `bpVerifyRequest` با `ResCode: 0` و یک `RefId` |
| `decline` | `ResCode: 41` |
| `timeout` | پاسخ HTTP `504` |
| `pending_settle` | تسویه پس از ۵ ثانیه انجام می‌شود |
| `verify_failed` | پرداخت موفق ولی `bpVerifyRequest` خطای `41` می‌دهد |
| `refund` | بازگشت وجه ثبت می‌شود |

## ۶. نمونه‌ی cURL

```bash
curl -X POST http://localhost:8080/behpardakht/services/pgw/InitializePay/InitializePay \
  -H "Content-Type: application/json" \
  -H "X-IPG-Scenario: approve" \
  -d '{
    "TerminalID": 847120,
    "User": "sandbox_test",
    "OrderId": 9042,
    "Amount": 2500000,
    "CallbackURL": "http://localhost:3000/verify"
  }'
```

---
این سند جریان و شکل پیام‌ها را مطابق قرارداد رایج درگاه و پیاده‌سازی سندباکس توصیف می‌کند.
پیش از رفتن به محیط عملیاتی، مقادیر را با مستندات رسمی به‌روز درگاه تطبیق دهید.
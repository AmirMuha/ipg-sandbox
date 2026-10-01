# Saman Electronic Payment (SEP) Technical Specification (مستندات فنی پرداخت سامان کیش)

## Overview (نمای کلی)
پرداخت الکترونیک سامان (سپ - SEP) یکی از بزرگترین PSPهای ایران است.
روال پرداخت در سیستم جدید بر اساس تولید **توکن (Token-based)** است.
واحد پول: **ریال (IRR)**.

---

## 1. نشانی‌های وب‌سرویس (Endpoints)

- **دریافت توکن پرداخت (Token Acquisition)**:
  - `POST https://sep.shaparak.ir/OnlinePG/onlinepg`
- **انتقال به درگاه پرداخت شاپرک (Gateway Redirect)**:
  - `POST https://sep.shaparak.ir/OnlinePG/OnlinePG` (با فیلد `Token`)
- **تایید تراکنش (Verification)**:
  - `POST https://sep.shaparak.ir/verifyTxnRandomSessionkey/ipg/VerifyTransaction`
- **استرداد تراکنش (Reverse)**:
  - `POST https://sep.shaparak.ir/verifyTxnRandomSessionkey/ipg/ReverseTransaction`

---

## 2. فرآیند تراکنش خرید

### مرحله ۱: دریافت توکن (`Token`)
پذیرنده مقادیر زیر را به صورت JSON یا فرم POST به نشانی دریافت توکن ارسال می‌کند:

```json
{
  "action": "token",
  "TerminalId": "12345678",
  "Amount": 100000,
  "ResNum": "Invoice-1001",
  "RedirectUrl": "https://example.com/sep/callback",
  "CellNumber": "09121234567"
}
```

#### پاسخ وب‌سرویس:
```json
{
  "status": 1,
  "token": "a1b2c3d4e5f6g7h8i9...",
  "errorCode": 0,
  "errorDesc": ""
}
```

---

### مرحله ۲: هدایت کاربر به درگاه سامان
پذیرنده کاربر را با متد **POST** به همراه پارامتر `Token` به آدرس درگاه منتقل می‌کند:
```html
<form method="POST" action="https://sep.shaparak.ir/OnlinePG/OnlinePG">
  <input type="hidden" name="Token" value="a1b2c3d4e5f6g7h8i9..." />
  <input type="submit" value="Pay" />
</form>
```

---

### مرحله ۳: بازگشت به پذیرنده (Callback)
سامان داده‌های بازگشتی را با متد **POST** به `RedirectUrl` ارسال می‌کند:

| نام پارامتر | نوع | توضیحات |
|---|---|---|
| `MID` / `TerminalId` | `string` | شماره ترمینال پذیرنده |
| `State` | `string` | وضعیت تراکنش (`OK` یا توضیحات خطا مانند `Canceled By User`) |
| `Status` | `integer` | کد عددی وضعیت پرداخت (`2` یعنی تراکنش موفق در درگاه) |
| `Rrn` | `string` | شماره پیگیری شبکه بانکی (Retrieval Reference Number) |
| `RefNum` | `string` | شماره پیگیری یکتای درگاه سامان |
| `ResNum` | `string` | همان شماره فاکتور ارسالی پذیرنده |
| `TraceNo` | `string` | شماره پیگیری ترمینال |
| `Amount` | `integer` | مبلغ تراکنش به ریال |
| `Wage` | `integer` | کارمزد تراکنش |
| `SecurePan` | `string` | شماره کارت ماسک‌شده خریدار |
| `HashedCardNumber` | `string` | هش شماره کارت |

---

### مرحله ۴: تایید تراکنش (Verification)
پذیرنده در صورت `State == "OK"` موظف است حداکثر ظرف ۷۰ ثانیه متد تایید را فراخوانی کند:

```json
POST https://sep.shaparak.ir/verifyTxnRandomSessionkey/ipg/VerifyTransaction
Content-Type: application/json

{
  "RefNum": "123456789012",
  "TerminalNumber": 12345678
}
```

#### پاسخ موفق:
```json
{
  "ResultCode": 0,
  "Success": true,
  "TransactionDetail": {
    "RRN": "...",
    "RefNum": "123456789012",
    "MaskedPan": "589210******1234",
    "OriginalAmount": 100000,
    "AffectiveAmount": 100000,
    "StraceDate": "2026-09-24 12:30:00",
    "StraceNo": "..."
  }
}
```

---

## 3. کدهای وضعیت و خطای سامان (SEP Status Codes)

| کد | شرح وضعیت |
|---|---|
| `0` / `2` | تراکنش موفق |
| `-1` | خطای عمومی در پردازش |
| `-3` | ورودی‌های ارسالی ناقص یا نامعتبر است |
| `-4` | ترمینال پذیرنده غیرفعال است |
| `-6` | عدم تطابق IP پذیرنده |
| `-7` | خطا در بازگشت وجه |
| `-8` | تراکنش قبلاً Verify شده است |
| `-9` | شماره ترمینال یافت نشد |
| `-10` | شماره پذیرنده یا IP نامعتبر است |
| `-11` | مبلغ تراکنش کمتر یا بیشتر از حد مجاز است |
| `-12` | شماره فاکتور `ResNum` تکراری است |
| `-15` | مهلت زمان انجام عملیات سپری شده است (Timeout) |

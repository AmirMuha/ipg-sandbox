[NAV\\
 ![](https://idpay.ir/web-service/v1.1/images/navbar-cad8cdcb.png)](https://idpay.ir/web-service/v1.1/#)

![](https://idpay.ir/web-service/v1.1/images/logo-2196dfa8.png)

- [مقدمه](https://idpay.ir/web-service/v1.1/#8614460e98)
- [احراز هویت](https://idpay.ir/web-service/v1.1/#cee8b80267)
- [آزمایشگاه](https://idpay.ir/web-service/v1.1/#cea080fca4)
- [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2)
- [بازگشت به سایت پذیرنده](https://idpay.ir/web-service/v1.1/#972fadbc1d)
- [تایید تراکنش](https://idpay.ir/web-service/v1.1/#83f88e9ac0)
- [استعلام وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#2c4c448629)
- [لیست تراکنش ها](https://idpay.ir/web-service/v1.1/#dc1489eb63)
- [وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#ad39f18522)
- [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c)
- [Postman](https://idpay.ir/web-service/v1.1/#postman)

- [v1.1](https://idpay.ir/web-service/v1.1/index.html)
- [v1.0](https://idpay.ir/web-service/v1.0/index.html)
- [GitHub](https://github.com/idpay)
- [تعرفه خدمات](https://blog.idpay.ir/helps/106)
- [پلاگین و افزونه های پرداخت](https://idpay.ir/plugins)

# مقدمه

این راهنما نحوه اتصال برنامه نویسان به درگاه های پرداخت از طریق API آیدی پی را توضیح میدهد.

API آیدی پی به روش [REST](https://en.wikipedia.org/wiki/Representational_state_transfer) سازماندهی شده است.
همچنین بدنه درخواست ها و پاسخ ها با فرمت [JSON](https://en.wikipedia.org/wiki/JSON) می‌باشد.

شما می‌توانید نمونه کدها را در ستون سمت چپ صفحه مشاهده کنید و درصورت تمایل می‌توانید از طریق تب های بالای صفحه، نمونه کدهای زبان های برنامه نویسی مختلف را انتخاب کنید.

# احراز هویت

برای استفاده از API های آیدی پی نیاز به یک API KEY است. شما می‌توانید به داشبورد خود در آیدی پی رفته و در بخش [وب سرویس‌های من](https://panel.idpay.ir/web-services)، یک وب سرویس جدید ایجاد کنید.

بعد از ایجاد وب سرویس، API KEY خود را دریافت می‌کنید و می‌توانید برای فراخوانی API از آن استفاده کنید.

برای ارسال تمام درخواست ها باید API KEY را مانند مثال زیر در header ارسال نمایید:

`X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4`

| پارامتر | نوع | ضروری | توضیحات |
| --- | --- | --- | --- |
| X-API-KEY | string | بله | کلید منحصر بفرد جهت احراز هویت<br>به طول 36 کاراکتر |

# آزمایشگاه

برای تست API و نحوه کارکرد آن می‌توانید در header درخواست های خود کلید `X-SANDBOX` را ارسال کنید.
در صورتیکه مقدار این پارامتر `true` یا `1` باشد، تمام فرایندهای بعدی بصورت آزمایشی ایجاد و شبیه سازی می‌شوند.

همچنین در این حالت حساسیت به آدرس وب سایت و IP در درخواست های ارسال شده اعمال نمی‌شود، و می‌توان درخواست خود را از با هر آدرس Callback یا IPی ارسال کنید.

مقدار پیش فرض این پارامتر `false` یا `0` است.

`X-SANDBOX: 1`

| پارامتر | نوع | ضروری |
| --- | --- | --- |
| X-SANDBOX | boolean | خیر |

# ایجاد تراکنش

با استفاده از آدرس زیر می‌توانید یک تراکنش جدید ایجاد کنید.

```
curl -X POST https://api.idpay.ir/v1.1/payment \
  -H 'Content-Type: application/json' \
  -H 'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4' \
  -H 'X-SANDBOX: 1' \
  -d '{
  "order_id": 101,
  "amount": 10000,
  "name": "قاسم رادمان",
  "phone": "09382198592",
  "mail": "my@site.com",
  "desc": "توضیحات پرداخت کننده",
  "callback": "https://example.com/callback"
}'
```

```
<?php
$params = array(
  'order_id' => '101',
  'amount' => 10000,
  'name' => 'قاسم رادمان',
  'phone' => '09382198592',
  'mail' => 'my@site.com',
  'desc' => 'توضیحات پرداخت کننده',
  'callback' => 'https://example.com/callback',
);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://api.idpay.ir/v1.1/payment');
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
curl_setopt($ch, CURLOPT_HTTPHEADER, array(
  'Content-Type: application/json',
  'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
  'X-SANDBOX: 1'
));

$result = curl_exec($ch);
curl_close($ch);

var_dump($result);
```

```
var request = require('request');

var options = {
  method: 'POST',
  url: 'https://api.idpay.ir/v1.1/payment',
  headers: {
    'Content-Type': 'application/json',
    'X-API-KEY': '6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
    'X-SANDBOX': 1,
  },
  body: {
    'order_id': '101',
    'amount': 10000,
    'name': 'قاسم رادمان',
    'phone': '09382198592',
    'mail': 'my@site.com',
    'desc': 'توضیحات پرداخت کننده',
    'callback': 'https://example.com/callback',
  },
  json: true,
};

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});
```

```
url := "https://api.idpay.ir/v1.1/payment"

data := map[string]string{
  "order_id": "101",
  "amount":   "10000",
  "name":     "قاسم رادمان",
  "phone":    "09382198592",
  "mail":     "my@site.com",
  "desc":     "توضیحات پرداخت کننده",
  "callback": "https://example.com/callback",
}

payload, _ := json.Marshal(data)

req, _ := http.NewRequest("POST", url, bytes.NewBuffer(payload))

req.Header.Set("Content-Type", "application/json")
req.Header.Set("X-API-KEY", "6a7f99eb-7c20-4412-a972-6dfb7cd253a4")
req.Header.Set("X-SANDBOX", 1)

res, _ := http.DefaultClient.Do(req)

defer res.Body.Close()
body, _ := ioutil.ReadAll(res.Body)

fmt.Println(string(body))
```

**آدرس درخواست**

`POST https://api.idpay.ir/v1.1/payment`

**پارامترهای مورد نیاز**

| پارامتر | نوع | ضروری | توضیحات |
| --- | --- | --- | --- |
| order\_id | string | بله | شماره سفارش پذیرنده<br>به طول حداکثر 50 کاراکتر |
| amount | number | بله | مبلغ مورد نظر به ریال<br>مبلغ باید بین 1,000 ریال تا 500,000,000 ریال باشد |
| name | string | خیر | نام پرداخت کننده<br>به طول حداکثر 255 کاراکتر |
| phone | string | خیر | تلفن همراه پرداخت کننده<br>به طول 11 کاراکتر<br>مثل 9382198592 یا 09382198592 یا 989382198592 |
| mail | string | خیر | پست الکترونیک پرداخت کننده<br>به طول حداکثر 255 کاراکتر |
| desc | string | خیر | توضیح تراکنش<br>به طول حداکثر 255 کاراکتر |
| callback | string | بله | آدرس بازگشت به سایت پذیرنده<br>به طول حداکثر 2048 کاراکتر |

**وضعیت پاسخ**

| کد وضعیت | توضیحات |
| --- | --- |
| 201 | تراکنش با موفقیت ایجاد شد |
| 403 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 405 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 406 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |

> وضعیت 200: با اجرای دستور بالا پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "id": "d2e353189823079e1e4181772cff5292",
  "link": "https://idpay.ir/p/ws-sandbox/d2e353189823079e1e4181772cff5292"
}
```

> وضعیت 406: در صورت بروز خطا، پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "error_code": 32,
  "error_message": "شماره سفارش `order_id` نباید خالی باشد."
}
```

**پاسخ**

درصورتیکه درخواست موفق باشد، وضعیت پاسخ `201 Created` اعلام خواهد شد.

در پاسخ، مقادیر `id` و `link` باز میگردد که بهتر است آنها را در دیتابیس خود ذخیره کنید.
بعد از ذخیره اطلاعات دریافتی، پرداخت کننده باید به لینک دریافت شده منتقل شود.

| پارامتر | نوع | توضیحات |
| --- | --- | --- |
| id | string | کلید منحصر بفرد تراکنش |
| link | string | لینک پرداخت برای انتقال خریدار به درگاه پرداخت |

# بازگشت به سایت پذیرنده

بعد از اتمام عملیات پرداخت، درصورتیکه پرداخت با موفقیت انجام شده باشد، پرداخت کننده به آدرسی که پذیرنده در `callback` مشخص کرده بود منتقل می‌شود.

همچنین پارامترهای زیر به آدرس `callback` تعریف شده در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) با توجه به تنظیمات وب سرویس در داشبورد آیدی پی تحت عنوان `روش بازگشت پس از پرداخت` به دو روش `POST (Post form)` یا `GET (Query String)` ارسال می شوند.

**پارامترهای ارسالی با روش POST**

| پارامتر | نوع | توضیحات |
| --- | --- | --- |
| status | number | [وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#ad39f18522) |
| track\_id | number | کد رهگیری آیدی پی |
| id | string | کلید منحصر بفرد تراکنش که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) دریافت شده است |
| order\_id | string | شماره سفارش پذیرنده که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) ارسال شده است |
| amount | number | مبلغ ثبت شده هنگام [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) |
| card\_no | string | شماره کارت پرداخت کننده با فرمت `123456******1234` |
| hashed\_card\_no | string | هش شماره کارت پرداخت کننده با الگوریتم SHA256 |
| date | timestamp | زمان پرداخت تراکنش |

**پارامترهای ارسالی با روش GET**

| پارامتر | نوع | توضیحات |
| --- | --- | --- |
| status | number | [وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#ad39f18522) |
| track\_id | number | کد رهگیری آیدی پی |
| id | string | کلید منحصر بفرد تراکنش که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) دریافت شده است |
| order\_id | string | شماره سفارش پذیرنده که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) ارسال شده است |

# تایید تراکنش

بعد از دریافت اطلاعات به سایت پذیرنده و اعتبار سنجی اطلاعات توسط پذیرنده،
پذیرنده باید تراکنش را تایید کند تا پرداخت بصورت سیستمی تکمیل شود
و از بازگشت پول به پرداخت کننده جلوگیری شود.

```
curl -X POST https://api.idpay.ir/v1.1/payment/verify \
  -H 'Content-Type: application/json' \
  -H 'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4' \
  -H 'X-SANDBOX: 1' \
  -d '{
  "id": "d2e353189823079e1e4181772cff5292",
  "order_id": "101"
}'
```

```
<?php
$params = array(
  'id' => 'd2e353189823079e1e4181772cff5292',
  'order_id' => '101',
);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://api.idpay.ir/v1.1/payment/verify');
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
curl_setopt($ch, CURLOPT_HTTPHEADER, array(
  'Content-Type: application/json',
  'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
  'X-SANDBOX: 1',
));

$result = curl_exec($ch);
curl_close($ch);

var_dump($result);
```

```
var request = require('request');

var options = {
  method: 'POST',
  url: 'https://api.idpay.ir/v1.1/payment/verify',
  headers: {
    'Content-Type': 'application/json',
    'X-API-KEY': '6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
    'X-SANDBOX': 1,
  },
  body: {
    'id': 'd2e353189823079e1e4181772cff5292',
    'order_id': '101',
  },
  json: true,
};

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});
```

```
url := "https://api.idpay.ir/v1.1/payment/verify"

data := map[string]string{
  "id":       "d2e353189823079e1e4181772cff5292",
  "order_id": "101",
}

payload, _ := json.Marshal(data)

req, _ := http.NewRequest("POST", url, bytes.NewBuffer(payload))

req.Header.Set("Content-Type", "application/json")
req.Header.Set("X-API-KEY", "6a7f99eb-7c20-4412-a972-6dfb7cd253a4")
req.Header.Set("X-SANDBOX", 1)

res, _ := http.DefaultClient.Do(req)

defer res.Body.Close()
body, _ := ioutil.ReadAll(res.Body)

fmt.Println(string(body))
```

**آدرس درخواست**

`POST https://api.idpay.ir/v1.1/payment/verify`

**پارامترهای مورد نیاز**

| پارامتر | نوع | ضروری | توضیحات |
| --- | --- | --- | --- |
| id | string | بله | کلید منحصر بفرد تراکنش که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) دریافت شده است |
| order\_id | string | بله | شماره سفارش پذیرنده که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) ارسال شده است |

**وضعیت پاسخ**

| کد وضعیت | توضیحات |
| --- | --- |
| 200 | تایید تراکنش به موفقیت انجام شد |
| 400 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 403 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 405 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 406 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |

> با اجرای دستور بالا پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "status": "100",
  "track_id": "10012",
  "id": "d2e353189823079e1e4181772cff5292",
  "order_id": "101",
  "amount": "10000",
  "date": "1546288200",
  "payment": {
    "track_id": "888001",
    "amount": "10000",
    "card_no": "123456******1234",
    "hashed_card_no": "E59FA6241C94B8836E3D03120DF33E80FD988888BBA0A122240C2E7D23B48295",
    "date": "1546288500"
  },
  "verify": {
    "date": "1546288800"
  }
}
```

> وضعیت 406: در صورت بروز خطا، پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "error_code": 32,
  "error_message": "شماره سفارش `order_id` نباید خالی باشد."
}
```

**پاسخ**

| پارامتر | نوع | توضیحات |
| --- | --- | --- |
| status | number | [وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#ad39f18522) |
| track\_id | number | کد رهگیری آیدی پی |
| id | string | کلید منحصر بفرد تراکنش که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) دریافت شده است |
| order\_id | string | شماره سفارش پذیرنده که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) ارسال شده است |
| amount | number | مبلغ ثبت شده هنگام [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) |
| date | timestamp | زمان ایجاد تراکنش |
| payment | object | اطلاعات پرداخت تراکنش |
| track\_id | string | کد رهگیری پرداخت |
| amount | number | مبلغ قابل پرداخت |
| card\_no | string | شماره کارت پرداخت کننده با فرمت `123456******1234` |
| hashed\_card\_no | string | هش شماره کارت پرداخت کننده با الگوریتم SHA256 |
| date | timestamp | زمان پرداخت تراکنش |
| verify | object | اطلاعات تایید تراکنش |
| date | timestamp | زمان تایید تراکنش |

# استعلام وضعیت تراکنش

با استفاده از آدرس زیر می‌توانید آخرین وضعیت یک تراکنش را دریافت نمایید.

```
curl -X POST https://api.idpay.ir/v1.1/payment/inquiry \
  -H 'Content-Type: application/json' \
  -H 'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4' \
  -H 'X-SANDBOX: 1' \
  -d '{
  "id": "d2e353189823079e1e4181772cff5292",
  "order_id": "101"
}'
```

```
<?php
$params = array(
  'id' => 'd2e353189823079e1e4181772cff5292',
  'order_id' => '101',
);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://api.idpay.ir/v1.1/payment/inquiry');
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
curl_setopt($ch, CURLOPT_HTTPHEADER, array(
  'Content-Type: application/json',
  'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
  'X-SANDBOX: 1',
));

$result = curl_exec($ch);
$httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

var_dump($httpcode);
var_dump($result);
```

```
var request = require('request');

var options = {
  method: 'POST',
  url: 'https://api.idpay.ir/v1.1/payment/inquiry',
  headers: {
    'Content-Type': 'application/json',
    'X-API-KEY': '6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
    'X-SANDBOX': 1,
  },
  body: {
    'id': 'd2e353189823079e1e4181772cff5292',
    'order_id': '101',
  },
  json: true,
};

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});
```

```
url := "https://api.idpay.ir/v1.1/payment/inquiry"

data := map[string]string{
  "id":       "d2e353189823079e1e4181772cff5292",
  "order_id": "101",
}

payload, _ := json.Marshal(data)

req, _ := http.NewRequest("POST", url, bytes.NewBuffer(payload))

req.Header.Set("Content-Type", "application/json")
req.Header.Set("X-API-KEY", "6a7f99eb-7c20-4412-a972-6dfb7cd253a4")
req.Header.Set("X-SANDBOX", 1)

res, _ := http.DefaultClient.Do(req)

defer res.Body.Close()
body, _ := ioutil.ReadAll(res.Body)

fmt.Println(string(body))
```

**آدرس درخواست**

`POST https://api.idpay.ir/v1.1/payment/inquiry`

**پارامترهای مورد نیاز**

| پارامتر | نوع | ضروری | توضیحات |
| --- | --- | --- | --- |
| id | string | بله | کلید منحصر بفرد تراکنش که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) دریافت شده است |
| order\_id | string | بله | شماره سفارش پذیرنده که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) ارسال شده است |

**وضعیت پاسخ**

| کد وضعیت | توضیحات |
| --- | --- |
| 200 | استعلام با موفقیت پاسخ داده شد |
| 400 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 403 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 406 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |

> با اجرای دستور بالا پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "status": "100",
  "track_id": "10012",
  "id": "d2e353189823079e1e4181772cff5292",
  "order_id": "101",
  "amount": "10000",
  "wage": {
    "by": "payee",
    "type": "percent",
    "amount": "2500"
  },
  "date": "1546288200",
  "payer": {
    "name": "قاسم رادمان",
    "phone": "09382198592",
    "mail": "my@site.com",
    "desc": "توضیحات پرداخت کننده"
  },
  "payment": {
    "track_id": "888001",
    "amount": "10000",
    "card_no": "123456******1234",
    "hashed_card_no": "E59FA6241C94B8836E3D03120DF33E80FD988888BBA0A122240C2E7D23B48295",
    "date": "1546288500"
  },
  "verify": {
    "date": "1546288800"
  },
  "settlement": {
    "track_id": "12345678900",
    "amount": "7500",
    "date": "1546398000"
  }
}
```

> وضعیت 406: در صورت بروز خطا پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "error_code": 32,
  "error_message": "شماره سفارش `order_id` نباید خالی باشد."
}
```

**پاسخ**

| پارامتر | نوع | توضیحات |
| --- | --- | --- |
| status | number | [وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#ad39f18522) |
| track\_id | number | کد رهگیری آیدی پی |
| id | string | کلید منحصر بفرد تراکنش که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) دریافت شده است |
| order\_id | string | شماره سفارش پذیرنده که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) ارسال شده است |
| amount | number | مبلغ ثبت شده هنگام [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) |
| wage | object | اطلاعات کارمزد تراکنش |
| by | string | دریافت کارمزد از پذیرنده یا پرداخت کننده<br>\- پذیرنده: payee<br>\- پرداخت کننده: payer |
| type | string | نوع کارمزد تراکنش<br>\- مبلغ ثابت: amount<br>\- درصدی: percent<br>\- پلکانی: stair |
| amount | number | مبلغ کارمزد تراکنش |
| date | timestamp | زمان ایجاد تراکنش |
| payer | object | اطلاعات پرداخت کننده تراکنش |
| name | string | نام پرداخت کننده |
| phone | string | شماره تلفن همراه پرداخت کننده |
| mail | string | پست الکترونیک پرداخت کننده |
| desc | string | توضیحات پرداخت کننده |
| payment | object | اطلاعات پرداخت تراکنش |
| track\_id | string | کد رهگیری پرداخت |
| amount | number | مبلغ قابل پرداخت |
| card\_no | string | شماره کارت پرداخت کننده با فرمت `123456******1234` |
| hashed\_card\_no | string | هش شماره کارت پرداخت کننده با الگوریتم SHA256 |
| date | timestamp | زمان پرداخت تراکنش |
| verify | object | اطلاعات تایید تراکنش |
| date | timestamp | زمان تایید تراکنش |
| settlement | object | اطلاعات واریز تراکنش |
| track\_id | number | کد رهگیری واریز |
| amount | number | مبلغ قابل واریز |
| date | timestamp | زمان واریز تراکنش به حساب بانکی پذیرنده |

# لیست تراکنش ها

با استفاده از آدرس زیر می توانید لیست تراکنش های خود را دریافت کنید.

```
curl -X POST https://api.idpay.ir/v1.1/payment/transactions?page=0&page_size=25 \
  -H 'Content-Type: application/json' \
  -H 'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4' \
  -H 'X-SANDBOX: 0' \
  -d '{
  "id": "e22952579725883bbad9f8fa429134bf",
  "order_id": 101,
  "amount": 10000,
  "status": ["100"],
  "track_id": "27384837",
  "payment_card_no": "636214******5409",
  "payment_hashed_card_no": "B913D97F01CE42601181135DF3D0F81DA9E98E61BE3E3AB4436E6345D6AB0AEA",
  "payment_date": {"min": 1600005000, "max": 1600006000},
  "settlement_date": {"min": 1600005746, "max": 1600006000}
}'
```

```
<?php
$params = array(
  "id" => "e22952579725883bbad9f8fa429134bf",
  "order_id" => 101,
  "amount" => 10000,
  "status" => ["100"],
  "track_id" => "27384837",
  "payment_card_no" => "636214******5409",
  "payment_hashed_card_no" => "B913D97F01CE42601181135DF3D0F81DA9E98E61BE3E3AB4436E6345D6AB0AEA",
  "payment_date" => ["min" => 1600005000, "max" => 1600006000],
  "settlement_date" => ["min" => 1600005746, "max" => 1600006000]
);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://api.idpay.ir/v1.1/payment/transactions?page=0&page_size=5');
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
curl_setopt($ch, CURLOPT_HTTPHEADER, array(
  'Content-Type: application/json',
  'X-API-KEY: 6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
  'X-SANDBOX: 0'
));

$result = curl_exec($ch);
curl_close($ch);

var_dump($result);
```

```
var body = {
  "id": "e22952579725883bbad9f8fa429134bf",
  "order_id": 101,
  "amount": 10000,
  "status": ["100"],
  "track_id": "27384837",
  "payment_card_no": "636214******5409",
  "payment_hashed_card_no": "B913D97F01CE42601181135DF3D0F81DA9E98E61BE3E3AB4436E6345D6AB0AEA",
  "payment_date": {"min": 1600005000, "max": 1600006000},
  "settlement_date": {"min": 1600005746, "max": 1600006000}
}

fetch("https://api.idpay.ir/v1.1/payment/transactions?page=0&page_size=5", {
  "headers": {
    'Content-Type': 'application/json',
    'X-API-KEY': '6a7f99eb-7c20-4412-a972-6dfb7cd253a4',
    'X-SANDBOX': 0
  },
  "body": JSON.stringify(body),
  "method": 'POST'
})
.then(e => e.json())
.then(e => {
    console.log(e)
})
```

```
url := "https://api.idpay.ir/v1.1/payment/transactions?page=0&page_size=5"

data := map[string]string{
  "id": "e22952579725883bbad9f8fa429134bf",
  "order_id": 101,
  "amount": 10000,
  "status": ["100"],
  "track_id": "27384837",
  "payment_card_no": "636214******5409",
  "payment_hashed_card_no": "B913D97F01CE42601181135DF3D0F81DA9E98E61BE3E3AB4436E6345D6AB0AEA",
  "payment_date": {"min": 1600005000, "max": 1600006000},
  "settlement_date": {"min": 1600005746, "max": 1600006000}
}

payload, _ := json.Marshal(data)

req, _ := http.NewRequest("POST", url, bytes.NewBuffer(payload))

req.Header.Set("Content-Type", "application/json")
req.Header.Set("X-API-KEY", "6a7f99eb-7c20-4412-a972-6dfb7cd253a4")
req.Header.Set("X-SANDBOX", 0)

res, _ := http.DefaultClient.Do(req)

defer res.Body.Close()
body, _ := ioutil.ReadAll(res.Body)

fmt.Println(string(body))
```

**آدرس درخواست**

`POST https://api.idpay.ir/v1.1/payment/transactions`

**پارامترهای اختیاری در URL**

| پارامتر | نوع | ضروری | توضیحات |
| --- | --- | --- | --- |
| page | number | خیر | شماره صفحه که از 0 شروع می شود و به صورت پیش‌فرض 0 است. |
| page\_size | number | خیر | تعداد رکوردهای دریافتی در هر صفحه و به صورت پیش‌فرض 25 تراکنش آخر است. |

**فیلتر های اختیاری در بدنه درخواست**

| پارامتر | نوع | ضروری | توضیحات |
| --- | --- | --- | --- |
| id | string | خیر | شناسه ای که هنگام ایجاد سفارش دریافت می کنید |
| order\_id | string | خیر | شماره سفارش پذیرنده<br>به طول حداکثر 50 کاراکتر |
| amount | number | خیر | مبلغ تراکنش به ریال<br>مبلغ باید بین 1,000 ریال تا 500,000,000 ریال باشد |
| status | string<br>array | خیر | آرایه ای (لیستی) از [وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) ها |
| track\_id | string | خیر | کد رهگیری آیدی پی |
| payment\_card\_no | string | خیر | شماره کارت پرداخت کننده با فرمت 123456\*\*\*\*\*\*1234 |
| payment\_hashed\_card\_no | string | خیر | هش شماره کارت پرداخت کننده با الگوریتم SHA256 |
| payment\_date | object | خیر | بازه زمان پرداخت تراکنش شامل کمینه و بیشینه از نوع timestamp |
| settlement\_date | object | خیر | بازه زمان تسویه تراکنش با پذیرنده شامل کمینه و بیشینه از نوع timestamp |

**وضعیت پاسخ**

| کد وضعیت | توضیحات |
| --- | --- |
| 200 | لیستی از تراکنش ها را دریافت می کنید |
| 204 | درخواست ارسالی درست است ولی تراکنشی یافت نشد |
| 403 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |
| 406 | [لیست خطاها](https://idpay.ir/web-service/v1.1/#d7b83cfb9c) |

> وضعیت 200: با اجرای دستور بالا پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "attachment": {
    "timestamp": 1601376343,
    "total_count": 1,
    "page_count": 1,
    "current_page": 0,
    "total_amount": "10000",
    "page_amount": 10000
  },
  "records": [\
    {\
      "status": "100",\
      "track_id": "10012",\
      "id": "d2e353189823079e1e4181772cff5292",\
      "order_id": "101",\
      "amount": "10000",\
      "wage": {\
        "by": "payee",\
        "type": "percent",\
        "amount": "2500"\
      },\
      "date": "1546288200",\
      "payer": {\
        "name": "قاسم رادمان",\
        "phone": "09382198592",\
        "mail": "my@site.com",\
        "desc": "توضیحات پرداخت کننده"\
      },\
      "payment": {\
        "track_id": "888001",\
        "amount": "10000",\
        "card_no": "123456******1234",\
        "hashed_card_no": "E59FA6241C94B8836E3D03120DF33E80FD988888BBA0A122240C2E7D23B48295",\
        "date": "1546288500"\
      },\
      "verify": {\
        "date": "1546288800"\
      },\
      "settlement": {\
        "account": {\
          "id": "26338651",\
          "iban": "IR550150000000712300672907",\
          "number": "712300672907",\
          "bank": {\
            "id": "1",\
            "title": "بانک سپه"\
          }\
        },\
        "track_id": "12345678900",\
        "amount": "7500",\
        "date": "1546398000"\
      }\
    }\
  ]
}
```

> وضعیت 406: در صورت بروز خطا، پاسخی مشابه متن زیر با فرمت JSON دریافت می‌شود:

```
{
  "error_code": 41,
  "error_message": "فیلتر وضعیت تراکنش ها می بایست آرایه ای (لیستی) از وضعیت های مجاز در مستندات باشد."
}
```

**پاسخ**

| پارامتر | نوع | توضیحات |
| --- | --- | --- |
| status | number | [وضعیت تراکنش](https://idpay.ir/web-service/v1.1/#ad39f18522) |
| track\_id | number | کد رهگیری آیدی پی |
| id | string | کلید منحصر بفرد تراکنش که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) دریافت شده است |
| order\_id | string | شماره سفارش پذیرنده که در مرحله [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) ارسال شده است |
| amount | number | مبلغ ثبت شده هنگام [ایجاد تراکنش](https://idpay.ir/web-service/v1.1/#2c82b7acb2) |
| wage | object | اطلاعات کارمزد تراکنش |
| by | string | دریافت کارمزد از پذیرنده یا پرداخت کننده<br>\- پذیرنده: payee<br>\- پرداخت کننده: payer |
| type | string | نوع کارمزد تراکنش<br>\- مبلغ ثابت: amount<br>\- درصدی: percent<br>\- پلکانی: stair |
| amount | number | مبلغ کارمزد تراکنش |
| date | timestamp | زمان ایجاد تراکنش |
| payer | object | اطلاعات پرداخت کننده تراکنش |
| name | string | نام پرداخت کننده |
| phone | string | شماره تلفن همراه پرداخت کننده |
| mail | string | پست الکترونیک پرداخت کننده |
| desc | string | توضیحات پرداخت کننده |
| payment | object | اطلاعات پرداخت تراکنش |
| track\_id | string | کد رهگیری پرداخت |
| amount | number | مبلغ قابل پرداخت |
| card\_no | string | شماره کارت پرداخت کننده با فرمت `123456******1234` |
| hashed\_card\_no | string | هش شماره کارت پرداخت کننده با الگوریتم SHA256 |
| date | timestamp | زمان پرداخت تراکنش |
| verify | object | اطلاعات تایید تراکنش |
| date | timestamp | زمان تایید تراکنش |
| settlement | object | اطلاعات واریز تراکنش |
| account | object | اطلاعات حساب بانکی که مبلغ تراکنش به آن واریز شده است. |
| wallet | object | اطلاعات کیف پول آیدی پی که مبلغ تراکنش به آن واریز شده است. |
| track\_id | number | کد رهگیری واریز |
| track\_id | number | کد رهگیری واریز |
| amount | number | مبلغ قابل واریز |
| date | timestamp | زمان واریز تراکنش به حساب بانکی پذیرنده |

# وضعیت تراکنش

وضعیت تراکنش دارای کدهای زیر است که توضیح هر یک در جدول زیر آمده است:

| کد وضعیت تراکنش | توضیحات |
| --- | --- |
| 1 | پرداخت انجام نشده است |
| 2 | پرداخت ناموفق بوده است |
| 3 | خطا رخ داده است |
| 4 | بلوکه شده |
| 5 | برگشت به پرداخت کننده |
| 6 | برگشت خورده سیستمی |
| 7 | انصراف از پرداخت |
| 8 | به درگاه پرداخت منتقل شد |
| 10 | در انتظار تایید پرداخت |
| 100 | پرداخت تایید شده است |
| 101 | پرداخت قبلا تایید شده است |
| 200 | به دریافت کننده واریز شد |

# لیست خطاها

لیست خطاها دارای کدهای زیر است که توضیح هر یک در جدول زیر آمده است:

| وضعیت | کد خطا | توضیح خطا |
| --- | --- | --- |
| 500 | -1 | خطای غیر منتظره |
| 403 | 11 | کاربر مسدود شده است. |
| 403 | 12 | API Key یافت نشد. |
| 403 | 13 | درخواست شما از {ip} ارسال شده است. این IP با IP های ثبت شده در وب سرویس همخوانی ندارد. |
| 403 | 14 | وب سرویس شما در حال بررسی است و یا تایید نشده است. |
| 500 | 15 | سرویس مورد نظر در دسترس نمی باشد. |
| 403 | 21 | حساب بانکی متصل به وب سرویس تایید نشده است. |
| 404 | 22 | وب سریس یافت نشد. |
| 401 | 23 | اعتبار سنجی وب سرویس ناموفق بود. |
| 403 | 24 | حساب بانکی مرتبط با این وب سرویس غیر فعال شده است. |
| 406 | 31 | کد تراکنش `id` نباید خالی باشد. |
| 406 | 32 | شماره سفارش `order_id` نباید خالی باشد. |
| 406 | 33 | مبلغ `amount` نباید خالی باشد. |
| 406 | 34 | مبلغ `amount` باید بیشتر از {min-amount} ریال باشد. |
| 406 | 35 | مبلغ `amount` باید کمتر از {max-amount} ریال باشد. |
| 406 | 36 | مبلغ `amount` بیشتر از حد مجاز است. |
| 406 | 37 | آدرس بازگشت `callback` نباید خالی باشد. |
| 406 | 38 | درخواست شما از آدرس {domain} ارسال شده است. دامنه آدرس بازگشت `callback` با آدرس ثبت شده در وب سرویس همخوانی ندارد. |
| 406 | 39 | آدرس بازگشت `callback` نامعتبر است. |
| 406 | 41 | فیلتر وضعیت تراکنش ها می بایست آرایه ای (لیستی) از وضعیت های مجاز در مستندات باشد. |
| 406 | 42 | فیلتر تاریخ پرداخت می بایست آرایه ای شامل المنت های min و max از نوع timestamp باشد. |
| 406 | 43 | فیلتر تاریخ تسویه می بایست آرایه ای شامل المنت های min و max از نوع timestamp باشد. |
| 406 | 44 | فیلتر تراکنش صحیح نمی باشد. |
| 405 | 51 | تراکنش ایجاد نشد. |
| 400 | 52 | استعلام نتیجه ای نداشت. |
| 405 | 53 | تایید پرداخت امکان پذیر نیست. |
| 405 | 54 | مدت زمان تایید پرداخت سپری شده است. |

# Postman

برای راحتی کار و بررسی سریعتر API آیدی پی می‌توانید فایل زیر را دریافت کنید و آن
را در برنامه [Postman](https://www.getpostman.com/downloads/) استفاده نمایید.

[دریافت فایل نمونه](https://idpay.ir/web-service/v1.1/idpay-v1.1.postman_collection.json)
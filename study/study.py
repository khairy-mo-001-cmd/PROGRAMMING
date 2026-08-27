import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout


# ==============================================================================
# 1. إرسال الطلبات بمختلف الطرق والمعاملات (HTTP Methods & Kwargs)
# ==============================================================================
def demo_http_methods():
    print("--- 1. طرق الطلبات والمعاملات ---")

    # [GET] مع تمرير Query Parameters
    params = {"q": "python", "page": 1}
    res_get = requests.get(
        "https://httpbin.org/get", params=params, timeout=5
    )
    print(f"GET URL: {res_get.url}")

    # [POST] إرسال Form Data
    form_data = {"username": "khairy", "action": "login"}
    res_post_form = requests.post(
        "https://httpbin.org/post", data=form_data, timeout=5
    )
    print(f"POST Form Status: {res_post_form.status_code}")

    # [POST] إرسال JSON Data مخصص مع Headers
    json_payload = {"item": "notebook", "quantity": 3}
    custom_headers = {
        "User-Agent": "MyApp/2.0",
        "Authorization": "Bearer fake_token_123",
    }
    res_post_json = requests.post(
        "https://httpbin.org/post",
        json=json_payload,
        headers=custom_headers,
        timeout=5,
    )
    print(f"POST JSON Status: {res_post_json.status_code}")

    # [PUT] تحديث كامل لبيانات
    res_put = requests.put(
        "https://httpbin.org/put", json={"status": "updated"}, timeout=5
    )
    print(f"PUT Status: {res_put.status_code}")

    # [PATCH] تعديل جزئي
    res_patch = requests.patch(
        "https://httpbin.org/patch", json={"email": "new@test.com"}, timeout=5
    )
    print(f"PATCH Status: {res_patch.status_code}")

    # [DELETE] حذف مورد
    res_delete = requests.delete("https://httpbin.org/delete", timeout=5)
    print(f"DELETE Status: {res_delete.status_code}")

    # [HEAD] جلب الترويسات فقط بدون جسم الاستجابة
    res_head = requests.head("https://httpbin.org/get", timeout=5)
    print(f"HEAD Headers count: {len(res_head.headers)}")

    # [OPTIONS] الاستعلام عن الصلاحيات والخيارات المتاحة
    res_options = requests.options("https://httpbin.org/get", timeout=5)
    print(f"OPTIONS Allowed: {res_options.headers.get('allow')}")

    # [request] الدالة العامة لاستخدام أي Method يدويًا
    res_custom = requests.request("GET", "https://httpbin.org/get", timeout=5)
    print(f"Custom Request Status: {res_custom.status_code}\n")


# ==============================================================================
# 2. خصائص ودوال كائن الاستجابة (Response Object Features)
# ==============================================================================
def demo_response_object():
    print("--- 2. خصائص ودوال الاستجابة ---")

    res = requests.get("https://httpbin.org/get", timeout=5)

    # الخصائص الأساسية
    print(f"Status Code: {res.status_code}")
    print(f"Is OK?: {res.ok}")  # True إذا كان الكود < 400
    print(f"Reason: {res.reason}")  # مثل 'OK'
    print(f"Final URL: {res.url}")
    print(f"Encoding: {res.encoding}")
    print(f"Elapsed Time: {res.elapsed.total_seconds()} seconds")

    # الترويسات والكوكيز
    print(f"Server Header: {res.headers.get('Server')}")

    # التحويل لـ JSON
    json_data = res.json()
    print(f"Parsed JSON Origin IP: {json_data.get('origin')}")

    # قراءة البيانات الخام (Bytes)
    img_res = requests.get("https://httpbin.org/image/png", timeout=5)
    print(f"Raw Image Bytes Length: {len(img_res.content)}")

    # تنزيل ملف مجزأ (Streaming) للملفات الكبيرة
    stream_res = requests.get(
        "https://httpbin.org/stream-bytes/1024", stream=True, timeout=5
    )
    total_bytes = 0
    for chunk in stream_res.iter_content(chunk_size=256):
        total_bytes += len(chunk)
    stream_res.close()
    print(f"Streamed Total Bytes: {total_bytes}\n")


# ==============================================================================
# 3. إدارة الجلسات (Sessions)
# ==============================================================================
def demo_sessions():
    print("--- 3. استخدام Session ---")

    # تعين الجلسة الترويسات والكوكيز عبر عدة طلبات متتالية
    with requests.Session() as session:
        # ضبط ترويسة ثابتة للجلسة بأكملها
        session.headers.update({"X-App-Version": "1.0.0"})

        # طلب ضبط الكوكيز
        session.get("https://httpbin.org/cookies/set/session_token/abc123xyz")

        # طلب آخر للتأكد من إرسال الكوكيز والترويسات تلقائياً
        res = session.get("https://httpbin.org/cookies")
        print(f"Cookies in Session: {res.json()}")


# ==============================================================================
# 4. معالجة الأخطاء الاستثناءات (Exceptions & Error Handling)
# ==============================================================================
def demo_exceptions():
    print("\n--- 4. التعامل مع الأخطاء ---")

    # تجربة خطأ HTTP 404 مع raise_for_status()
    try:
        res = requests.get("https://httpbin.org/status/404", timeout=5)
        res.raise_for_status()
    except HTTPError as e:
        print(f"تعذر الطلب بسبب خطأ HTTP: {e}")

    # تجربة خطأ تجاوز الوقت (Timeout)
    try:
        requests.get("https://httpbin.org/delay/3", timeout=1)
    except Timeout:
        print("خطأ: انتهت المهلة الزمنية قبل استلام الرد!")

    # الهيكل العام الشامل للتعامل مع الأخطاء
    try:
        res = requests.get("https://invalid-domain-name-test.org", timeout=3)
        res.raise_for_status()
    except Timeout:
        print("خطأ في المهلة الزمنية.")
    except ConnectionError:
        print("خطأ في الاتصال بالشبكة أو الـ DNS.")
    except HTTPError as err:
        print(f"خطأ HTTP: {err}")
    except RequestException as err:
        print(f"حدث خطأ عام في المكتبة: {err}")


# ==============================================================================
# التشغيل
# ==============================================================================
if __name__ == "__main__":
    demo_http_methods()
    demo_response_object()
    demo_sessions()
    demo_exceptions()
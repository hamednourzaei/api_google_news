import asyncio
from pygooglenews import GoogleNews
from datetime import datetime
import json
import uuid
import os
import time
import random
from langdetect import detect, LangDetectException

# لیست User-Agent‌ها (اختیاری)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# تنظیم اولیه
print("📢 شروع تنظیم GoogleNews...")
seen_links = set()

def search_news(today):
    items = []
    print("📢 جستجوی اخبار...")
    
    try:
        # انتخاب User-Agent تصادفی
        headers = {'User-Agent': random.choice(USER_AGENTS)} if USER_AGENTS else {}
        gn = GoogleNews(lang='fa', country='IR')
        
        # اضافه کردن تأخیر تصادفی
        time.sleep(random.uniform(2, 5))  # افزایش تأخیر به 2-5 ثانیه
        
        # جستجوی عمومی برای اخبار
        search = gn.search(query='all', when='1d')  # جستجو برای یک ماه گذشته
        print(f"📢 دریافت {len(search['entries'])} خبر از Google News")
        
        if not search['entries']:
            print("⚠️ هیچ خبری از API دریافت نشد. بررسی تنظیمات API یا اتصال اینترنت.")
            return items
        
        for entry in search['entries']:
            try:
                pub_datetime = datetime(*entry.published_parsed[:6])
                print(f"📢 پردازش خبر: {entry.get('title', 'بدون عنوان')} (تاریخ: {pub_datetime})")
            except (TypeError, ValueError):
                print(f"⚠️ خطا در پردازش تاریخ برای خبر: {entry.get('title', 'بدون عنوان')}")
                pub_datetime = datetime.now()
            
            # بررسی تکراری بودن لینک
            if entry['link'] in seen_links:
                print(f"ℹ️ خبر تکراری رد شد: {entry.get('title', 'بدون عنوان')}")
                continue
            
            # تشخیص زبان عنوان خبر
            try:
                language = detect(entry['title'])
            except LangDetectException:
                language = 'unknown'
                print(f"⚠️ خطا در تشخیص زبان برای خبر: {entry.get('title', 'بدون عنوان')}")
            
            news_item = {
                "id": str(uuid.uuid4()),
                "title": entry['title'],
                "link": entry['link'],
                "published": pub_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                "source": entry['source']['title'],
                "summary": entry.get('summary', ''),
                "languages": language
            }
            try:
                json.dumps(news_item, ensure_ascii=False)
                items.append(news_item)
                seen_links.add(entry['link'])  # اضافه کردن لینک به seen_links
                print(f"✅ خبر اضافه شد: {entry['title']} (زبان: {language})")
            except Exception as e:
                print(f"⚠️ خطا در سریال‌سازی خبر: {entry['title']}. خطا: {str(e)}")
    except Exception as e:
        print(f"⚠️ خطا در جستجوی اخبار: {str(e)}")
        if "429" in str(e) or "Too Many Requests" in str(e):
            print("📢 تلاش دوباره بعد از 10 ثانیه...")
            time.sleep(10)
            return search_news(today)  # تلاش دوباره
        elif "503" in str(e) or "Service Unavailable" in str(e):
            print("⚠️ سرور Google News در دسترس نیست. تلاش دوباره بعد از 10 ثانیه...")
            time.sleep(10)
            return search_news(today)
    return items

async def news_producer(today):
    file_name = f"news_{today.strftime('%Y-%m-%d')}.json"
    new_items = []
    print(f"📢 شروع تابع news_producer برای تاریخ {today}...")

    new_items.extend(search_news(today))

    print(f"📢 جمع‌آوری اخبار به پایان رسید. تعداد اخبار جدید: {len(new_items)}")
    if new_items:
        try:
            print(f"📢 تلاش برای خواندن/نوشتن فایل: {file_name}")
            if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
                with open(file_name, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        print(f"📢 فایل {file_name} با موفقیت خوانده شد. تعداد اخبار موجود: {len(data)}")
                    except json.JSONDecodeError:
                        print(f"⚠️ فایل {file_name} نامعتبر است. شروع با فایل خالی.")
                        data = []
            else:
                print(f"📢 فایل {file_name} وجود ندارد یا خالی است. شروع با فایل جدید.")
                data = []

            data.extend(new_items)
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ {len(new_items)} خبر جدید در {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} به {file_name} اضافه شد")
        except Exception as e:
            print(f"⚠️ خطا در نوشتن/خواندن فایل {file_name}: {str(e)}")
    else:
        print(f"ℹ️ هیچ خبر جدیدی در {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} یافت نشد")

async def main():
    today = datetime.now().date()
    print(f"📢 شروع تابع main برای تاریخ {today}...")

    file_name = f"news_{today.strftime('%Y-%m-%d')}.json"
    global seen_links
    try:
        print(f"📢 بررسی فایل موجود: {file_name}")
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            with open(file_name, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    seen_links = set(item['link'] for item in data)
                    print(f"📢 لینک‌های قبلی از فایل {file_name} بارگذاری شدند. تعداد: {len(seen_links)}")
                except json.JSONDecodeError:
                    print(f"⚠️ فایل {file_name} نامعتبر است. شروع با seen_links خالی.")
                    seen_links = set()
        else:
            print(f"📢 فایل {file_name} وجود ندارد یا خالی است. شروع با seen_links خالی.")
            seen_links = set()
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری فایل {file_name}: {str(e)}")
        seen_links = set()

    await news_producer(today)
    print("📢 اجرای اسکریپت به پایان رسید.")

if __name__ == "__main__":
    try:
        print("📢 شروع اجرای اسکریپت...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 اجرای اسکریپت متوقف شد")
    except Exception as e:
        print(f"⚠️ خطای کلی در اجرای اسکریپت: {str(e)}")

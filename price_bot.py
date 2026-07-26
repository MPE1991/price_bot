import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
from datetime import datetime
import jdatetime  # برای تاریخ شمسی

# ===== تنظیمات =====
BOT_TOKEN = "8971414276:AAEYTqEgnhr5_FSvw-dnICkYPkSu_53xzYw"
CHANNEL_ID = "@jalebposts"
CHANNEL_LINK = "@jalebposts"  # آدرس کانال

bot = Bot(token=BOT_TOKEN)


def get_dollar_price():
    """قیمت دلار از tgju.org"""
    try:
        url = "https://www.tgju.org/profile/price_dollar_rl"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        price_element = soup.find("span", {"data-col": "info.last_trade.PDrCotVal"})
        if price_element:
            price_raw = price_element.text.strip()
            price_toman = int(price_raw.replace(",", "")) // 10
            return f"{price_toman:,}"
    except Exception as e:
        print(f"خطا در دلار: {e}")
    return None


def get_gold_18k_price():
    """قیمت طلای ۱۸ عیار از tgju.org"""
    try:
        url = "https://www.tgju.org/profile/geram18"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        price_element = soup.find("span", {"data-col": "info.last_trade.PDrCotVal"})
        if price_element:
            price_raw = price_element.text.strip()
            price_toman = int(price_raw.replace(",", "")) // 10
            return f"{price_toman:,}"
    except Exception as e:
        print(f"خطا در طلای ۱۸ عیار: {e}")
    return None


def get_ounce_gold_price():
    """قیمت اونس جهانی طلا از tgju.org"""
    try:
        url = "https://www.tgju.org/profile/ons"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        price_element = soup.find("span", {"data-col": "info.last_trade.PDrCotVal"})
        if price_element:
            return price_element.text.strip()
    except Exception as e:
        print(f"خطا در اونس طلا: {e}")
    return None


def get_persian_time():
    """گرفتن ساعت و تاریخ شمسی"""
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    
    # تاریخ شمسی
    jalali = jdatetime.datetime.now()
    date_str = jalali.strftime("%Y/%m/%d")
    
    # تبدیل اعداد انگلیسی به فارسی
    time_fa = time_str.replace("0", "۰").replace("1", "۱").replace("2", "۲").replace("3", "۳").replace("4", "۴").replace("5", "۵").replace("6", "۶").replace("7", "۷").replace("8", "۸").replace("9", "۹")
    date_fa = date_str.replace("0", "۰").replace("1", "۱").replace("2", "۲").replace("3", "۳").replace("4", "۴").replace("5", "۵").replace("6", "۶").replace("7", "۷").replace("8", "۸").replace("9", "۹")
    
    return time_fa, date_fa


async def send_prices():
    """گرفتن قیمت‌ها و ارسال به کانال"""
    dollar = get_dollar_price()
    gold18 = get_gold_18k_price()
    ounce = get_ounce_gold_price()
    time_fa, date_fa = get_persian_time()

    message = "💰 **قیمت‌های لحظه‌ای بازار:**\n\n"
    
    if dollar:
        message += f"💵 دلار: `{dollar}` تومان\n"
    if gold18:
        message += f"🪙 طلای ۱۸ عیار: `{gold18}` تومان\n"
    if ounce:
        message += f"🌍 اونس طلا: `{ounce}` دلار\n"
    
    message += f"\n⏰ ساعت: {time_fa}"
    message += f"\n📅 تاریخ: {date_fa}"
    message += f"\n🆔 {CHANNEL_LINK}"

    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")
        print("✅ قیمت‌ها ارسال شد")
    except Exception as e:
        print(f"❌ خطا در ارسال: {e}")


async def main():
    """حلقه اصلی - هر ۳۰ دقیقه"""
    while True:
        await send_prices()
        print("⏳ ۳۰ دقیقه صبر می‌کنم...")
        await asyncio.sleep(1800)


if __name__ == "__main__":
    asyncio.run(main())

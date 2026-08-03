# ========== milad can do anyhing ===========
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import jdatetime
from datetime import datetime
import asyncio
import pytz
import os

SEND_INTERVAL = 3600  # ۲ ساعت 
# ============ تنظیمات ============
# توکن رو از environment variable می‌خونیم، نه اینکه مستقیم توی کد بنویسیم
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_USERNAME = "@MarketPulseIR"

if not TELEGRAM_TOKEN:
    raise ValueError("متغیر محیطی TELEGRAM_TOKEN تنظیم نشده است!")

bot = Bot(token=TELEGRAM_TOKEN)

# ============ توابع قیمت‌ها ============
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
        print(f"خطای دلار: {e}")
    return None

def get_gold_price():
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
        print(f"خطای طلا: {e}")
    return None

def get_gold_silver_ounce():
    """
    قیمت اونس طلا و اونس نقره (دلار) از goldprice.org
    این سایت قیمت‌ها رو از طریق یک API داخلی (JSON) به‌روزرسانی می‌کنه که
    نمودار زنده‌ش هم از همون استفاده می‌کنه، پس خیلی پایدارتر از اسکرپ HTML هست.
    خروجی: (gold_ounce, silver_ounce) به صورت رشته یا (None, None) در صورت خطا
    """
    try:
        url = "https://data-asg.goldprice.org/dbXRates/USD"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        item = data["items"][0]
        gold_ounce = f"{float(item['xauPrice']):,.2f}"
        silver_ounce = f"{float(item['xagPrice']):,.2f}"
        return gold_ounce, silver_ounce
    except Exception as e:
        print(f"خطای اونس طلا/نقره (goldprice.org): {e}")
    return None, None

def get_tether_price():
    """قیمت واقعی تتر به تومان از صرافی Wallex"""
    try:
        url = "https://api.wallex.ir/v1/markets"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        symbols = data.get("result", {}).get("symbols", {})
        usdt_market = symbols.get("USDTTMN", {})
        stats = usdt_market.get("stats", {})

        last_price = stats.get("lastPrice")
        if last_price:
            price_toman = float(last_price)
            return f"{price_toman:,.0f}"

    except Exception as e:
        print(f"خطای تتر: {e}")
    return None


def get_oil_prices_yahoo():
    """
    قیمت لحظه‌ای نفت WTI و برنت از Yahoo Finance
    (endpoint داخلی غیررسمی ولی پایدار و پراستفاده، نیازی به API key نداره)
    نمادها: CL=F برای WTI و BZ=F برای برنت
    خروجی: (wti_price, brent_price) به صورت رشته یا None در صورت خطا
    """
    def fetch_price(symbol):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return f"{float(price):,.2f}"
        except Exception as e:
            print(f"خطای دریافت قیمت {symbol} از Yahoo Finance: {e}")
            return None

    wti_price = fetch_price("CL=F")
    brent_price = fetch_price("BZ=F")
    return wti_price, brent_price

# ============ ارسال پیام ============
async def send_prices():
    """دریافت و ارسال قیمت‌ها"""
    dollar = get_dollar_price()
    gold = get_gold_price()
    gold_ounce, silver_ounce = get_gold_silver_ounce()
    tether = get_tether_price()
    oil_wti, oil_brent = get_oil_prices_yahoo()
    
    # ساعت تهران
    tehran_tz = pytz.timezone('Asia/Tehran')
    now_tehran = datetime.now(tehran_tz)
    time_str = now_tehran.strftime('%H:%M')
    
    # تاریخ شمسی
    jalali_date = jdatetime.datetime.fromgregorian(datetime=now_tehran)
    
    # ============ ساخت متن پیام ============
    text = f"""💰 قیمت‌های لحظه‌ای بازار:

💵 دلار: `{dollar or 'ناموجود'}` تومان
🥇 طلای ۱۸ عیار: `{gold or 'ناموجود'}` تومان
🌍 اونس طلا: `{gold_ounce or 'ناموجود'}` دلار
🥈 اونس نقره: `{silver_ounce or 'ناموجود'}` دلار
💲 تتر: `{tether or 'ناموجود'}` تومان
🛢 نفت WTI: `{oil_wti or 'ناموجود'}` دلار
🛢 نفت برنت: `{oil_brent or 'ناموجود'}` دلار
⏰ ساعت: {time_str}
📅 تاریخ: {jalali_date.strftime('%Y/%m/%d')}
🆔 @MarketPulseIR"""
    
    try:                                              # ← این خط ۴ فاصله داره
        await bot.send_message(                       # ← این خط هم ۸ فاصله
            chat_id=CHANNEL_USERNAME,
            text=text,
            parse_mode="Markdown"
        )
        print(f"✅ قیمت‌ها ارسال شد - {time_str}")
    except Exception as e:                            # ← این خط هم ۸ فاصله (داخل try)
        print(f"❌ خطا در ارسال: {e}")

# ============ حلقه اصلی ============
async def main():
    """ارسال هر ۲ ساعت یک‌بار با مدیریت خطا"""
    print("🤖 ربات قیمت شروع به کار کرد!")
    
    while True:
        try:
            await send_prices()
            print(f"⏰ منتظر {SEND_INTERVAL//3600} ساعت برای ارسال بعدی...")
        except Exception as e:
            print(f"❌ خطا در ارسال: {e}")
            print(f"⏰ بعد از {SEND_INTERVAL//3600} ساعت دوباره تلاش می‌کنم...")
        
        # ✅ همیشه ۲ ساعت صبر کن، چه موفق بشه چه خطا بده
        await asyncio.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())

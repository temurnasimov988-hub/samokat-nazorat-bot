import asyncio
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import datetime
import pytz

# --- SOZLAMALAR ---
JSON_FILE = "key.json"
SPREADSHEET_ID = "178ie0Ryq_FwQ0NrA2oL-X3RbkXICndYfLL4Bb4HcO7U"
BOT_TOKEN = "8923498756:AAEq6TZL8_lCSTdcmpQEmCVY0pkVFcI2egE"

# GitHub Pages havolasi
WEB_APP_URL = "https://temurnasimov988-hub.github.io/samokat-nazorat-bot/"

ALLOWED_PHONES = ["+998972230237", "+998941991535", "+998770014411", "+79895811328"]

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
client = gspread.authorize(creds)

main_sheet = client.open_by_key(SPREADSHEET_ID).sheet1
last_check_sheet = client.open_by_key(SPREADSHEET_ID).worksheet("LastCheck")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(
        text="📝 Nosozlikni kiritish (Web App)", 
        web_app=types.WebAppInfo(url=WEB_APP_URL)
    ))
    await message.answer(
        "Assalomu alaykum! Tizimga ma'lumot kiritish uchun quyidagi tugmani bosing:", 
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(F.web_app_data)
async def web_app_receive(message: types.Message):
    web_data = json.loads(message.web_app_data.data)
    
    ism = web_data.get('ism')
    tel = web_data.get('tel')
    samokat_id = web_data.get('samokat_num')
    current_part = web_data.get('qism')
    current_error = web_data.get('xatolik')
    comment = web_data.get('izoh')

    if tel not in ALLOWED_PHONES:
        await message.answer(f"⚠️ Xatolik: Siz kiritgan `{tel}` telefon raqamiga tizimdan foydalanishga ruxsat berilmagan!")
        return

    # Vaqtni aniqlash
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent_tz)
    vagt_str = now.strftime("%d.%m.%Y %H:%M")
    
    analysis = "Birinchi marta"

    # Smart Analiz (Tahlil) tizimi
    try:
        cell = last_check_sheet.find(samokat_id)
        if cell:
            last_row = last_check_sheet.row_values(cell.row)
            last_time = tashkent_tz.localize(datetime.strptime(last_row[1], "%d.%m.%Y %H:%M"))
            diff = now - last_time
            muddati = f"{diff.days} kun, {diff.seconds // 3600} soat"
            
            if last_row[2] == current_part and last_row[3] == current_error:
                analysis = f"⚠️ TAKROR (Muddati: {muddati}. Oldin ham {current_part}-{current_error} edi)"
            else:
                analysis = f"Yangi ayb (Muddati: {muddati}. Oldin {last_row[2]}-{last_row[3]} edi)"
            
            last_check_sheet.update(range_name=f"B{cell.row}:D{cell.row}", values=[[vagt_str, current_part, current_error]])
        else:
            last_check_sheet.append_row([samokat_id, vagt_str, current_part, current_error])
    except Exception:
        analysis = "Tahlil qilib bo'lmadi"

    # Google Sheets jadvaliga yozish
    row = [vagt_str, ism, tel, samokat_id, current_part, current_error, comment, analysis]
    main_sheet.append_row(row, value_input_option="USER_ENTERED")
    
    # Orqa fonda botga ham chiroyli hisobot borib turaveradi
    await message.answer(
        f"📥 **Yangi ma'lumot keldi va saqlandi:**\n\n"
        f"👤 Mexanik: {ism}\n"
        f"🛴 Samokat: `{samokat_id}`\n"
        f"⚙️ Qism: {current_part}\n"
        f"🚨 Xatolik: {current_error}\n"
        f"📊 **Smart Tahlil:** {analysis}",
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
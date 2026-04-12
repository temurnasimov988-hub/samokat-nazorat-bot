import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

# --- SOZLAMALAR ---
JSON_FILE = "key.json" # Papkangizdagi JSON fayl nomi
SPREADSHEET_ID = "178ie0Ryq_FwQ0NrA2oL-X3RbkXICndYfLL4Bb4HcO7U"
BOT_TOKEN = "8749296120:AAEeLAmghz_BLK7lr6kAlzqdxk7iDU2zEhA" # O'zingizning to'liq tokeningizni qo'ying

# Google Sheets ulanish
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bot bosqichlari (States)
class Anketa(StatesGroup):
    ism = State()
    tel = State()
    samokat_num = State()
    qism = State()
    eski_sn = State()
    yangi_sn = State()
    xato_kodi = State()
    izoh = State()

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Salom! Yangi nazorat ma'lumotlarini kiritishni boshlaymiz.\n\nMexanik ismingizni kiriting:")
    await state.set_state(Anketa.ism)

@dp.message(Anketa.ism)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(ism=message.text)
    
    # Telefon raqam so'rash uchun tugma
    kb = [[types.KeyboardButton(text="📱 Kontaktni ulash", request_contact=True)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer("Rahmat. Endi pastdagi tugmani bosib telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(Anketa.tel)

@dp.message(Anketa.tel, F.contact)
async def get_tel(message: types.Message, state: FSMContext):
    await state.update_data(tel=message.contact.phone_number)
    await message.answer("Samokat raqamini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Anketa.samokat_num)

@dp.message(Anketa.samokat_num)
async def get_scooter(message: types.Message, state: FSMContext):
    await state.update_data(s_num=message.text)
    await message.answer("Almashtirilgan qism nomi:")
    await state.set_state(Anketa.qism)

@dp.message(Anketa.qism)
async def get_part(message: types.Message, state: FSMContext):
    await state.update_data(qism=message.text)
    await message.answer("Eski S/N (seriya raqami):")
    await state.set_state(Anketa.eski_sn)

@dp.message(Anketa.eski_sn)
async def get_old_sn(message: types.Message, state: FSMContext):
    await state.update_data(e_sn=message.text)
    await message.answer("Yangi S/N (seriya raqami):")
    await state.set_state(Anketa.yangi_sn)

@dp.message(Anketa.yangi_sn)
async def get_new_sn(message: types.Message, state: FSMContext):
    await state.update_data(y_sn=message.text)
    await message.answer("Xato kodi:")
    await state.set_state(Anketa.xato_kodi)

@dp.message(Anketa.xato_kodi)
async def get_error(message: types.Message, state: FSMContext):
    await state.update_data(xato=message.text)
    await message.answer("Izoh qoldiring:")
    await state.set_state(Anketa.izoh)

@dp.message(Anketa.izoh)
async def final_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    vagt = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Ma'lumotlarni tartib bilan ro'yxatga yig'amiz
    row = [
        vagt, 
        data['ism'], 
        data['tel'], 
        data['s_num'], 
        data['qism'], 
        data['e_sn'], 
        data['y_sn'], 
        data['xato'], 
        message.text
    ]
    
    try:
        # Jadvalga alohida katakchalar qilib yozish
        sheet.append_row(row, value_input_option="USER_ENTERED")
        await message.answer("✅ Ma'lumotlar muvaffaqiyatli saqlandi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
    
    await state.clear()

async def main():
    print("Bot bosqichma-bosqich rejimda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
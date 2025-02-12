import logging
import random
import asyncio
import os
import time
from database import add_user, add_coins, get_balance
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# 🔥 .env ফাইল লোড করা
load_dotenv()

# ✅ BotFather থেকে পাওয়া API Token
TOKEN = os.getenv("TOKEN")

# ✅ Token না পাওয়া গেলে এরর দেখাবে
if not TOKEN:
    raise ValueError("❌ TOKEN পাওয়া যায়নি! `.env` ফাইলে এটি সেট করো।")

# ✅ Aiogram সেটআপ
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 🔗 রেফারেল সিস্টেম সেটআপ
user_referrals = {}
REFERRAL_BONUS = 100  # রেফারেল বোনাস কয়েন

# 🎡 Spin & Win এবং 🎫 Scratch & Win পুরস্কার তালিকা
SPIN_REWARDS = ["10 Coins", "50 Coins", "100 Coins", "Better Luck Next Time!", "500 Coins", "Jackpot! 1000 Coins"]
SCRATCH_REWARDS = ["5 Coins", "20 Coins", "50 Coins", "No Win!", "200 Coins", "Lucky! 500 Coins"]

# 🎮 মেনু কীবোর্ড
keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎡 Spin & Win")],
    [KeyboardButton(text="🎫 Scratch & Win")],
    [KeyboardButton(text="🎁 Daily Bonus")],
    [KeyboardButton(text="🔗 Referral")],  # ✅ রেফারেল বাটন
    [KeyboardButton(text="💰 Check Balance")]
], resize_keyboard=True)

# 🏦 ইউজারের ব্যালান্স সংরক্ষণ
user_balances = {}
last_bonus_claim = {}
BONUS_AMOUNT = 50  # প্রতিদিন ফ্রি বোনাস কয়েন সংখ্যা

# ✅ ইউজারের ব্যালান্স ফাংশন
def get_balance(user_id):
    return user_balances.get(user_id, 0)

def add_coins(user_id, amount):
    user_balances[user_id] = get_balance(user_id) + amount

# 🏁 `/start` কমান্ড হ্যান্ডলার
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()

    # ইউজার ডাটাবেসে যোগ করো
    add_user(user_id)

    # ✅ যদি ইউজার রেফারেল লিংক দিয়ে জয়েন করে থাকে
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id and referrer_id not in user_referrals.get(user_id, []):  
            add_coins(referrer_id, REFERRAL_BONUS)
            user_referrals.setdefault(user_id, []).append(referrer_id)
            await bot.send_message(referrer_id, f"🎊 আপনি নতুন রেফারেল পেয়েছেন এবং {REFERRAL_BONUS} Coins উপার্জন করেছেন!")

    # ✅ ওয়েলকাম ম্যাসেজ পাঠাও
    welcome_text = f"🎉 Welcome {message.from_user.first_name}!\nPlay and Win Rewards!\nChoose an option below:"
    await message.answer(welcome_text, reply_markup=keyboard)

# 🔗 `/referral` কমান্ড হ্যান্ডলার
@dp.message(Command("referral"))
async def referral_system(message: types.Message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/@Spin4EarnBot?start={user_id}"
    await message.answer(f"🔗 আপনার রেফারেল লিংক:\n{referral_link}\n\n📢 বন্ধুদের শেয়ার করুন এবং প্রতিটি নতুন ইউজারের জন্য {REFERRAL_BONUS} Coins উপার্জন করুন!")

# 🔗 **রেফারেল বাটন প্রেস করলে** একই তথ্য পাঠাবে
@dp.message(lambda message: message.text == "🔗 Referral")
async def referral_button(message: types.Message):
    await referral_system(message)

# 🎁 `/dailybonus` হ্যান্ডলার
@dp.message(Command("dailybonus"))
# 🎁 Daily Bonus বাটন হ্যান্ডলার (সঠিকভাবে বসানো)
@dp.message(lambda message: message.text == "🎁 Daily Bonus")
async def daily_bonus_button(message: types.Message):
    await daily_bonus(message)  # ✅ আগের daily_bonus ফাংশন কল

@dp.message(lambda message: message.text == "🎁 Daily Bonus")
async def daily_bonus(message: types.Message):
    user_id = message.from_user.id
    current_time = time.time()

    # প্রথমবার বোনাস নেওয়ার চেক
    if user_id not in last_bonus_claim:
        last_bonus_claim[user_id] = 0

    # চেক করা হচ্ছে ইউজার শেষ কবে বোনাস নিয়েছে (২৪ ঘণ্টা পার হয়েছে কি না)
    if current_time - last_bonus_claim[user_id] < 86400:
        await message.answer("❌ আপনি ইতিমধ্যে আজকের বোনাস গ্রহণ করেছেন। কাল আবার চেষ্টা করুন!")
    else:
        add_coins(user_id, BONUS_AMOUNT)
        last_bonus_claim[user_id] = current_time  # নতুন সময় স্টোর
        await message.answer(f"🎁 আপনি {BONUS_AMOUNT} Coins ফ্রি পেয়েছেন!\n💰 বর্তমান ব্যালান্স: {get_balance(user_id)} Coins")

# 🎡 **Spin & Win হ্যান্ডলার**
@dp.message(lambda message: message.text == "🎡 Spin & Win")
async def spin_win(message: types.Message):
    reward = random.choice(SPIN_REWARDS)
    if "Coins" in reward:
        coins = int(reward.split()[0])  # সংখ্যাটা বের করে
        add_coins(message.from_user.id, coins)
    await message.answer(f"🎡 Spinning...\nCongratulations! You won: {reward}")

# 🎫 **Scratch & Win হ্যান্ডলার**
@dp.message(lambda message: message.text == "🎫 Scratch & Win")
async def scratch_win(message: types.Message):
    reward = random.choice(SCRATCH_REWARDS)
    if "Coins" in reward:
        coins = int(reward.split()[0])  # সংখ্যাটা বের করে
        add_coins(message.from_user.id, coins)
    await message.answer(f"🎫 Scratching...\nYou got: {reward}")

# 💰 **Check Balance হ্যান্ডলার**
@dp.message(lambda message: message.text == "💰 Check Balance")
@dp.message(Command("balance"))
async def check_balance(message: types.Message):
    balance = get_balance(message.from_user.id)
    await message.answer(f"💰 Your current balance: {balance} Coins")

# 🔥 **বট চালু করা**
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

import os
import re
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Forbidden

# Initialize bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when user starts the bot"""
    welcome_msg = """
    مرحباً! 👋  
    أرسل أي رقم هاتف وسأخبرك إذا كان مشبوهاً.  

    📌 *طريقة الاستخدام:*  
    اكتب `/report` متبوعاً بالرقم، مثل:  
    `/report (اكتب الرقم هن)`  
    `/report ٠٥٠١٢٣٤٥٦٧`  

    🛡️ النتائج المحتملة:  
    ✅ غير مبلغ عنه 
    ⚠️ مشبوه  
    ❌ خطير
    """
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# Country codes for Arabian nations

ARABIAN_COUNTRY_CODES = {
    'SA': '+966', 'AE': '+971', 'EG': '+20', 'QA': '+974', 
    'KW': '+965', 'BH': '+973', 'OM': '+968', 'JO': '+962',
    'LB': '+961', 'PS': '+970', 'SY': '+963', 'IQ': '+964',
    'LY': '+218', 'TN': '+216', 'DZ': '+213', 'MA': '+212',
    'MR': '+222', 'SD': '+249', 'SS': '+211', 'SO': '+252',
    'DJ': '+253', 'KM': '+269', 'YE': '+967', 'EH': '+212'
}
COUNTRY_PATTERNS = {
       # Gulf
    'SA': {'length': 9, 'mobile_prefixes': ['5'], 'landline_prefixes': ['1']},
    'AE': {'length': 9, 'mobile_prefixes': ['5'], 'landline_prefixes': ['2']},
    'KW': {'length': 8, 'mobile_prefixes': ['5', '6', '9'], 'landline_prefixes': ['2']},
    'QA': {'length': 8, 'mobile_prefixes': ['3', '5', '6', '7'], 'landline_prefixes': ['4']},
    'BH': {'length': 8, 'mobile_prefixes': ['3'], 'landline_prefixes': ['1']},
    'OM': {'length': 8, 'mobile_prefixes': ['7', '9'], 'landline_prefixes': ['2']},
    
    # Levant
    'JO': {'length': 9, 'mobile_prefixes': ['7'], 'landline_prefixes': ['6']},
    'LB': {'length': 7, 'mobile_prefixes': ['3', '7'], 'landline_prefixes': ['1']},
    'PS': {'length': 9, 'mobile_prefixes': ['5', '5'], 'landline_prefixes': ['2']},
    'SY': {'length': 9, 'mobile_prefixes': ['9'], 'landline_prefixes': ['1']},
    'IQ': {'length': 10, 'mobile_prefixes': ['7'], 'landline_prefixes': ['1']},
    
    # North Africa
    'EG': {'length': 10, 'mobile_prefixes': ['1'], 'landline_prefixes': ['2']},
    'LY': {'length': 9, 'mobile_prefixes': ['9'], 'landline_prefixes': ['2']},
    'TN': {'length': 8, 'mobile_prefixes': ['2', '9'], 'landline_prefixes': ['7']},
    'DZ': {'length': 9, 'mobile_prefixes': ['5', '6', '7'], 'landline_prefixes': ['3']},
    'MA': {'length': 9, 'mobile_prefixes': ['6', '7'], 'landline_prefixes': ['5']},
    'MR': {'length': 8, 'mobile_prefixes': ['2'], 'landline_prefixes': ['4']},
    'SD': {'length': 9, 'mobile_prefixes': ['9'], 'landline_prefixes': ['1']},
    'SS': {'length': 9, 'mobile_prefixes': ['9'], 'landline_prefixes': ['1']},
    'SO': {'length': 8, 'mobile_prefixes': ['6', '7'], 'landline_prefixes': ['1']},
    'DJ': {'length': 8, 'mobile_prefixes': ['7'], 'landline_prefixes': ['2']},
    'KM': {'length': 7, 'mobile_prefixes': ['3'], 'landline_prefixes': ['2']},
    
    # Special Cases
    'YE': {'length': 9, 'mobile_prefixes': ['7'], 'landline_prefixes': ['1']},
    'EH': {'length': 9, 'mobile_prefixes': ['6'], 'landline_prefixes': ['5']}
}


# Arabic responses
RESPONSES = {
    "high_risk": "⚠️ **خطر عالي** ⚠️\nالرقم `{number}` الرقم مبلغ عنه. تجنب التعامل معه!",
    "medium_risk": "⚠️ تحذير ⚠️\nالرقم `{number}` مشبوه. كن حذرا.",
    "unreported": "ℹ️ تنبيه ℹ️\nالرقم `{number}` غير مسجل سابقا. .",
    "not_found": "✅ غير مبلغ عنه ✅\nالرقم `{number}` غير موجود في قواعدنا.",
    "invalid_format": "❌ خطأ في التنسيق ❌\nاستخدم:\n`/report 501234567`\n`/report ٠٥٠١٢٣٤٥٦٧`\n`/report +966501234567`",
    "help": "📌 *كيفية استخدام البوت:*\n\n1. لفحص رقم:\n   `/report 0512345678`\n2. للمساعدة:\n   `/help`\n3. لبدء المحادثة:\n   `/start`"
}

def load_number_lists():
    """تحميل الأرقام من الملفات"""
    number_lists = {
        "high_risk": [],
        "medium_risk": [],
        "unreported": []
    }
    for risk in number_lists:
        try:
            with open(f"data/{risk}_numbers.txt", "r", encoding='utf-8') as f:
                number_lists[risk] = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            open(f"data/{risk}_numbers.txt", "w", encoding='utf-8').close()
    return number_lists

def normalize_number(raw_number):
    # Convert Arabic numerals to English and clean input
    eastern_to_west = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    cleaned = raw_number.translate(eastern_to_west)
    cleaned = re.sub(r'\D', '', cleaned)  # Remove all non-digits

    # Already in international format?
    for code in ARABIAN_COUNTRY_CODES.values():
        code_digits = code.lstrip('+')
        if cleaned.startswith(code_digits):
            return f"+{code_digits}{cleaned[len(code_digits):]}"

    # Priority: Yemen (like 733xxxxxx), then Iraq (starts with 7 but longer)
    if cleaned.startswith('7') and len(cleaned) == 9:
        return '+967' + cleaned
    if cleaned.startswith('7') and len(cleaned) == 10:
        return '+964' + cleaned

    # Match all patterns
    for country, pattern in COUNTRY_PATTERNS.items():
        prefixes = pattern['mobile_prefixes'] + pattern['landline_prefixes']
        if any(cleaned.startswith(p) for p in prefixes) and len(cleaned) == pattern['length']:
            return ARABIAN_COUNTRY_CODES[country] + cleaned

    # Fallback to Saudi Arabia 9-digit format
    return '+966' + cleaned[-9:]

def search_number(raw_number):
    normalized = normalize_number(raw_number)
    number_lists = load_number_lists()

    for risk_level, numbers in number_lists.items():
        for stored in numbers:
            cleaned = stored.strip()

            # Compare directly if stored number is formatted
            if cleaned == normalized:
                return (cleaned, risk_level)

            # Compare after normalization in case of raw stored number
            if normalize_number(cleaned) == normalized:
                return (cleaned, risk_level)

    return (None, "not_found")


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /report"""
    if not context.args:
        await update.message.reply_text(RESPONSES["invalid_format"])
        return
    
    raw_number = ' '.join(context.args)
    stored_number, risk_level = search_number(raw_number)
    
    response = RESPONSES[risk_level].format(
        number=stored_number if stored_number else raw_number
    )
    await update.message.reply_text(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    await update.message.reply_text(RESPONSES["help"], parse_mode="Markdown")

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any non-command messages"""
    if not update.message.text.startswith('/'):
        await update.message.reply_text(RESPONSES["help"], parse_mode="Markdown")


async def verify_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """For admins to test normalization"""
    if not context.args:
        await update.message.reply_text("Usage: /verify 0501234567")
        return
    
    raw = ' '.join(context.args)
    normalized = normalize_number(raw)
    
    await update.message.reply_text(
        f"🔍 *Normalization Result*\n"
        f"Original: `{raw}`\n"
        f"Normalized: `{normalized}`",
        parse_mode="Markdown"
    )
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle blocked users and other errors"""
    if isinstance(context.error, Forbidden):
        print(f"⚠️ User blocked the bot: {update.effective_user.id}")
    else:
        print(f"⚠️ Error: {context.error}")

if __name__ == "__main__":
    TOKEN = "7156251484:AAF-GksjFZe1FZ43_sbJcCML7NJlMt4206U"
    app = Application.builder().token(TOKEN).build()
    app.add_error_handler(error_handler)
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("verify", verify_number))  # <-- New handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))
    app.add_handler(CommandHandler("start", start))
    
    print("البوت يعمل...")
    while True:
        try:
            app.run_polling()
        except Exception as e:
            print(f"Error: {e}. Restarting...")
            time.sleep(5)
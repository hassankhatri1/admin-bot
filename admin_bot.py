#!/usr/bin/env python3
import logging, qrcode, io, json, os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8622574551:AAHDaXzNKYk7RULYptDKdIkTIAFMkbVkHzc")
ADMIN_ID  = 8239453740

DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r") as f: return json.load(f)
    return {"upi":"yourname@upi","username":"@YourUsername","price":"99","links":[],
            "premium_image":"","demo_video":"",
            "welcome_text":"🎉 *Welcome!*\n\nHamari service mein aapka swagat hai.\n\nPayment ke liye /pay likho.",
            "users":{},"history":[]}

def save_data(data):
    with open(DATA_FILE,"w") as f: json.dump(data,f,indent=2,ensure_ascii=False)

data = load_data()
(WAIT_UPI,WAIT_USER,WAIT_PRICE,WAIT_LINK,WAIT_IMG,WAIT_VID,WAIT_WELCOME,WAIT_PVID)=range(8)
logging.basicConfig(level=logging.INFO)

def is_admin(uid): return uid==ADMIN_ID

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Change UPI",callback_data="upi"),
         InlineKeyboardButton("👤 Change Username",callback_data="uname")],
        [InlineKeyboardButton("💰 Change Price",callback_data="price"),
         InlineKeyboardButton("🔗 Add Links",callback_data="link")],
        [InlineKeyboardButton("🖼 Premium Image",callback_data="img"),
         InlineKeyboardButton("🎬 Process Video",callback_data="pvid")],
        [InlineKeyboardButton("📹 Add Demo Video",callback_data="demo"),
         InlineKeyboardButton("❌ Remove Demo",callback_data="remdemo")],
        [InlineKeyboardButton("👥 Users List",callback_data="users"),
         InlineKeyboardButton("📋 History",callback_data="history")],
        [InlineKeyboardButton("✏️ Welcome Text",callback_data="welcome"),
         InlineKeyboardButton("📱 UPI QR Code",callback_data="qr")],
        [InlineKeyboardButton("📊 Stats",callback_data="stats")],
    ])

def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back",callback_data="back")]])

async def start(update:Update,context):
    user=update.effective_user
    uid=str(user.id)
    if uid not in data["users"]:
        data["users"][uid]={"name":user.full_name,"username":user.username or "N/A","joined":datetime.now().strftime("%Y-%m-%d %H:%M")}
        save_data(data)
    if is_admin(user.id):
        await update.message.reply_text("👑 *Welcome Admin*\n_Panel manage karo_",parse_mode="Markdown",reply_markup=main_kb())
    else:
        await update.message.reply_text(data["welcome_text"],parse_mode="Markdown")

async def pay(update:Update,context):
    await update.message.reply_text(f"💳 *Payment Details*\n\nUPI: `{data['upi']}`\nAmount: ₹{data['price']}\nUsername: {data['username']}\n\n_Payment ke baad screenshot bhejo_",parse_mode="Markdown")

async def button(update:Update,context):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id
    if not is_admin(uid):
        await q.edit_message_text("❌ Access Denied!")
        return ConversationHandler.END
    cb=q.data
    if cb=="back":
        await q.edit_message_text("👑 *Admin Panel*",parse_mode="Markdown",reply_markup=main_kb())
        return ConversationHandler.END
    elif cb=="upi":
        await q.edit_message_text(f"💳 Current: `{data['upi']}`\n\nNaya UPI bhejo:",parse_mode="Markdown")
        return WAIT_UPI
    elif cb=="uname":
        await q.edit_message_text(f"👤 Current: `{data['username']}`\n\nNaya username bhejo:",parse_mode="Markdown")
        return WAIT_USER
    elif cb=="price":
        await q.edit_message_text(f"💰 Current: ₹{data['price']}\n\nNayi price bhejo:",parse_mode="Markdown")
        return WAIT_PRICE
    elif cb=="link":
        links="\n".join(data["links"]) if data["links"] else "Koi link nahi"
        await q.edit_message_text(f"🔗 Links:\n{links}\n\nNaya link bhejo:")
        return WAIT_LINK
    elif cb=="img":
        await q.edit_message_text("🖼 Image URL bhejo:")
        return WAIT_IMG
    elif cb=="pvid":
        await q.edit_message_text("🎬 Video link bhejo:")
        return WAIT_PVID
    elif cb=="demo":
        await q.edit_message_text("📹 Demo video link bhejo:")
        return WAIT_VID
    elif cb=="remdemo":
        data["demo_video"]=""
        save_data(data)
        await q.edit_message_text("✅ Demo remove ho gaya!",reply_markup=back_kb())
        return ConversationHandler.END
    elif cb=="welcome":
        await q.edit_message_text(f"✏️ Current:\n{data['welcome_text']}\n\nNaya text bhejo:")
        return WAIT_WELCOME
    elif cb=="qr":
        await gen_qr(q,context)
        return ConversationHandler.END
    elif cb=="users":
        txt=f"👥 *Total: {len(data['users'])}*\n\n"+"".join(f"• {v['name']} | @{v['username']} | {v['joined']}\n" for v in list(data["users"].values())[-15:]) if data["users"] else "Koi user nahi."
        await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=back_kb())
        return ConversationHandler.END
    elif cb=="history":
        txt="📋 *History:*\n\n"+"\n".join(f"• {h}" for h in data["history"][-10:]) if data["history"] else "Koi history nahi."
        await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=back_kb())
        return ConversationHandler.END
    elif cb=="stats":
        await q.edit_message_text(f"📊 *Stats*\n\n👥 Users: {len(data['users'])}\n💳 UPI: `{data['upi']}`\n💰 Price: ₹{data['price']}\n🔗 Links: {len(data['links'])}\n📹 Demo: {'✅' if data['demo_video'] else '❌'}\n🖼 Image: {'✅' if data['premium_image'] else '❌'}",parse_mode="Markdown",reply_markup=back_kb())
        return ConversationHandler.END

async def gen_qr(q,context):
    upi_url=f"upi://pay?pa={data['upi']}&pn=Payment&am={data['price']}&cu=INR"
    qr=qrcode.QRCode(version=1,box_size=10,border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img=qr.make_image(fill_color="black",back_color="white")
    buf=io.BytesIO()
    img.save(buf,format="PNG")
    buf.seek(0)
    await context.bot.send_photo(chat_id=q.message.chat_id,photo=buf,
        caption=f"📱 *UPI QR*\n\n💳 `{data['upi']}`\n💰 ₹{data['price']}\n👤 {data['username']}",
        parse_mode="Markdown",reply_markup=back_kb())
    await q.message.delete()

async def got_upi(u,c):
    data["upi"]=u.message.text.strip()
    data["history"].append(f"UPI→{data['upi']} [{datetime.now().strftime('%d/%m %H:%M')}]")
    save_data(data)
    await u.message.reply_text(f"✅ UPI: `{data['upi']}`",parse_mode="Markdown",reply_markup=main_kb())
    return ConversationHandler.END

async def got_user(u,c):
    data["username"]=u.message.text.strip()
    save_data(data)
    await u.message.reply_text(f"✅ Username: `{data['username']}`",parse_mode="Markdown",reply_markup=main_kb())
    return ConversationHandler.END

async def got_price(u,c):
    data["price"]=u.message.text.strip().replace("₹","")
    save_data(data)
    await u.message.reply_text(f"✅ Price: ₹{data['price']}",reply_markup=main_kb())
    return ConversationHandler.END

async def got_link(u,c):
    data["links"].append(u.message.text.strip())
    save_data(data)
    await u.message.reply_text(f"✅ Link add! Total: {len(data['links'])}",reply_markup=main_kb())
    return ConversationHandler.END

async def got_img(u,c):
    data["premium_image"]=u.message.text.strip()
    save_data(data)
    await u.message.reply_text("✅ Image updated!",reply_markup=main_kb())
    return ConversationHandler.END

async def got_vid(u,c):
    data["demo_video"]=u.message.text.strip()
    save_data(data)
    await u.message.reply_text("✅ Demo video updated!",reply_markup=main_kb())
    return ConversationHandler.END

async def got_welcome(u,c):
    data["welcome_text"]=u.message.text.strip()
    save_data(data)
    await u.message.reply_text("✅ Welcome text updated!",reply_markup=main_kb())
    return ConversationHandler.END

async def got_pvid(u,c):
    data["history"].append(f"Video: {u.message.text.strip()[:40]} [{datetime.now().strftime('%d/%m %H:%M')}]")
    save_data(data)
    await u.message.reply_text("✅ Video saved!",reply_markup=main_kb())
    return ConversationHandler.END

async def cancel(u,c):
    await u.message.reply_text("❌ Cancel.",reply_markup=main_kb())
    return ConversationHandler.END

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(button)],
        states={
            WAIT_UPI:[MessageHandler(filters.TEXT&~filters.COMMAND,got_upi)],
            WAIT_USER:[MessageHandler(filters.TEXT&~filters.COMMAND,got_user)],
            WAIT_PRICE:[MessageHandler(filters.TEXT&~filters.COMMAND,got_price)],
            WAIT_LINK:[MessageHandler(filters.TEXT&~filters.COMMAND,got_link)],
            WAIT_IMG:[MessageHandler(filters.TEXT&~filters.COMMAND,got_img)],
            WAIT_VID:[MessageHandler(filters.TEXT&~filters.COMMAND,got_vid)],
            WAIT_WELCOME:[MessageHandler(filters.TEXT&~filters.COMMAND,got_welcome)],
            WAIT_PVID:[MessageHandler(filters.TEXT&~filters.COMMAND,got_pvid)],
        },
        fallbacks=[CommandHandler("cancel",cancel)],
    )
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("pay",pay))
    app.add_handler(conv)
    print("✅ Bot chalu hai!")
    app.run_polling()

if __name__=="__main__":
    main()

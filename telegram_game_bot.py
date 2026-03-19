# telegram_game_bot.py
import os
import sqlite3
from datetime import datetime
from telegram import Update, Bot # type: ignore
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes # type: ignore

# Inisialisasi database
def init_db():
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER,
                games_played INTEGER,
                last_played TEXT)''')
    conn.commit()
    conn.close()

# Tambah/update skor pemain
def update_score(username, score):
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM players WHERE username=?", (username,))
    player = c.fetchone()
    
    if player:
        new_score = player[2] + score
        new_games = player[3] + 1
        c.execute('''UPDATE players 
                    SET score=?, games_played=?, last_played=?
                    WHERE id=?''',
                  (new_score, new_games, datetime.now(), player[0]))
    else:
        c.execute('''INSERT INTO players (username, score, games_played, last_played)
                    VALUES (?, ?, 1, ?)''',
                  (username, score, datetime.now()))
    
    conn.commit()
    conn.close()

# Dapatkan leaderboard
def get_leaderboard(limit=10):
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('''SELECT username, score, games_played, last_played 
                FROM players 
                ORDER BY score DESC 
                LIMIT ?''', (limit,))
    leaderboard = c.fetchall()
    conn.close()
    return leaderboard

# Callback command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🎮 Game Score Bot\n\n'
        'Perintah yang tersedia:\n'
        '/addscore [username] [score] - Tambah skor pemain\n'
        '/leaderboard - Tampilkan leaderboard\n'
        '/reset - Reset semua data\n'
        '/help - Bantuan'
    )

async def add_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('⚠️ Format: /addscore [username] [score]')
        return
    
    username = args[0]
    try:
        score = int(args[1])
    except ValueError:
        await update.message.reply_text('⚠️ Score harus angka!')
        return
    
    update_score(username, score)
    await update.message.reply_text(f'✅ Skor {username} berhasil ditambahkan: {score}')

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leaderboard = get_leaderboard()
    
    if not leaderboard:
        await update.message.reply_text('❌ Belum ada data skor')
        return
    
    msg = '🏆 **LEADERBOARD**\n\n'
    for i, player in enumerate(leaderboard, 1):
        msg += f'{i}. {player[0]} - {player[1]} pts\n'
        msg += f'   Games: {player[2]}, Last: {player[3][:16]}\n\n'
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('DELETE FROM players')
    conn.commit()
    conn.close()
    await update.message.reply_text('🗑️ Data berhasil direset')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '📚 **BANTUAN BOT**\n\n'
        'Bot ini digunakan untuk memantau skor game Color Tap.\n\n'
        'Cara penggunaan:\n'
        '1. Setiap kali game selesai, gunakan /addscore\n'
        '2. Cek leaderboard dengan /leaderboard\n'
        '3. Data otomatis tersimpan di database'
    )

def main():
    # Inisialisasi
    init_db()
    
    # Token bot dari @BotFather
    BOT_TOKEN = '8699818014:AAGPo1C3a-HI4eEeCSko63eZ4_NDHrM-9o0'
    
    # Setup aplikasi
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handler
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('addscore', add_score))
    application.add_handler(CommandHandler('leaderboard', leaderboard))
    application.add_handler(CommandHandler('reset', reset))
    application.add_handler(CommandHandler('help', help_command))
    
    # Jalankan bot
    print('🚀 Bot sedang berjalan...')
    application.run_polling()

if __name__ == '__main__':
    main()
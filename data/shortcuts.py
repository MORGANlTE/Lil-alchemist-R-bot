import discord
from discord.ext import commands
import sqlite3

# Discord.py
async def sync_guilds(guilds, tree):
  if(guilds == []):
    await tree.sync()
    print("[V] Synced Tree")
  else:
    for guild in guilds:
      await tree.sync(guild=guild)
    print("[V] Synced Trees: " + str(guilds))


# Database shortcuts:
  
def setup_database(dbfile):
    conn = sqlite3.connect(dbfile)
    create_leaderboard_if_doesnt_exist(conn)
    conn.close()

def create_leaderboard_if_doesnt_exist(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            userid TEXT,
            gems INTEGER
        )
    ''')
    conn.commit()

def add_gems_to_user(userid, gems, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT id, gems FROM users WHERE userid = ?", (userid,))
  user_data = cursor.fetchone()

  if user_data is None:
      if gems < 0:
          gems = 0
      cursor.execute("INSERT INTO users (userid, gems) VALUES (?, ?)", (userid, gems))
  else:
      current = user_data[1]
      if user_data[1] + gems < 0:
          gems = 0
          current = 0
      cursor.execute("UPDATE users SET gems = ? WHERE userid = ?", (current + gems, userid))

  conn.commit()
  conn.close()

def get_top_users(dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()

  # Retrieve the top 3 users from the database
  cursor.execute("SELECT id, userid, gems FROM users ORDER BY gems DESC LIMIT 3")
  top_users = cursor.fetchall()
  conn.close()
  return top_users

def get_users_gems(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT id, userid, gems FROM users WHERE userid = ?", (userid,))
  user_data = cursor.fetchone()
  conn.close()
  if user_data is None:
      return 0
  else:
      return user_data[2]
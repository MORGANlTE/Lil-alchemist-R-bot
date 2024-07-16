import sqlite3
import os
import math
import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import io
from datetime import datetime, timedelta
import json
from data.shortcuts import *

def calculate_level(exp):
    return math.ceil((-3 + math.sqrt(exp)) / 2)

def how_much_exp(level):
    return (2*(level-1) +3)**2

def chin_avatar_calculator(level):
    # final img
    if level >= 100:
        return 16
    modulus = level // 5
    if modulus > 15:
        modulus = 15

    if modulus <= 0:
        modulus = 0
    
    
    return modulus
       
    

def add_experience_to_user(userid, exp, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT id, exp, lastupdated FROM users WHERE userid = ?", (userid,))
  user_data = cursor.fetchone()
  current = 0
  if user_data is None:
    cursor.execute("INSERT INTO users (userid, exp) VALUES (?, ?)", (userid, exp))
  else:
      if user_data[1] is None:
        current = 0
      else:
        current = user_data[1]

      # if the last updated is not 30sec ago, reset the exp
      # Check if user_data_time + 30 is less than current date & time
      now = datetime.now()
      date_from_db_plus_5_seconds = 0
      if user_data[2] is not None:
        date_from_db_plus_5_seconds = (datetime.fromtimestamp(float(user_data[2])) + timedelta(seconds=5)).timestamp()
      if (date_from_db_plus_5_seconds > now.timestamp()):
          conn.commit()
          conn.close()
          return False
      
      cursor.execute("UPDATE users SET exp = ? WHERE userid = ?", (current + exp, userid))
      cursor.execute("UPDATE users SET lastupdated = ? WHERE userid = ?", (now.timestamp(), userid))
  currentlvl = calculate_level(current)
  newlvl = calculate_level(current + exp)
    # add the users pfps for the levels
  add_user_pfps_for_levels(userid, currentlvl, newlvl, conn)

  conn.commit()
  conn.close()

  return {"exptotal": current + exp, "levelup": currentlvl!=newlvl} # did we level up or nah?

def get_experience(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT exp FROM users WHERE userid = ?", (userid,))
  user_exp = cursor.fetchone()
  conn.close()
  if user_exp is None:
    return 0
  else:
    return user_exp[0]
  
def get_experience_From_db_itself(userid, db_connection):
  conn = db_connection
  cursor = conn.cursor()
  cursor.execute("SELECT exp FROM users WHERE userid = ?", (userid,))
  user_exp = cursor.fetchone()
  if user_exp is None:
    return 0
  else:
    return user_exp[0]
  
def get_custom_pfp(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT current_pfp FROM users WHERE userid = ?", (userid,))
  user_pfp = cursor.fetchone()
  conn.close()
  if user_pfp[0] is None:
    return "0"
  else:
    return user_pfp[0]
  
def get_pfps(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT pfps FROM users WHERE userid = ?", (userid,))
  pfps = cursor.fetchone()
  conn.close()
  if pfps[0] is None:
    return '["0"]'
  else:
    return pfps[0]
  
def set_custom_pfp(userid, pfp, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("UPDATE users SET current_pfp = ? WHERE userid = ?", (pfp, userid))
  conn.commit()
  conn.close()
  

async def make_profile_picture(discord_name, discord_avatar, exp, gems, winstreak, leaderboard_rank_user, pfpchin):
  if leaderboard_rank_user is None:
    leaderboard_rank_user = 0

  response = requests.get(discord_avatar)
  avatar = Image.open(io.BytesIO(response.content))
  avatar = avatar.resize((200, 200))

  background = Image.new('RGB', (800, 200), (10, 20, 30))
  # zoom in on the background
  # make it so the avatar is a circle
  mask = Image.new('L', (180, 180), 0)
  draw = ImageDraw.Draw(mask)
  radius = 20  # Adjust the radius to control the roundness of the corners
  draw.rounded_rectangle([(0, 0), (180, 180)], radius, fill=255)
  avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
  avatar = avatar.convert("RGBA")  # Convert avatar image to RGBA mode
  avatar.putalpha(mask)
  
  # put the avatar on the background
  background.paste(avatar, (10, 10), avatar)

  # Get the absolute path of the current file
  current_dir = os.path.dirname(os.path.abspath(__file__))

  # Specify the relative path to the font file from the current file's directory
  font_path = os.path.join(current_dir, "fonts/")
  images = os.path.join(current_dir, "data_images/")

  # Load the font using the absolute path
  titlefont = ImageFont.truetype(font_path+"Sora-Bold.ttf", 50)
  font = ImageFont.truetype(font_path+"Sora-Regular.ttf", 20)


  draw = ImageDraw.Draw(background)
  draw.text((200, 15), discord_name, (255, 255, 255), font=titlefont)
  draw.text((240, 150), str(winstreak), (255, 255, 255), font=font)
  draw.text((320, 150), str(gems), (255, 255, 255), font=font)
  draw.text((520, 150), "#" + str(leaderboard_rank_user), (255, 255, 255), font=font)

  # draw a fire next to the winstreak
  fire = Image.open(images+"Fire.png")
  fire = fire.resize((40, 40))
  background.paste(fire, (200, 140), fire)
  
  # draw a diamond next to the gems
  diamond = Image.open(images+"Diamond.png")
  diamond = diamond.resize((40, 40))
  background.paste(diamond, (280, 142), diamond)

  # draw a trophy next to the leaderboard rank
  trophy = Image.open(images+"trophy.png")
  trophy = trophy.resize((40, 40))
  background.paste(trophy, (480, 142), trophy)

  # make a progress bar, with the percentage of the exp
  try:
    percentage_towards_next_level = (exp - how_much_exp(calculate_level(exp))) / (how_much_exp(calculate_level(exp)+1) - how_much_exp(calculate_level(exp)))
  except:
    percentage_towards_next_level = 0
  normal_color = (15, 50, 120)
  if exp >= 41209:
     normal_color = (50, 15, 10)
  draw.text((200, 80), "Level " + str(calculate_level(exp)), (255, 255, 255), font=font)
  draw.text((520, 80), f"{exp}/{how_much_exp(calculate_level(exp)+1)}", (255, 255, 255), font=font)
  draw.rectangle([200, 110, 600, 130], fill=(255, 255, 255))
  draw.rectangle([200, 110, 200 + 400*percentage_towards_next_level, 130], fill=normal_color)

  # we want the Chin based on the users level

  # chin_avatar_calculator(calculate_level(exp))
  chin = Image.open(images + "Chins/" + pfpchin)
  # if the user is the highest on the leaderboard, make them top1.png, else top2.png or top3.png
  # userid = str(userid)
  # if(userid == top3[0][0]):
  #   chin = Image.open(images + "Chins/top1.png")
  # elif(userid == top3[1][0]):
  #   chin = Image.open(images + "Chins/top2.png")
  # elif(userid == top3[2][0]):
  #   chin = Image.open(images + "Chins/top3.png")
  
  aspect_ratio = chin.width / chin.height
  new_height = int(200 / aspect_ratio)
  chin = chin.resize((200, new_height))
  background.paste(chin, (650, 30), chin)

  # if folder does not exist, create it
  if not os.path.exists("important_images"):
    os.makedirs("important_images")
  background.save(f"important_images/{discord_name}.png")
  fileM = discord.File(
            f"./important_images/{discord_name}.png",
            filename=f"{discord_name}.png",
        )
  return fileM

def claim_daily(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT lastlogin FROM users WHERE userid = ?", (userid,))
  lastlogin = cursor.fetchone()
  if lastlogin is None or lastlogin[0] is None:
    lastlogin = 0
  else:
    lastlogin = float(lastlogin[0])

# check if less than 23 h, calculated
  if datetime.now().timestamp() - lastlogin < 82800:
    conn.close()
    time_difference = timedelta(seconds=82800 - (datetime.now().timestamp() - lastlogin))
    hours = time_difference.seconds // 3600
    minutes = (time_difference.seconds // 60) % 60
    time_string = f"{hours}h {minutes}min"
    return False, time_string
  else:
    getter = cursor.execute("SELECT gems, winstreak, exp FROM users WHERE userid = ?", (userid,))
    # get the users level
    user = getter.fetchone()
    if user is None:
      conn.close()
      return "User not found", False
    # gems should be 0 if it is null
    gems = user[0] if user[0] is not None else 0
    # winstreak = user[1] if user[1] is not None else 0
    exp = user[2] if user[2] is not None else 0

    standard = 200
    # add 1 gem per level
    standardgem_amount = standard + calculate_level(exp)

    cursor.execute("UPDATE users SET gems = ? WHERE userid = ?", (gems + standardgem_amount, userid))
    cursor.execute("UPDATE users SET lastlogin = ? WHERE userid = ?", (datetime.now().timestamp(), userid))

    conn.commit()
    conn.close()
    return True, f"You gained **{str(standardgem_amount)}** :gem: \n"
  
def get_highest_exp(dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT id, userid, gems, winstreak, exp FROM users ORDER BY exp DESC LIMIT 5")
  users = cursor.fetchall()
  conn.close()
  if users is None:
    return None
  return users

def get_user_pfps_db(userid, db_connection):
  cursor = db_connection.cursor()
  cursor.execute("SELECT pfps FROM users WHERE userid = ?", (userid,))
  pfps = cursor.fetchone()[0]
  if pfps is None:
    currentexp = get_experience_From_db_itself(userid, db_connection)
    add_user_pfps_for_levels(userid, 0, calculate_level(currentexp), db_connection)
    pfps = get_user_pfps_db(userid, db_connection)
  # make the list a set json
  pfps = json.loads(pfps)

  return pfps

def add_user_pfps_for_levels(userid, currentlvl, newlvl, db_connection):
  # get user pfps
  pfps = get_user_pfps_db(userid, db_connection)
  oldpfps = pfps.copy()

  # check if we unlocked a new pfp
  currentlvlchin = chin_avatar_calculator(newlvl)
  if pfps is None:
    currentexp = get_experience_From_db_itself(userid, db_connection)
    add_user_pfps_for_levels(userid, 0, calculate_level(currentexp), db_connection)
    pfps = get_user_pfps_db(userid, db_connection)
  # make the list a set json
  if type(pfps) == str:
    pfps = json.loads(pfps)
  for i in range(currentlvlchin):
    if str(i+1) not in pfps:
      pfps.append(str(i+1))

  # order the list
  pfps = sorted(pfps, key=lambda x: int(x))

  if pfps == oldpfps: # no updates needed
    return

  cursor = db_connection.cursor()
  # set the new pfps
  cursor.execute("UPDATE users SET pfps = ? WHERE userid = ?", (json.dumps(pfps), userid))
  db_connection.commit()

def add_pfp(userid, pfp, db_file):
  db_connection = sqlite3.connect(db_file)
  pfps = get_user_pfps_db(userid, db_connection)
  if pfp not in pfps:
    pfps.append(pfp)
  else:
     return
  # order the list
  pfps = sorted(pfps, key=lambda x: int(x))
  # set the new pfps
  cursor = db_connection.cursor()
  cursor.execute("UPDATE users SET pfps = ? WHERE userid = ?", (json.dumps(pfps), userid))
  db_connection.commit()
  db_connection.close()

def get_store_pfps_not_bought(userid, dbfile):
  db_connection = sqlite3.connect(dbfile)
  pfps = get_user_pfps_db(userid, db_connection)
  db_connection.close()

  # store pfps:
  #imgId : {price: name}
  store_pfps = get_allstore_pfps()

  # get the ones that are not bought
  not_bought = []
  for key in store_pfps.keys():
    if str(key) not in pfps:
      not_bought.append(key)

  # get me the names of the not bought ones
  return_not_bought = {}
  for i in not_bought:
    return_not_bought[i] = get_description_pfp(i)

  return return_not_bought


def get_allstore_pfps():
  store_pfps = {
      17: {0:"Bird"},
      18: {3000:"Raging Bird"},
      19: {4000:"Messenger Bird"},
      20: {7000:"Atomic Burrito"},
      21: {10000:"King of the Heap"},
  }
  return store_pfps

def buy_pfp(pfpid, user_id, dbfile):
    # Open a database connection
    conn = sqlite3.connect(dbfile)
    try:
        # get pfp from the store
        pfpid = int(pfpid)
        # check if we already have this pfp
        pfps = get_user_pfps_db(user_id, conn)
        if str(pfpid) in pfps:
            return False, "You already have this avatar"
        store_pfps = get_allstore_pfps()
        if pfpid not in store_pfps.keys():
            return False, "This pfp does not exist in the store"
        
        # get the price
        price = store_pfps[pfpid].keys()
        # get the first element of the dict
        price = list(price)[0]
        # get the users gems
        user_gems = get_users_gems_and_top_percentage(user_id, dbfile)[0]
        if user_gems < price:
            return False, "You do not have enough gems to buy this pfp"

        # add the pfp to the users pfps

        add_pfp(user_id, str(pfpid), dbfile)
        return True, "Avatar purchased successfully"
    finally:
        conn.close()


def set_leaderboard_rank_pfps(rank, userid, dbfile):
  rank = str(rank)
  if rank == "1":
    pfps = ["23", "24", "25"]
  elif rank == "2":
    pfps = ["24", "25"]
  elif rank == "3":
    pfps = ["25"]
  else:
    return
  for pfp in pfps:
    add_pfp(userid, pfp, dbfile)


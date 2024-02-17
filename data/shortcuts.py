import discord
from discord.ext import commands
import sqlite3
import requests
from bs4 import BeautifulSoup
from random import randint
from data.essentials.data.question import Question
from random import shuffle
from data.data_grabber import get_rarity_and_form_etc

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
    check_winstreak_exists_in_users(conn)
    conn.close()

def create_leaderboard_if_doesnt_exist(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            userid TEXT,
            gems INTEGER,
            winstreak INTEGER
        )
    ''')
    conn.commit()

def check_winstreak_exists_in_users(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    table_info = cursor.fetchall()
    winstreak_exists = False
    for column in table_info:
        if column[1] == "winstreak":
            winstreak_exists = True
            break
    if not winstreak_exists:
        cursor.execute("ALTER TABLE users ADD COLUMN winstreak INTEGER")
        conn.commit()

def add_gems_to_user(userid, gems, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT id, gems FROM users WHERE userid = ?", (userid,))
  user_data = cursor.fetchone()
  current = 0
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
  return current + gems

def update_winstreak(userid, dbfile, amount):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT id, winstreak FROM users WHERE userid = ?", (userid,))
  user_data = cursor.fetchone()
  current = 0
  if user_data is None:
      if amount < 0:
          amount = 0
      cursor.execute("INSERT INTO users (userid, winstreak) VALUES (?, ?)", (userid, amount))
  else:
      cursor.execute("UPDATE users SET winstreak = ? WHERE userid = ?", (amount, userid))

  conn.commit()
  conn.close()
  return current + amount

def get_winstreak(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT winstreak FROM users WHERE userid = ?", (userid,))
  user_winstreak = cursor.fetchone()
  if user_winstreak is None:
    return 0
  else:
    return user_winstreak[0]

def get_top_users(dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()

  # Retrieve the top 3 users from the database
  cursor.execute("SELECT id, userid, gems FROM users ORDER BY gems DESC LIMIT 5")
  top_users = cursor.fetchall()
  conn.close()
  return top_users

def get_users_gems_and_top_percentage(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT gems FROM users WHERE userid = ?", (userid,))
  user_gems = cursor.fetchone()
  if user_gems is None:
    return 0, 0
  else:
    cursor.execute("SELECT COUNT(*) FROM users WHERE gems > ?", (user_gems[0],))
    higher_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    top_percentage = (higher_users / total_users) * 100
    conn.close()
    return user_gems[0], top_percentage



# Trivia Shortcuts
def search_diamonds():
  url = f"https://lil-alchemist.fandom.com/wiki/Card_Combinations/Diamond"
  resp = requests.get(url)
  soup = BeautifulSoup(resp.content, "html.parser")
  table = soup.find("table", class_="article-table sortable")

  trs = table.find_all("tr")[1:]
  return trs

def get_question_combos():
  # select random one
  alldiamonds = search_diamonds()
  # generate 3 numbers, between randint(0, len(alldiamonds) - 1), that are not the same
  randomnr1 = randint(0, len(alldiamonds) - 1)
  randomnr2 = randint(0, len(alldiamonds) - 1)
  randomnr3 = randint(0, len(alldiamonds) - 1)
    
  tr = alldiamonds[randomnr1]
  tr2 = alldiamonds[randomnr2]
  tr3 = alldiamonds[randomnr3]

  combo1 = tr.find_all("td")[0].text
  combo2 = tr.find_all("td")[1].text

  real_result = get_result(tr)
  fake_result1 = get_result(tr2)
  
  # Ensure fake_result1 is not the same as real_result
  while fake_result1 == real_result:
    randomnr2 = randint(0, len(alldiamonds) - 1)
    tr2 = alldiamonds[randomnr2]
    fake_result1 = get_result(tr2)
  
  fake_result2 = get_result(tr3)
  
  # Ensure fake_result2 is not the same as real_result or fake_result1
  while fake_result2 == real_result or fake_result2 == fake_result1:
    randomnr3 = randint(0, len(alldiamonds) - 1)
    tr3 = alldiamonds[randomnr3]
    fake_result2 = get_result(tr3)

  # add all 3 results to a list
  results = []
  results.append(real_result)
  results.append(fake_result1)
  results.append(fake_result2)

  shuffle(results)
  correct_answer_index = results.index(real_result)

  question = Question(
            f"What does {combo1} & {combo2} make?",
            results,
            f"https://iili.io/Jc4pJa4.png",
            correct_answer_index,
        )
  
  return question

def get_result(tr):
  return tr.find_all("td")[2].text

  

def get_question_ability():
  # select random one
  alldiamonds = search_diamonds()
  tr = alldiamonds[randint(0, len(alldiamonds) - 1)]
  tds = tr.find_all("td")

  third_td = tds[2].text.strip()
  third_td = third_td.replace(" ", "_").replace("_and_", "_And_").replace("\n", "_")
  # get the url of the card and replace enters with nothing
  url = f"https://lil-alchemist.fandom.com/wiki/{third_td}"
  resp = requests.get(url)
  soup = BeautifulSoup(resp.content, "html.parser")

  card1_image = get_image(soup)

  (
        description,
        base_attack,
        base_defense,
        base_power,
        rarity,
        form,
        fusion,
        where_to_acquire,
        level_stats,
        recipes,
        combos,
    ) = get_rarity_and_form_etc(soup)
  # get the ability/fusion is done
  # now we need to add all others
  list_of_abilities = ["Crushing Blow","Protection", "Counter Attack", "Absorb", "Critical Strike", "Curse"]
  # remove the ability from the list
  list_of_abilities.remove(fusion)

  # get 2 random abilities from the list
  ability1 = list_of_abilities[randint(0, len(list_of_abilities) - 1)]
  ability2 = list_of_abilities[randint(0, len(list_of_abilities) - 1)]
  while ability2 == ability1:
    ability2 = list_of_abilities[randint(0, len(list_of_abilities) - 1)]
  
  # add the 3 abilities to a list
  abilities = []
  abilities.append(fusion)
  abilities.append(ability1)
  abilities.append(ability2)

  shuffle(abilities)
  correct_answer_index = abilities.index(fusion)

  question = Question(
            f"What ability does {third_td.replace('_', ' ')} have?",
            abilities,
            card1_image,
            correct_answer_index,
        )
  
  return question



# Beautifulsoup shortcuts

def get_image(soup):
        figure_element = soup.find("figure", class_="pi-item pi-image")
        if figure_element:
            a_tag = figure_element.find("a")
            if a_tag and "href" in a_tag.attrs:
                image_url = a_tag["href"]
            else:
                print("No image URL found within the <a> tag.")
        else:
            print("No <figure> element with class 'pi-item pi-image' found.")
            image_url = None
        return image_url
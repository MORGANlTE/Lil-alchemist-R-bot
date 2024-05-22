import discord
from discord.ext import commands
import sqlite3
import requests
from bs4 import BeautifulSoup
from random import randint
from data.essentials.data.question import Question
from random import shuffle
from data.data_grabber import get_rarity_and_form_etc
from data.data_grabber import get_fusion_url, get_embedcolor
from data.custom_cards.custom_card_names import custom_names

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
    check_exp_exists_in_users(conn)
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

def check_exp_exists_in_users(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    table_info = cursor.fetchall()
    exp_exists = False
    lastupdated_exists = False
    lastlogin_exists = False

    for column in table_info:
        if column[1] == "exp":
            exp_exists = True
            break
        
    for column in table_info:
        if column[1] == "lastupdated":
            lastupdated_exists = True
            break
        
    for column in table_info:
        if column[1] == "lastlogin":
            lastlogin_exists = True
            break
        
    if not exp_exists:
        cursor.execute("ALTER TABLE users ADD COLUMN exp INTEGER")
        conn.commit()
    if not lastupdated_exists: # lastupdated is the last time the user got exp
        cursor.execute("ALTER TABLE users ADD COLUMN lastupdated TEXT")
        conn.commit()
    if not lastlogin_exists: # lastupdated is the last time the user got exp
        cursor.execute("ALTER TABLE users ADD COLUMN lastlogin TEXT")
        conn.commit()

    conn.close()

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
      if user_data[1] is None:
        current = 0
      else:
        current = user_data[1]
      if current + gems < 0:
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

def get_top_users(dbfile, sortedByGems):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  # Retrieve the top 3 users from the database
  if sortedByGems:
    cursor.execute("SELECT id, userid, COALESCE(gems, 0), winstreak, exp FROM users ORDER BY COALESCE(gems, 0) DESC, winstreak DESC, exp DESC LIMIT 5")
  else:
    cursor.execute("SELECT id, userid, COALESCE(gems, 0), winstreak, exp FROM users ORDER BY exp DESC, COALESCE(gems, 0), winstreak DESC LIMIT 5")
  top_users = cursor.fetchall()
  conn.close()
  return top_users


def get_top_users_top_3(dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT userid FROM users ORDER BY exp DESC, COALESCE(gems, 0), winstreak DESC LIMIT 3")
  top_users = cursor.fetchall()
  conn.close()
  return top_users

def get_users_gems_and_top_percentage(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT gems, winstreak, exp FROM users WHERE userid = ?", (userid,))
  user_gems = cursor.fetchone()
  conn.close()
  return user_gems[0], user_gems[1], user_gems[2]

def get_levels(userid, dbfile):
  conn = sqlite3.connect(dbfile)
  cursor = conn.cursor()
  cursor.execute("SELECT exp FROM users WHERE userid = ?", (userid,))
  user_exp = cursor.fetchone()
  conn.close()
  if user_exp is None:
    return 0
  return user_exp[0]

# Wiki shortcuts
def check_if_custom_name(cardname):
  cardname = cardname.capitalize()
  if not cardname in custom_names:
     return False
  else:
    current_custom_card = custom_names[cardname]
    embed = discord.Embed(
        color=get_embedcolor(current_custom_card["rarity"]),
    )
    fusion = current_custom_card["fusion"]
    rarity = current_custom_card["rarity"]
    ability_img_url = get_fusion_url(current_custom_card["fusion"])
    img_url = current_custom_card["img_url"]
    recipes = current_custom_card["recipes"]
    combos = current_custom_card["combos"]

    embed.set_author(
        icon_url=ability_img_url,
        name=fusion,
    )
    # add url link to wiki
    embed.add_field(
        name="Custom Card",
        value=f"Suggested: `{current_custom_card['suggester']}`",
        inline=False,
    )
    embed.add_field(name="Full Name", value=current_custom_card["name"], inline=True)
    embed.add_field(name="Rarity", value=rarity, inline=True)
    embed.add_field(name="Description", value=current_custom_card["description"],inline=False)
    embed.set_thumbnail(url=img_url)
    levels_left = ""
    levels_right = ""
    
    for level in current_custom_card["level_stats"].items():
        level_text = f"{level[0]}  -  {level[1]['Attack']}/{level[1]['Defense']}\n"
        if int(level[0]) >= 4:
            levels_right += level_text
        else:
            levels_left += level_text

    embed.add_field(name="Levels", value=levels_left, inline=True)
    embed.add_field(name="** **", value=levels_right, inline=True)
    where_to_acquire = current_custom_card["where_to_acquire"]
    embed.add_field(
        name="Where to acquire", value=", ".join(where_to_acquire), inline=False
    )
    if fusion == "Orb":
        embed.add_field(
            name="Combos",
            value=f"Amount of Combos: {len(combos)}",
            inline=False,
        )

    else:
        combos_left = []
        combos_right = []
        counter = 0
        if rarity == "Onyx":
            # filter out all non onyx combos
            combos = [
                combo
                for combo in combos
                if "(Onyx)" in combo[0] and "(Onyx)" in combo[1]
            ]
        else:
            # filter out all onyx combos
            combos = [
                combo
                for combo in combos
                if not "(Onyx)" in combo[0] and not "(Onyx)" in combo[1]
            ]

        for recipe in recipes:
            if counter < (len(recipes) / 2):
                combos_left.append(f"{counter+1}.{recipe[1]} + {recipe[0]}")
            else:
                combos_right.append(f"{counter+1}.{recipe[1]} + {recipe[0]}")
            counter += 1
        
        # if empty combos, add a "/"
        if len(recipes) == 0:
            embed.add_field(name="Combos", value="/", inline=True)
            embed.add_field(name="** **", value="", inline=True)
        else:
            embed.add_field(name="Combos", value="\n".join(combos_left), inline=True)
            embed.add_field(name="** **", value="\n".join(combos_right), inline=True)

    # add underneath the author the rarity and form
    embed.set_footer(
        text=f"{cardname.title()} - {rarity} ~ ChinBot & LAR Wiki",
        icon_url=ability_img_url,
    )
    return embed

# Trivia Shortcuts
def search_rarity(rarity):
  url = f"https://lil-alchemist.fandom.com/wiki/Card_Combinations/{rarity}"
  resp = requests.get(url)
  soup = BeautifulSoup(resp.content, "html.parser")
  table = soup.find("table", class_="article-table sortable")

  trs = table.find_all("tr")[1:]
  return trs

def get_combos_from_page(soup):
  table = soup.find("table", id="mw-customcollapsible-combosTable")
  trs = table.find_all("tr")[1:]
  return trs

def get_question_combos():
  # select random one

  category = randint(0, 6)
  # more chance for diamond (cuz its harder to guess)

  allcombos = []
  if category == 0:
    allcombos = search_rarity("Bronze")
  elif category == 1:
    allcombos = search_rarity("Silver")
  elif category == 2:
    allcombos = search_rarity("Gold")
  else:
    allcombos = search_rarity("Diamond")
     
  randomnr1 = randint(0, len(allcombos) - 1)

  tr = allcombos[randomnr1]

  combo1 = tr.find_all("td")[0].text
  combo2 = tr.find_all("td")[1].text

  real_result = get_result(tr)
  # get the page of the real result
  url = f"https://lil-alchemist.fandom.com/wiki/{combo1.replace(' ', '_').strip()}"
  resp = requests.get(url)
  soup = BeautifulSoup(resp.content, "html.parser")

  combo1_image = get_image(soup)

  cardnames = []
  # get the cards from the list of trs
  for tr in get_combos_from_page(soup):
      cardnames.append(tr.find_all("td")[1].text)

  # make a set of the cardnames
  cardnames = set(cardnames)
  # remove the real result from the set
  cardnames.discard(real_result.strip())
  # get 2 random cards from the set
  card1 = cardnames.pop()
  card2 = cardnames.pop()

  # add all 3 results to a list
  results = []
  results.append(real_result.strip())
  results.append(card1.strip())
  results.append(card2.strip())

  shuffle(results)
  correct_answer_index = results.index(real_result.strip())

  question = Question(
          f"What does {combo1} & {combo2} make?",
          results,
          f"{combo1_image}",
          correct_answer_index,
      )

  return question

def get_result(tr):
  return tr.find_all("td")[2].text

  

def get_question_ability():
  rarity = randint(0, 3)
  alldiamonds = search_rarity("Diamond")

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
            print("No <figure> element with class 'pi-item pi-image' found.")
            image_url = None
        return image_url
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
import re
import traceback
from data.data_grabber import *
import metaphone

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
  
def setup_databases(dbfile, admindbfile):
    conn = sqlite3.connect(dbfile)
    create_leaderboard_if_doesnt_exist(conn)
    check_winstreak_exists_in_users(conn)
    check_exp_exists_in_users(conn)
    check_profilepictures_exist_in_users(conn)
    conn.close()
    # setup admin controls
    conn = sqlite3.connect(admindbfile)
    check_admin_guildandchannels_exist(conn)
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
    server_for_exp_exists = False

    for column in table_info:
        if column[1] == "exp":
            exp_exists = True
        if column[1] == "lastupdated":
            lastupdated_exists = True
        if column[1] == "lastlogin":
            lastlogin_exists = True
        if column[1] == "server_for_exp":
            server_for_exp_exists = True
        if exp_exists and lastupdated_exists and lastlogin_exists and server_for_exp_exists:
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
    if not server_for_exp_exists:
        cursor.execute("ALTER TABLE users ADD COLUMN server_for_exp TEXT DEFAULT '317710252369772544'")
        conn.commit()

def check_profilepictures_exist_in_users(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    table_info = cursor.fetchall()
    pfp_list_exists = False
    current_pfp_exists = False
    for column in table_info:
        if column[1] == "pfps":
            pfp_list_exists = True
        if column[1] == "current_pfp":
            current_pfp_exists = True
        if pfp_list_exists and current_pfp_exists:
            break

    if not pfp_list_exists:
        cursor.execute("ALTER TABLE users ADD COLUMN pfps TEXT")
        conn.commit()
    if not current_pfp_exists:
        cursor.execute("ALTER TABLE users ADD COLUMN current_pfp TEXT")
        conn.commit()

def check_admin_guildandchannels_exist(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loggingchannels (
            id INTEGER PRIMARY KEY,
            guildid TEXT,
            channelid TEXT
        )
    ''')
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
  if(user_gems is None):
    return 0, 0, 0, "-1"
  if user_gems[2] is None:
    user_gems = (user_gems[0], user_gems[1], 0)
     
  cursor.execute("SELECT COUNT(*) FROM users WHERE exp > ?", (user_gems[2],))
  user_rank = cursor.fetchone()[0] + 1

  # return the users current rank
  conn.close()
  #       gems,       winstreak,       exp,            rank 
  return user_gems[0], user_gems[1], user_gems[2], str(user_rank)

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
  list_of_abilities = ["Crushing Blow","Protection", "Counter Attack", "Absorb", "Critical Strike", "Curse", "Pillage", "Plunder"]
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

# Packview shortcuts

def get_pack_contents(pack):
    url_name = pack.replace(" ", "_")
    url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs/{url_name}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    return_cards = []

    try:
        div1 = soup.find_all("div", id="gallery-0")[0]
    except:
        return "Not found"
    
    aside = soup.find("aside").find("a").get("href").replace("/wiki/", "").strip()

    def loop_and_add_cards(cards):
       for card in cards:
        # find the img inside the card
        img = card.find("img")
        
        # name, stats, fusion
        return_cards.append([
           card.get("href").replace("/wiki/", "").strip(),
           img.get("alt"),
           fusion_to_emote(get_filename_from_url(img.get('data-caption')))
        ])

    gallery = soup.find("div", id="gallery-0")
    cards = gallery.find_all("a", class_="image link-internal")
    loop_and_add_cards(cards)

    gallery = soup.find("div", id="gallery-1")
    cards = gallery.find_all("a", class_="image link-internal")
    loop_and_add_cards(cards)
    

    return {"cards":return_cards, "img": aside}


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

# Discord emotes shortcuts
def fusion_to_emote(fusion):
  if fusion is None:
    return None
  fusion = fusion.replace("_", " ").strip().capitalize()

  if fusion == "Pierce":
      return "<:pierce:1251260068415012965>"
  elif fusion == "Crushing blow":
      return "<:cb:1251258459715014687>"
  elif fusion == "Block":
      return "<:block:1251258423765504112>"
  elif fusion == "Protection":
     return "<:pr:1251258185805987930>"
  elif fusion == "Reflect":
      return "<:reflect:1251258557236645929>"
  elif fusion == "Counter attack":
      return "<:ca:1251258446716600411>"
  elif fusion == "Siphon":
      return "<:siphon:1251258574156333166>"
  elif fusion == "Absorb":
      return "<:ab:1251258370305032365>"
  elif fusion == "Amplify":
      return "<:amplify:1251258389443645471>"
  elif fusion == "Criticalstrike":
     return "<:cs:1251258476517130263> "
  elif fusion == "Weaken":
     return "<:weaken:1251258603390767285>"
  elif fusion == "Curse":
      return "<:cu:1251258490026987532>"
  elif fusion == "Pillage":
      return "<:pillage:1251259075405283418>"
  elif fusion == "Plunder":
      return "<:plunder:1251259077452103751>"
  elif fusion == "Orb":
     return "<:orb:1251259896997871788>"
  

  else:
      return fusion
  
def get_filename_from_url(url):
  match = re.search(r"(?<=images/).+?\.png", url)
  if match:
    return match.group().split("/")[-1].replace(".png", "")
  else:
    return None
  
def find_closest_pack(user_input, word_list):
  # "borrowed" this code from Google Gemini
  if user_input.strip() == "Darkness":
     return "The Dark"
  user_metaphone = metaphone.doublemetaphone(user_input)[0]  # Use primary metaphone code
  distances = []

  for item in word_list:
    item_metaphone = metaphone.doublemetaphone(item)[0]
    distance = sum(a != b for a, b in zip(user_metaphone, item_metaphone))
    distances.append(distance)

  # Consider word length as a factor
  for i, item in enumerate(word_list):
    distances[i] += abs(len(user_input) - len(item)) * 0.5

  return word_list[distances.index(min(distances))]

# pfp shortcuts
def get_description_pfp(pfp_id):
  # pfps = {
  #     0: "Zombiechin",
  #     1: "Chinchilla - free",
  #     2: "Pilgrim Chin - lvl 5",
  #     3: "Chinzilla - lvl 10",
  #     4: "Aviator Chin - lvl 15",
  #     5: "Chinchilla Knight - lvl 20",
  #     6: "Wonderchin - lvl 25",
  #     7: "Chinchillalope - lvl 30",
  #     8: "Chin Cousteau - lvl 35",
  #     9: "Chinchilla Raider - lvl 40",
  #     10: "Candy King Chin - lvl 45",
  #     11: "Mozart Chin - lvl 50",
  #     12: "Chin Trooper - lvl 55",
  #     13: "Bionic Chinchilla - lvl 60",
  #     14: "Bone Chin - lvl 65",
  #     15: "Forest Chinchillas - lvl 70",
  #     16: "🎉 Mecha Chinzilla - lvl 100"
  #  }
  pfps = {
      0: "Free - Zombiechin",
      1: "lvl 5 - Chinchilla",
      2: "lvl 10 - Pilgrim Chin",
      3: "lvl 15 - Chinzilla",
      4: "lvl 20 - Aviator Chin",
      5: "lvl 25 - Chinchilla Knight",
      6: "lvl 30 - Wonderchin",
      7: "lvl 35 - Chinchillalope",
      8: "lvl 40 - Chin Cousteau",
      9: "lvl 45 - Chinchilla Raider",
      10: "lvl 50 - Candy King Chin",
      11: "lvl 55 - Mozart Chin",
      12: "lvl 60 - Chin Trooper",
      13: "lvl 65 - Bionic Chinchilla",
      14: "lvl 70 - Bone Chin",
      15: "lvl 75 - Forest Chinchillas",
      16: "lvl 100 - Mecha Chinzilla",
      17: "💎Free - Bird",
      18: "💎3000 - Raging Bird",
      19: "💎4000 - Messenger Bird",
      20: "💎7000 - Atomic Burrito",
      21: "💎10.000 - King of the Heap",
      22: "??? - Pirate Captain",
      23: "Rank 1 - Smokescreen",
      24: "Rank 2 - Slime Warrior",
      25: "Rank 3 - Soul Harvester",
      26: "??? - Angelfish"
  }
  return pfps[int(pfp_id)]

def chunk_list(lst, chunk_size):
    """Split a list into chunks of a specified size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def get_arena_powers():
  arena_powers = [
        {
            "name": "Tiebreaker",
            "emoji": "<:tiebreaker:1198288123407372348>",
            "description": "In the event of a tie, you win the matchup",
            "tiers": [
                {"tier": 1, "orb": 400}
            ]
        },
        {
            "name": "Combo Master",
            "emoji": "<:ComboMaster:1262860895911022613>",
            "description": "Start with 1 Orb filled at the beginning of each match",
            "tiers": [
                {"tier": 1, "orb": 1000}
            ]
        },
        {
            "name": "Master Healer",
            "emoji": "<:masterhealer:1262861006665814096>",
            "description": "You start with bonus HP",
            "tiers": [
                {"tier": 1, "power": 4, "emoji": "HP", "orb": 850},
                {"tier": 2, "power": 7, "emoji": "HP", "orb": 1065},
                {"tier": 3, "power": 10, "emoji": "HP", "orb": 1280}
            ]
        },
        {
            "name": "Master Elementalist",
            "emoji": "<:masterelementalist:1262861128782839958>",
            "description": "Opponents start with less HP",
            "tiers": [
                {"tier": 1, "power": 4, "emoji": "HP", "orb": 850},
                {"tier": 2, "power": 7, "emoji": "HP", "orb": 1065},
                {"tier": 3, "power": 10, "emoji": "HP", "orb": 1280}
            ]
        },
        {
            "name": "Master Enchanter",
            "emoji": "<:masterenchanter:1262861080716247224>",
            "description": "1 Orb added to max orb count",
            "tiers": [
                {"tier": 1, "orb": 700}
            ]
        },
        {
            "name": "Greed",
            "emoji": "<:greed:1262861161884549304>",
            "description": "Gain bonus coins at the end of each battle",
            "tiers": [
                {"tier": 1, "power": 20, "emoji": "%", "orb": 550},
                {"tier": 2, "power": 40, "emoji": "%", "orb": 690},
                {"tier": 3, "power": 60, "emoji": "%", "orb": 830}
            ]
        },
        {
            "name": "Quick Learner",
            "emoji": "<:QuickLearner:1262861395222069389>",
            "description": "Earn extra xp at the end of each match",
            "tiers": [
                {"tier": 1, "power": 20, "emoji": "%", "orb": 550},
                {"tier": 2, "power": 40, "emoji": "%", "orb": 690},
                {"tier": 3, "power": 60, "emoji": "%", "orb": 830}
            ]
        },
        {
            "name": "Lucky",
            "emoji": "<:lucky:1262861466420252873>",
            "description": "Increased chance of a card dropping from campaign bosses (multiplicative, not additive)",
            "tiers": [
                {"tier": 1, "power": 10, "emoji": "%", "orb": 550},
                {"tier": 2, "power": 20, "emoji": "%", "orb": 690},
                {"tier": 3, "power": 30, "emoji": "%", "orb": 830}
            ]
        },
        {
            "name": "Lobotomizer",
            "emoji": "<:Lobotomizer:1262861602974208020>",
            "description": "Remove Cards from opponents deck at the start of each battle",
            "tiers": [
                {"tier": 1, "power": 5, "emoji": "Cards", "orb": 700},
                {"tier": 2, "power": 10, "emoji": "Cards", "orb": 875},
                {"tier": 3, "power": 15, "emoji": "Cards", "orb": 1075}
            ]
        }
    ]
   
  return arena_powers

def get_events():
# Huntress:Bear~1:Bear :gcc~1: - Anna :Anna~1:
# Mad Scientist :Science~1: Science :gcc~1: - Albert :Albert~1:
# Time Traveler :Time~1: Time :gcc~1: - Mr. Pimm :Pimm~1:
# Crazed AI :Energy~1: Energy :gcc~1: - Lucy :Lucy~1:
# Cyclone :Wind~1: Wind :gcc~1: - Leopold :Leopold~1:
# Super Villain :Villain~1: Villain :gcc~1: - Vera :Vera~1:
# Copper Chef :Food~1: Food :gcc~1: - Francois :Francois~1:
# Science Fair :Life~1: Life :gcc~1: - Miles :Miles~1:
# Invasion :Space~2: Space :gcc~1: - Xanthar :Xanthar~2:
# Monster Bash :Monster~1: Monster :gcc~1: - Ella :Ella~1:

    events = [
        {
            "eventname": "Huntress",
            "eventemoji": "<:Bear:1270751618354249790>",
            "eventgcc": "Bear",
            "bossname": "Anna",
            "bossemoji": "<:Anna:1270751642576490507>"
        },
        {
            "eventname": "Mad Scientist",
            "eventemoji": "<:Science:1270751724839112778>",
            "eventgcc": "Science",
            "bossname": "Albert",
            "bossemoji": "<:Albert:1270751744573444266>"
        },
        {
            "eventname": "Time Traveler",
            "eventemoji": "<:Time:1270751765041778841>",
            "eventgcc": "Time",
            "bossname": "Mr. Pimm",
            "bossemoji": "<:Pimm:1270751780753641606>"
        },
        {
            "eventname": "Crazed AI",
            "eventemoji": "<:Energy:1270751806120657011>",
            "eventgcc": "Energy",
            "bossname": "Lucy",
            "bossemoji": "<:Lucy:1270751824688975952>"
        },
        {
            "eventname": "Cyclone",
            "eventemoji": "<:Wind:1270751849028259872>",
            "eventgcc": "Wind",
            "bossname": "Leopold",
            "bossemoji": "<:Leopold:1270752103496945665>"
        },
        {
            "eventname": "Super Villain",
            "eventemoji": "<:Villain:1270752131183546449>",
            "eventgcc": "Villain",
            "bossname": "Vera",
            "bossemoji": "<:Vera:1270752156961738822>"
        },
        {
            "eventname": "Copper Chef",
            "eventemoji": "<:Food:1270752174531678251>",
            "eventgcc": "Food",
            "bossname": "Francois",
            "bossemoji": "<:Francois:1270752193829408800>"
        },
        {
            "eventname": "Science Fair",
            "eventemoji": "<:Life:1270752212624343091>",
            "eventgcc": "Life",
            "bossname": "Miles",
            "bossemoji": "<:Miles:1270752228025696286>"
        },
        {
            "eventname": "Invasion",
            "eventemoji": "<:Space:1270752281058611220>",
            "eventgcc": "Space",
            "bossname": "Xanthar",
            "bossemoji": "<:Xanthar:1270752296451440784>"
        },
        {
            "eventname": "Monster Bash",
            "eventemoji": "<:Monster:1270752308724240424>",
            "eventgcc": "Monster",
            "bossname": "Ella",
            "bossemoji": "<:Ella:1270752334439387200>"
        }
    ]
    return events

def get_goblins():
    goblins = {
        "gobgold": {
            "name": "Gold goblin",
            "emoji": "<:gobgold:1258839564936675348>",
            "spawn_daysC": 1,
            "spawnC": 10,
            "spawn_days": 12,
            "health": 60,
            "rewards": ["500 <:coin:1258877467842576415>", "50 <:gem:1258877082734297108> ", "1 <:gff:1258876866249625620> upgrade boost/1 random 2-orb <:gff:1258876866249625620>"]
        },
        "gobdia": {
            "name": "Diamond goblin",
            "emoji": "<:gobdiamond:1258839525401165887>",
            "spawn_daysC": 1,
            "spawnC": 4,
            "spawn_days": 28,
            "health": 72,
            "rewards": ["1000 <:coin:1258877467842576415>", "100 <:gem:1258877082734297108> ", "5 fragments <:fragment:1196793443612098560>", "1 <:dff:1258876920574116000> upgrade boost/1 random portal event <:dff:1258876920574116000>"]
        },
        "gobking": {
            "name": "Goblin king",
            "emoji": "<:gobking:1258839599938142269>",
            "spawn_daysC": 25, 
            "spawnC": 1, 
            "spawn_days": 54,
            "health": 84,
            "rewards": ["2000 <:coin:1258877467842576415>", "500 <:gem:1258877082734297108> ", "10 fragments <:fragment:1196793443612098560>", "1 non-event Premium <:gcc:1258877882571427880>/1 <:occ:1258878153913274449>"]
        }
    }
    return goblins

def construct_urls(cardname: str, is_onyx: bool = False) -> str:
    # we return a list of 3 urls, one with the cardname, one with the cardname + onyx and one with the cardname + card
    cardname = cardname.replace(" ", "_")
    if is_onyx:
        cardname += "_(Onyx)"

    urls = [
        f"https://lil-alchemist.fandom.com/wiki/{cardname.title().replace(' ', '_').replace('_And_', '_and_')}",
        f"https://lil-alchemist.fandom.com/wiki/{cardname.title().replace(' ', '_').replace('_And_', '_and_')}_(Card)",
        f"https://lil-alchemist.fandom.com/wiki/{cardname.title().replace(' ', '_').replace('_And_', '_and_').replace('_The_', '_the_').replace('_Is_', '_is_')}",
        f"https://lil-alchemist.fandom.com/wiki/{cardname.replace(' ', '_').replace('_And_', '_and_').replace('_The_', '_the_').replace('_Is_', '_is_')}",
        f"https://lil-alchemist.fandom.com/wiki/{cardname.replace(' ', '_')}",
        f"https://lil-alchemist.fandom.com/wiki/{cardname.replace(' ', '_')}_(Card)",
        ]
    
    return urls

def construct_image_urls(cardname: str, is_onyx: bool = False) -> str:
    cardname = cardname.replace(" ", "_")
    if is_onyx:
        cardname += "_(Onyx)"
    urls = [
        f"https://lil-alchemist.fandom.com/wiki/File:{cardname.title().replace(' ', '_').replace('_And_', '_and_')}.png",
        f"https://lil-alchemist.fandom.com/wiki/File:{cardname.title().replace(' ', '_').replace('_And_', '_and_').replace('_The_', '_the_').replace('_Is_', '_is_')}.png",
        f"https://lil-alchemist.fandom.com/wiki/File:{cardname.replace(' ', '_').replace('_And_', '_and_').replace('_The_', '_the_').replace('_Is_', '_is_')}.png",
        f"https://lil-alchemist.fandom.com/wiki/File:{cardname.replace(' ', '_')}.png",
        f"https://lil-alchemist.fandom.com/wiki/File:{cardname.title().replace(' ', '_').replace('_And_', '_and_')}_(Card).png",
        f"https://lil-alchemist.fandom.com/wiki/File:{cardname.replace(' ', '_')}_(Card).png",
        ]
    
    return urls


def get_correct_url(urls, cardname):
    for url in urls:
        try:
            resp = requests.get(url)
            soup = BeautifulSoup(resp.content, "html.parser")
            info = parseinfo(soup, cardname)
            return {"info": info, "url": url}
        except Exception as e:
            if url == urls[-1]:
                return None # tried all, but no url found... .
            
def get_just_image(urls, cardname):
    for url in urls:
        try:
            resp = requests.get(url, allow_redirects=False)
            # get response url
            respurl = resp.url
            soup = BeautifulSoup(resp.content, "html.parser")
            img = get_image_img_url(soup)
            return img
        except Exception as e:
            if url == urls[-1]:
                return None # tried all, but no url found... .
            

def get_medal_emoji(rank):
    if rank == 1:
        return "🥇"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    elif rank == 4:
        return "🔥"
    else:
        return "👾"
    


async def handle_error(client, admindb, error, errorwhere, interaction):
    await interaction.followup.send(errorwhere)
    get_logging_guilds_and_channels = get_logging_guilds_and_channels_from_db(admindb)

    for guild in get_logging_guilds_and_channels:
        guildid = guild[0]
        channelid = guild[1]
        guild = client.get_guild(int(guildid))
        channel = guild.get_channel(int(channelid))
        #  create embed
        embed = discord.Embed(
            title="Error",
            description=f"Error: {errorwhere}",
            color=discord.Color.red()
        )
        errormessage = traceback.format_exception(type(error), error, error.__traceback__) # this is a list
        errormessage = "\n".join(errormessage)
        embed.add_field(name="Error", value=f"{errormessage}")
        embed.set_footer(text="ChinBot & LAR Wiki")
        embed.timestamp = interaction.created_at
        embed.set_thumbnail(url="https://i.ibb.co/5KDyYkM/aw.jpg")
        await channel.send(embed=embed)

def set_logging_channel(guildid, channelid, admindbfile):
    conn = sqlite3.connect(admindbfile)
    cursor = conn.cursor()
    
    # Check if the guildid and channelid both exists in the database
    cursor.execute("SELECT * FROM loggingchannels WHERE guildid = ? AND channelid = ?", (guildid, channelid))
    data = cursor.fetchone()
    
    if data is None:
        # Insert new record if guildid does not exist
        cursor.execute("INSERT INTO loggingchannels (guildid, channelid) VALUES (?, ?)", (guildid, channelid))
    else:
        # Delete the existing channelid if it exists
        cursor.execute("DELETE FROM loggingchannels WHERE channelid = ?", (channelid,))
    
    conn.commit()
    conn.close()

    if data is None:
        return True
    return False

def get_logging_guilds_and_channels_from_db(admindbfile):
    conn = sqlite3.connect(admindbfile)
    cursor = conn.cursor()
    cursor.execute("SELECT guildid, channelid FROM loggingchannels")
    data = cursor.fetchall()
    conn.close()
    return data

def get_member_count(client):
    membercount = 0
    for guild in client.guilds:
        membercount += guild.member_count
    return membercount
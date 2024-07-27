from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import sys
import os
from sqlalchemy.sql.expression import or_
import discord
import json

# Add the current directory to the Python module search path
sys.path.append(os.path.dirname(__file__))

from essentials.data.db_classes import (
    CardPack,
    Card,
    Combination,
    Recipe,
    Base,
    CardLevelStats,
)


# Create a SQLite database engine
engine = create_engine("sqlite:///card_database.db")

# Create an inspector
inspector = inspect(engine)

# Check if the "cards" table exists
if not inspector.has_table("cards"):
    Base.metadata.create_all(engine)

if not inspector.has_table("card_packs"):
    Base.metadata.create_all(engine)


# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()


def get_card(name, is_onyx=False):
    name = name.lower().replace("_", " ").replace(" (Onyx)", "")
    if is_onyx:
        card = (
            session.query(Card)
            .filter(Card.rarity == "Onyx")
            .filter(Card.full_name.ilike(name + " (Onyx)"))
        )

    else:
        card = (
            session.query(Card)
            .filter(Card.rarity != "Onyx")
            .filter(
                or_(Card.full_name.ilike(name + " (Card)"), Card.full_name.ilike(name))
            )
        )
    card = card.first()

    if card is None:
        return "Card not found"

    if card.fusion != "Orb":
        card.combos = (
            session.query(Combination).filter(Combination.result.ilike(name)).all()
        )
    else:
        card.combos = (
            session.query(Combination)
            .filter(
                or_(
                    Combination.card1.ilike(name),
                    Combination.card2.ilike(name),
                )
            )
            .all()
        )

    return card


def get_fusion_url(fusion):
    if fusion == "Orb":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/9/96/Orb.png/"
    elif fusion == "Pierce":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/9/9b/Pierce.png"
    elif fusion == "Crushing Blow":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/1/10/Crushing_Blow.png"
    elif fusion == "Block":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/4/48/Block.png"
    elif fusion == "Protection":
        return (
            "https://static.wikia.nocookie.net/lil-alchemist/images/6/6c/Protection.png"
        )
    elif fusion == "Reflect":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/d/d0/Reflect.png"
    elif fusion == "Counter Attack":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/c/c7/Counter_Attack.png"
    elif fusion == "Siphon":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/3/3a/Siphon.png"
    elif fusion == "Absorb":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/8/8a/Absorb.png"
    elif fusion == "Amplify":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/6/6d/Amplify.png"
    elif fusion == "Critical Strike":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/6/60/CriticalStrike.png"
    elif fusion == "Weaken":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/0/00/Weaken.png"
    elif fusion == "Curse":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/8/85/Curse.png"
    elif fusion == "Pillage":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/1/1e/Pillage.png"
    elif fusion == "Plunder":
        return "https://static.wikia.nocookie.net/lil-alchemist/images/4/46/Plunder.png"
    else:
        return "https://static.wikia.nocookie.net/lil-alchemist/images/9/96/Orb.png"


def get_embedcolor(rarity):
    switcher = {
        "Bronze": discord.Color.from_rgb(205, 127, 50),  # Brown
        "Silver": discord.Color.from_rgb(192, 192, 192),  # Silver
        "Gold": discord.Color.from_rgb(255, 215, 0),  # Gold
        "Diamond": discord.Color.from_rgb(138, 43, 226),  # Blue/Purple
        "Onyx": discord.Color.from_rgb(0, 0, 0),  # Black
    }
    return switcher.get(rarity, discord.Color.default())


def get_image(soup):
    figure_element = soup.find("figure", class_="pi-item pi-image")
    if figure_element:
        a_tag = figure_element.find("a")
        if a_tag and "href" in a_tag.attrs:
            image_url = a_tag["href"]
    else:
        image_url = None
    return image_url

def get_image_img_url(soup):
    script_element = soup.find("script", type="application/ld+json")

    if script_element:
        # Get the text content of the script element, make sure Linux can read the line endings
        script_text = script_element
        print("Script text:")
        print(script_text)
        json_data = json.loads(script_text)
        print("Json data:")
        print(json_data)
       
        img_url = json_data["mainEntity"]["image"]
    else:
        img_url = None
    return img_url


def get_rarity_and_form_etc(soup):
    # The table for the rarity and form information
    # print whole soup but formatted
    tables_rarity_form = soup.find_all("table", class_="pi-horizontal-group")
    # Description
    descr = (
        tables_rarity_form[0]
        .find("td", attrs={"data-source": "imagecaption"})
        .get_text(strip=True)
    )

    # Base Attack
    base_attack = (
        tables_rarity_form[1]
        .find("td", attrs={"data-source": "attack"})
        .get_text(strip=True)
    )
    # Base Defense
    base_defense = (
        tables_rarity_form[1]
        .find("td", attrs={"data-source": "defense"})
        .get_text(strip=True)
    )
    # Base Power
    base_power = (
        tables_rarity_form[1].find("td", attrs={"data-source": "rarity"}).text.strip()
    )

    # Rarity
    rarity = (
        tables_rarity_form[2].find("td", attrs={"data-source": "rarity"}).text.strip()
    )
    # Form
    form = tables_rarity_form[2].find("td", attrs={"data-source": "form"}).text.strip()

    # Fusion
    fusion = (
        soup.find(
            "div",
            class_="pi-item pi-data pi-item-spacing pi-border-color",
            attrs={"data-source": "fusion"},
        )
        .find("b")
        .text.strip()
    )

    # Where to acquire
    # Where to acquire
    div_acquire = soup.find("div", class_="mw-parser-output")
    list_acquire = div_acquire.find_all("ul")
    where_to_acquire = []
    element = ""
    # Check if there is only one div
    if len(list_acquire) == 1:
        element_list = list_acquire[0].find_all("li")
        for el in element_list:
            where_to_acquire.append(el.text.strip())
    else:
        where_to_acquire = [
            elem.text.strip() for elem in list_acquire[0].find_all("li")
        ]

    # The table with the level info
    table_level_info = soup.find("table", class_="article-table")

    # Initialize an empty dictionary to store the key-value pairs
    level_stats = {}

    # Find all rows within the table except the header row
    rows = table_level_info.find_all("tr")[1:]
    for row in rows:
        # Extract the level, attack, and defense values
        level_img = row.find("th").find("img")  # Find the img tag
        level = level_img["alt"]  # Extract the level from the alt attribute
        tds = row.find_all("td")  # Find all td tags
        attack = int(tds[0].text.strip())
        defense = int(tds[1].text.strip())
        level_stats[level] = {"Attack": attack, "Defense": defense}

    # The Card Recipes:

    table_recipes = soup.find("table", {"id": "mw-customcollapsible-recipesTable"})
    recipes = []

    # If there is no table_recipes, then there are no recipes
    if table_recipes is None:
        recipes = []
    else:
        table_body = table_recipes.find("tbody")
        rows = table_body.find_all("tr")

        # Iterate through the rows and extract the names from the first and second columns
        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 2:
                card1_name = columns[0].text.strip()
                card2_name = columns[1].text.strip()
                recipes.append((card1_name, card2_name))
    # The Card Combos:

    table_combos = soup.find("table", {"id": "mw-customcollapsible-combosTable"})
    combos = []

    # If there is no table_recipes, then there are no recipes
    if table_combos is None:
        combos = []
    else:
        table_body = table_combos.find("tbody")
        rows = table_body.find_all("tr")

        # Iterate through the rows and extract the names from the first and second columns
        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 2:
                card2_name = columns[0].text.strip()
                result = columns[1].text.strip()
                combos.append((card2_name, result))

    return (
        descr,
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
    )


def parseinfo(soup, cardname):
    imgurl = get_image(soup)
    try:
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
    except Exception as e:
        raise e

    levelstats = []

    # Create CardLevelStats instances and set the relationship
    for level, stats in level_stats.items():
        attack = stats["Attack"]
        defense = stats["Defense"]
        levelstats.append(CardLevelStats(level=level, attack=attack, defense=defense))

    # If you have combo data, create Combination instances and add them to the session
    if combos and combos != []:
        for combo in combos:
            # check if the other card exists in the database

            card2 = combo[0]
            result = combo[1]

    return (
        imgurl,
        description,
        base_attack,
        base_defense,
        base_power,
        rarity,
        form,
        fusion,
        where_to_acquire,
        recipes,
        combos,
        level_stats,
    )

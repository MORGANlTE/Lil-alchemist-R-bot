from bs4 import BeautifulSoup
import requests
import time
import json
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from essentials.data.db_classes import (
    CardPack,
    Card,
    Combination,
    Recipe,
    Base,
    CardLevelStats,
)
from essentials.data.cards import get_cards, get_packs


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


class Scraper:
    def get_image(self, soup):
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

    def get_rarity_and_form_etc(self, soup):
        # The table for the rarity and form information
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
            tables_rarity_form[1]
            .find("td", attrs={"data-source": "rarity"})
            .text.strip()
        )

        # Rarity
        rarity = (
            tables_rarity_form[2]
            .find("td", attrs={"data-source": "rarity"})
            .text.strip()
        )
        # Form
        form = (
            tables_rarity_form[2].find("td", attrs={"data-source": "form"}).text.strip()
        )

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
        list_acquire = (
            soup.find("div", class_="mw-parser-output").find("ul").find_all("li")
        )
        where_to_acquire = []
        for elemnt in list_acquire:
            where_to_acquire.append(elemnt.text.strip())

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

    def name_converter(self, name):
        # check if name ends with " (Card)"
        type_card = ""
        url_name = name.replace(" ", "_")
        real_name = name

        if name.endswith(" (Card)"):
            type_card = "Boss "
            url_name = name.replace(" ", "_")
            # remove everything after "_(" if this is present
            if "_(" in url_name:
                real_name = url_name[: url_name.index("_(")].replace("_", " ")

        if name.endswith(" (Onyx)"):
            url_name = name.replace(" ", "_")
            # remove everything after "_(" if this is present
            if "_(" in url_name:
                real_name = url_name[: url_name.index("_(")].replace("_", " ")

        return type_card, url_name, real_name

    def scrape_card_data(self, name):
        type_card, url_name, real_name = self.name_converter(name)
        # check if already in database
        card = session.query(Card).filter_by(full_name=name).first()
        if card:
            print(f"Card {name} already in database")

            return

        url = f"https://lil-alchemist.fandom.com/wiki/{url_name}"
        print("- " + url)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        imgurl = self.get_image(soup)
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
        ) = self.get_rarity_and_form_etc(soup)

        print(f"\tName: {real_name}")
        print("\tImage URL:", imgurl)
        print(f"\tDescription: {description}")
        print(f"\tBase attack: {base_attack}")
        print(f"\tBase defense: {base_defense}")
        print(f"\tBase power: {base_power}")
        print(f"\tRarity: {rarity}")
        print(f"\tForm: {type_card}{form}")
        print(f"\tFusion: {fusion}")
        print(f"\tWhere to acquire: {where_to_acquire}")
        print(f"\tStats per level: {level_stats}")
        print(f"\tRecipes:\n\t{recipes}")
        print(f"\tCombos:\n\t{combos}")

        # Create the Card instance first
        card = Card(
            name=real_name,
            full_name=name,
            image_url=imgurl,
            description=description,
            base_attack=base_attack,
            base_defense=base_defense,
            base_power=base_power,
            rarity=rarity,
            form=f"{type_card}{form}",
            fusion=fusion,
            where_to_acquire=json.dumps(where_to_acquire),
        )

        # Create CardLevelStats instances and set the relationship
        for level, stats in level_stats.items():
            attack = stats["Attack"]
            defense = stats["Defense"]

            card_level_stats = CardLevelStats(
                level=level,
                attack=attack,
                defense=defense,
            )

            # Set the relationship on both sides
            card.level_stats.append(card_level_stats)
            card_level_stats.card = card

            session.add(card_level_stats)

        # Add the Card instance to the session
        session.add(card)

        # If you have recipe data, create Recipe instances and add them to the session
        if recipes and recipes != []:
            for recipe in recipes:
                # check if the other card exists in the database
                card1 = recipe[0]
                card2 = recipe[1]
                result = card.full_name
                # check if opposite recipe exists in the database, in the recipe table
                opposite_recipe = (
                    session.query(Recipe).filter_by(card1=card2, card2=card1).first()
                )

                if not opposite_recipe:
                    recipe = Recipe(
                        card1=card1,
                        card2=card2,
                        result=result,
                    )
                    session.add(recipe)

        # If you have combo data, create Combination instances and add them to the session
        if combos and combos != []:
            for combo in combos:
                # check if the other card exists in the database

                card1 = card.full_name
                card2 = combo[0]
                result = combo[1]
                # check if opposite combo exists in the database, in the combo table
                opposite_combo = (
                    session.query(Combination)
                    .filter_by(card1=card2, card2=card1)
                    .first()
                )

                if not opposite_combo:
                    combo = Combination(
                        card1=card1,
                        card2=card2,
                        result=result,
                    )
                    session.add(combo)

        # Commit changes to the database
        session.commit()

        print(f"Added {card.name} to database")
        return "Success"

    def scrape_pack_data(self, pack_name):
        url_name = pack_name.replace(" ", "_")
        url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs/{url_name}"
        print("- " + url)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        # print(soup)

        table = soup.find_all("table", class_="pi-horizontal-group")[0]

        cost = table.find("td", {"data-source": "cost"}).get_text(strip=True)
        print(cost)

        gallery = soup.find("div", id="gallery-0")
        cardnames = []
        cards = gallery.find_all("div", class_="lightbox-caption")
        for card in cards:
            cardnames.append(card.text.strip())

        onyx_fragments_caption = soup.find(
            "div", class_="lightbox-caption", text="Onyx Fragments"
        )

        onyx = False

        if onyx_fragments_caption:
            onyx = True

        cardpack = CardPack(
            name=pack_name,
            price=cost,
            cards=json.dumps(cardnames),
            onyx_fragments=onyx,
        )

        session.add(cardpack)
        session.commit()

        return "Succes"

    def scrape_pack_data_and_add_cards(self, pack_name):
        url_name = pack_name.replace(" ", "_")
        url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs/{url_name}"
        print("- " + url)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        # print(soup)

        table = soup.find_all("table", class_="pi-horizontal-group")[0]

        cost = table.find("td", {"data-source": "cost"}).get_text(strip=True)
        print(cost)

        gallery = soup.find("div", id="gallery-0")
        cardnames = []
        cards = gallery.find_all("div", class_="lightbox-caption")
        for card in cards:
            cardnames.append(card.text.strip())

        onyx_fragments_caption = soup.find(
            "div", class_="lightbox-caption", text="Onyx Fragments"
        )

        onyx = False

        if onyx_fragments_caption:
            onyx = True

        cardpack = CardPack(
            name=pack_name,
            price=cost,
            cards=json.dumps(cardnames),
            onyx_fragments=onyx,
        )

        session.add(cardpack)
        session.commit()
        scraper = Scraper()
        # add the cards to the pack
        for card in cardnames:
            try:
                scraper.scrape_card_data(card)
            except Exception as e:
                print(f"Error on card {card}")
                print(e)

            time.sleep(2)
        return "Succes"

    def scrape_pack_data_and_overwrite_cards(self, pack_name):
        url_name = pack_name.replace(" ", "_")
        url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs/{url_name}"
        print("- " + url)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        # print(soup)

        table = soup.find_all("table", class_="pi-horizontal-group")[0]

        cost = table.find("td", {"data-source": "cost"}).get_text(strip=True)
        print(cost)

        gallery = soup.find("div", id="gallery-0")
        cardnames = []
        cards = gallery.find_all("div", class_="lightbox-caption")
        for card in cards:
            cardnames.append(card.text.strip())

        onyx_fragments_caption = soup.find(
            "div", class_="lightbox-caption", text="Onyx Fragments"
        )

        onyx = False

        if onyx_fragments_caption:
            onyx = True

        cardpack = CardPack(
            name=pack_name,
            price=cost,
            cards=json.dumps(cardnames),
            onyx_fragments=onyx,
        )

        session.add(cardpack)
        session.commit()
        scraper = Scraper()
        # add the cards to the pack
        for card in cardnames:
            try:
                scraper.scrape_card_data_overwrite(card)
            except Exception as e:
                print(f"Error on card {card}")
                print(e)

            time.sleep(2)
        return "Succes"

    def scrape_card_data_overwrite(self, name):
        type_card, url_name, real_name = self.name_converter(name)
        # check if already in database
        card = session.query(Card).filter_by(full_name=name).first()
        if card:
            # delete the card in the database and add the newer one
            print(f"Card {name} already in database, overwriting...")
            session.delete(card)
            session.commit()
            # delete all the recipes and combos that contain this card
            recipes = (
                session.query(Recipe)
                .filter_by(card1=name)
                .union(session.query(Recipe).filter_by(card2=name))
            )
            for recipe in recipes:
                session.delete(recipe)
            combos = (
                session.query(Combination)
                .filter_by(card1=name)
                .union(session.query(Combination).filter_by(card2=name))
            )
            for combo in combos:
                session.delete(combo)
            session.commit()
        else:
            print(f"Card {name} not in database, adding...")

        url = f"https://lil-alchemist.fandom.com/wiki/{url_name}"
        print("- " + url)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        imgurl = self.get_image(soup)
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
        ) = self.get_rarity_and_form_etc(soup)

        print(f"\tName: {real_name}")
        print("\tImage URL:", imgurl)
        print(f"\tDescription: {description}")
        print(f"\tBase attack: {base_attack}")
        print(f"\tBase defense: {base_defense}")
        print(f"\tBase power: {base_power}")
        print(f"\tRarity: {rarity}")
        print(f"\tForm: {type_card}{form}")
        print(f"\tFusion: {fusion}")
        print(f"\tWhere to acquire: {where_to_acquire}")
        print(f"\tStats per level: {level_stats}")
        print(f"\tRecipes:\n\t{recipes}")
        print(f"\tCombos:\n\t{combos}")

        # Create the Card instance first
        card = Card(
            name=real_name,
            full_name=name,
            image_url=imgurl,
            description=description,
            base_attack=base_attack,
            base_defense=base_defense,
            base_power=base_power,
            rarity=rarity,
            form=f"{type_card}{form}",
            fusion=fusion,
            where_to_acquire=json.dumps(where_to_acquire),
        )

        # Create CardLevelStats instances and set the relationship
        for level, stats in level_stats.items():
            attack = stats["Attack"]
            defense = stats["Defense"]

            card_level_stats = CardLevelStats(
                level=level,
                attack=attack,
                defense=defense,
            )

            # Set the relationship on both sides
            card.level_stats.append(card_level_stats)
            card_level_stats.card = card

            session.add(card_level_stats)

        # Add the Card instance to the session
        session.add(card)

        # If you have recipe data, create Recipe instances and add them to the session
        if recipes and recipes != []:
            for recipe in recipes:
                # check if the other card exists in the database
                card1 = recipe[0]
                card2 = recipe[1]
                result = card.full_name
                # check if opposite recipe exists in the database, in the recipe table
                opposite_recipe = (
                    session.query(Recipe).filter_by(card1=card2, card2=card1).first()
                )

                if not opposite_recipe:
                    recipe = Recipe(
                        card1=card1,
                        card2=card2,
                        result=result,
                    )
                    session.add(recipe)

        # If you have combo data, create Combination instances and add them to the session
        if combos and combos != []:
            for combo in combos:
                # check if the other card exists in the database

                card1 = card.full_name
                card2 = combo[0]
                result = combo[1]
                # check if opposite combo exists in the database, in the combo table
                opposite_combo = (
                    session.query(Combination)
                    .filter_by(card1=card2, card2=card1)
                    .first()
                )

                if not opposite_combo:
                    combo = Combination(
                        card1=card1,
                        card2=card2,
                        result=result,
                    )
                    session.add(combo)

        # Commit changes to the database
        session.commit()

        print(f"Overwritten {card.name} to database")
        return "Success"


scraper = Scraper()


def scrape_new_cards(cards_to_scrape):
    counter = 1
    print(cards_to_scrape)
    for name in get_cards():
        print(f"#{counter} {name}")
        try:
            response = scraper.scrape_card_data(name)
        except Exception as e:
            print(f"Error on card {name}")
            print(e)
            # print where the error occurs
            import traceback

            traceback.print_exc()
        time.sleep(2)
        counter += 1


def scrape_new_packs(packs_to_scrape):
    counter = 1
    for pack in packs_to_scrape:
        print(f"#{counter} {pack}")
        try:
            response = scraper.scrape_pack_data_and_add_cards(pack)
        except Exception as e:
            print(f"Error on card {pack}")
            print(e)
            # print where the error occurs
            import traceback

            traceback.print_exc()
        time.sleep(2)
        counter += 1


def overwrite_packs(packs_to_scrape):
    counter = 1
    for pack in packs_to_scrape:
        print(f"#{counter} {pack}")
        try:
            response = scraper.scrape_pack_data_and_overwrite_cards(pack)
        except Exception as e:
            print(f"Error on card {pack}")
            print(e)
            # print where the error occurs
            import traceback

            traceback.print_exc()
        time.sleep(2)
        counter += 1


def overwrite_cards(cards_to_overwrite, onyx_cards):
    counter = 1
    for name in cards_to_overwrite:
        print(f"#{counter} {name}")
        try:
            response = scraper.scrape_card_data_overwrite(name)
        except Exception as e:
            print(f"Error on card {name}")
            print(e)
            # print where the error occurs
            import traceback

            traceback.print_exc()
        time.sleep(2)
        counter += 1

    for name in onyx_cards:
        print(f"#{counter} {name}_(Onyx)")
        try:
            response = scraper.scrape_card_data_overwrite(name + " (Onyx)")
        except Exception as e:
            print(f"Error on card {name}")
            print(e)
            # print where the error occurs
            import traceback

            traceback.print_exc()
        time.sleep(2)
        counter += 1


# Close the session
session.close()

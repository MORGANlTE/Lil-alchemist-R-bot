from bs4 import BeautifulSoup
import requests
from data_grabber import *
import discord
import PIL
from PIL import Image, ImageDraw, ImageFont
import random
import os


async def simulate_pack_opening(name):
    if name == "Jark":
        cardnames = [
            "Chinchilla_(Onyx)",
            "Chinchilla_(Onyx)",
            "Chinchilla_(Onyx)",
            "Chinchilla_(Onyx)",
        ]
    elif name == "Melmman":
        cardnames = [
            "Hammer_(Onyx)",
            "Hammer_(Onyx)",
            "Hammer_(Onyx)",
            "Grabbers",
        ]
        random.shuffle(cardnames)
    elif name == "ILoveDog":
        cardnames = [
            "Bat_(Onyx)",
            "Dog",
            "Dog",
            "Dog",
            "Dog",
            "Bat_(Onyx)",
            "Siberian Husky",
            "Siberian Husky",
            "Siberian Husky",
            "Siberian Husky",
        ]
        random.shuffle(cardnames)
    else:
        url_name = name.replace(" ", "_")
        url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs/{url_name}"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")

        try:
            table = soup.find_all("table", class_="pi-horizontal-group")[0]
        except:
            return "Not found"
        cost = table.find("td", {"data-source": "cost"}).get_text(strip=True)

        gallery = soup.find("div", id="gallery-0")
        cardnames = []
        cards = gallery.find_all("div", class_="lightbox-caption")
        for card in cards:
            cardnames.append(card.text.strip())

        # multiply all cards that are not ending with _(Onyx) by 4, so 3 more copies of the card are added
        for i in range(len(cardnames)):
            if not cardnames[i].endswith("(Onyx)"):
                for j in range(3):
                    cardnames.append(cardnames[i])

    randomnumberForResult = random.randint(0, 100000)

    random.shuffle(cardnames)
    cardnames = cardnames[:4]

    card_pictures = []

    counter = 1
    try:
        for cardname in cardnames:
            url = f"https://lil-alchemist.fandom.com/wiki/{cardname.replace(' ', '_').replace('_The_', '_the_')}"

            resp = requests.get(url)
            soup = BeautifulSoup(resp.content, "html.parser")
            test = parseinfo(soup, cardname)

            (
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
            ) = test

            randomnumber = random.randint(0, 100000)
            with open(f"./test/images/{cardname}{randomnumber}.png", "wb") as f:
                f.write(requests.get(imgurl).content)

            image = Image.open(f"./test/images/{cardname}{randomnumber}.png")
            resized_image = image.resize((350, 465))

            mask = Image.new("L", resized_image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle(
                [(0, 0), resized_image.size], 25, fill=255, outline=0
            )

            result = Image.new("RGBA", resized_image.size)
            result.paste(resized_image, (0, 0), mask=mask)

            draw = ImageDraw.Draw(result)
            draw.rounded_rectangle(
                [(0, 0), resized_image.size], 25, outline=(0, 0, 0), width=3
            )

            if not os.path.exists("./images"):
                os.makedirs("./images")

            result.save(f"./images/{cardname}{randomnumber}.png")
            counter += 1

            card_pictures.append(f"./images/{cardname}{randomnumber}.png")

        new_im = Image.new("RGBA", (350 * 4 + 30 * 3, 465), (0, 0, 0, 0))
        x_offset = 0
        y_offset = 0
        spacing = 30
        image_width = 350

        x_offset = 0
        y_offset = 0

        for i in range(0, 4):
            new_im.paste(Image.open(card_pictures[i]), (x_offset, y_offset))
            x_offset += image_width + spacing

        new_im.save(f"./images/{name}{randomnumberForResult}.png")

        fileM = discord.File(
            f"./images/{name}{randomnumberForResult}.png",
            filename=f"{name}{randomnumberForResult}.png",
        )

        if counter > 4:
            for i in range(len(card_pictures) - 1):
                os.remove(card_pictures[i])

        return fileM
    except Exception as e:
        print(e)
        return "Error occured"


def delete_saved_images():
    # if the images folder doesnt exist, create it
    if not os.path.exists("./images"):
        os.makedirs("./images")
    for filename in os.listdir("./images"):
        os.remove(f"./images/{filename}")

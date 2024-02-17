from bs4 import BeautifulSoup
import httpx
import random

name = "Wintertide"

url_name = name.replace(" ", "_")
url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs/{url_name}"
resp = httpx.get(url)
soup = BeautifulSoup(resp.content, "html.parser")

try:
    div1 = soup.find_all("div", id="gallery-0")[0]
except:
    print("Not found")
cardnames = []

gallery = soup.find("div", id="gallery-0")
cards = gallery.find_all("a", class_="image link-internal")
for card in cards:
    cardnames.append(card.get("href").replace("/wiki/", "").strip())

gallery = soup.find("div", id="gallery-1")
cards = gallery.find_all("a", class_="image link-internal")
for card in cards:
    cardnames.append(card.get("href").replace("/wiki/", "").strip())


# multiply all cards that are not ending with _(Onyx) by 4, so 3 more copies of the card are added
for i in range(len(cardnames)):
    if not cardnames[i].endswith("(Onyx)"):
        for j in range(3):
            cardnames.append(cardnames[i])

print(cardnames)
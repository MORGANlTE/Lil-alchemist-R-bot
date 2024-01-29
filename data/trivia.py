from random import randint
import requests
from bs4 import BeautifulSoup

packs = []

def get_trivia_questions():
    questions = [
        Question(
            "What is the name of the first boss in the game?",
            ["Vlad", "Harmony", "Chloe"],
            "https://static.wikia.nocookie.net/lil-alchemist/images/d/d5/Graveyard.png",
            2,
        ),
        Question(
            "What Pokémon is Evomon based on?",
            ["Eviolite", "Eevee", "Evangel"],
            "https://static.wikia.nocookie.net/lil-alchemist/images/e/ed/Evomon.png",
            1,
        ),
        Question(
            "Give the name of the GCC from the Science Fair Event",
            ["Life", "Science", "Monster"],
            "https://static.wikia.nocookie.net/lil-alchemist/images/a/a8/Miles.png",
            0,
        ),
        Question(
            "What is the description of the Healers ability?",
            ["Heal your wounds", "Heal your allies", "Replenish your health"],
            "https://static.wikia.nocookie.net/lil-alchemist/images/d/d5/HealerProfileFrame.png",
            0,
        ),
        Question(
            "What movie does the Hopeful Robot reference?",
            ["EEV-E", "WALL-E", "WALLEY"],
            "https://static.wikia.nocookie.net/lil-alchemist/images/a/a5/Hopeful_Robot.png",
            2,
        ),
        Question(
            "In Greek mythology, Atlas was a titan condemned to:",
            ["Have his liver eaten repeatedly by an eagle", "Eternally push a rock up a mountain", "Hold up the sky for eternity"],
            "https://static.wikia.nocookie.net/lil-alchemist/images/0/04/Atlas.png",
            2,
        ),
    ]
    # return random question
    # 1/50 chance to return any of these questions
    chance = randint(0, 60)
    if chance == 0:
        return questions[randint(0, len(questions) - 1)]
    else:
        return generate_random_question()

def setup_packs():
    url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")


    table = soup.find("table", style="width:100%;text-align:center;")

    trs = table.find_all("tr")
    trs = trs[3:-4]
    # clear packs
    packs.clear()
    for i, tr in enumerate(trs):
        if i % 2 != 0:
            akes = tr.find_all("a")
            for ake in akes:
                packs.append(ake["href"].split("/")[2].replace("_Pack", "").replace("_Of_", "_of_"))


def generate_random_question():
    # get 3 random packs
    packs_clone = packs.copy()
    # random pack 1
    pack1 = packs_clone[randint(0, len(packs_clone) - 1)]
    packs_clone.remove(pack1)
    # random pack 2
    pack2 = packs_clone[randint(0, len(packs_clone) - 1)]
    packs_clone.remove(pack2)
    # random pack 3
    pack3 = packs_clone[randint(0, len(packs_clone) - 1)]
    packs_clone.remove(pack3)

    correct_answer_int = randint(0, 2)
    print(f"[Packopening]: {pack1}")

    # get 2 random cards from pack1
    # all cards from this pack:
    url = f"https://lil-alchemist.fandom.com/wiki/Special_Packs/{pack1}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    gallery = soup.find("div", id="gallery-0")
    cardnames = []
    cards = gallery.find_all("div", class_="lightbox-caption")
    for card in cards:
        cardnames.append(card.text.strip())
    
    # get 2 random cards from this list
    card1 = cardnames[randint(0, len(cardnames) - 1)]
    card2 = cardnames[randint(0, len(cardnames) - 1)]
    while card2 == card1:
        card2 = cardnames[randint(0, len(cardnames) - 1)]

    # get the image from the first card
    url = f"https://lil-alchemist.fandom.com/wiki/{card1}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    card1_image = get_image(soup)
    packs_local = []
    # add the 3 packs randomly into a list
    packs_local.append(pack1.replace("_", " "))
    packs_local.append(pack2.replace("_", " "))
    packs_local.append(pack3.replace("_", " "))
    correct_answer = pack1.replace("_", " ")

    # shuffle the list, randomize the order
    packs_local = sorted(packs_local, key=lambda x: randint(0, len(packs_local) - 1))

    # index of the correct answer, index of 
    correct_answer_index = packs_local.index(correct_answer)

    # get the image from the first card
    question = Question(
            f"What pack do the cards `{card1}` and `{card2}` belong to?",
            packs_local,
            f"{card1_image}",
            correct_answer_index,
        )
    
    return question


class Question:
    def __init__(self, question, answers, image_url_question, correct_answer_index):
        self.question = question
        self.answers = answers
        self.image_url_question = image_url_question
        self.correct_answer_index = correct_answer_index

    def __str__(self):
        return self.question

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
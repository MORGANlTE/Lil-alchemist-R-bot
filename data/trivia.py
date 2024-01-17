from random import randint


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
    ]
    # return random question
    return questions[randint(0, len(questions) - 1)]


class Question:
    def __init__(self, question, answers, image_url_question, correct_answer_index):
        self.question = question
        self.answers = answers
        self.image_url_question = image_url_question
        self.correct_answer_index = correct_answer_index

    def __str__(self):
        return self.question

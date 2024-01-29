class Question:
    def __init__(self, question, answers, image_url_question, correct_answer_index):
        self.question = question
        self.answers = answers
        self.image_url_question = image_url_question
        self.correct_answer_index = correct_answer_index

    def __str__(self):
        return self.question
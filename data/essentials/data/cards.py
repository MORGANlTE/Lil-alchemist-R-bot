from .cardnames import cards
from .packnames import packs
def get_cards():
  no_duplicates = {}

  # Use set to remove duplicates
  no_duplicates = set(cards)

  # Sort the set alphabetically and convert it back to a list
  sorted_cards = sorted(no_duplicates)  
  
  return sorted_cards


def get_packs():
  return packs
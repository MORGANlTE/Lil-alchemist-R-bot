from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    full_name = Column(String)
    image_url = Column(String)
    description = Column(String)
    base_attack = Column(Integer)
    base_defense = Column(Integer)
    base_power = Column(Integer)
    rarity = Column(String)
    form = Column(String)
    fusion = Column(String)
    where_to_acquire = Column(String)

    level_stats = relationship('CardLevelStats', back_populates='card')

class CardLevelStats(Base):
    __tablename__ = 'card_level_stats'

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.id'))
    level = Column(Integer)
    attack = Column(Integer)
    defense = Column(Integer)

    card = relationship('Card', back_populates='level_stats')

class Combination(Base):
    __tablename__ = 'combinations'

    id = Column(Integer, primary_key=True)
    card1 = Column(Integer, ForeignKey('cards.id'))
    card2 = Column(Integer, ForeignKey('cards.id'))
    result = Column(Integer, ForeignKey('cards.id'))

class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    card1 = Column(Integer, ForeignKey('cards.id'))
    card2 = Column(Integer, ForeignKey('cards.id'))
    result = Column(Integer, ForeignKey('cards.id'))

class CardPack(Base):
    __tablename__ = 'card_packs'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    cards = Column(String)
    onyx_fragments = Column(Boolean)

    def get_cards(self):
        return json.loads(self.cards)
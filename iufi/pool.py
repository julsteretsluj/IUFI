from random import Random
from collections import Counter

from .objects import Card
from .exceptions import DuplicatedCardError, DuplicatedTagError
from .deepsearch import (
    Load_Data,
    Search_Setup
)

DROP_RATES = {
    'common': .9,
    'rare': .08,
    'epic': .007,
    'legendary': .003,
    'mystic': .001,
    "celestial": .0005
}

class CardPool:
    _cards: dict[str, Card] = {}
    _tag_cards: dict[str, Card] = {}
    _available_cards: dict[str, list[Card]] = {
        category: [] for category in DROP_RATES
    }
    _rand = Random()

    #DeepSearch
    search_image: Search_Setup | None = None

    @classmethod
    def load_search_metadata(cls) -> None:
        image_list = Load_Data().from_folder(["/metadata-files"])
        cls.search_image = Search_Setup(image_list=image_list)
        cls.search_image.run_index()

    @classmethod
    def add_available_card(cls, card: Card) -> None:
        card.change_owner()
        cls._available_cards[card.tier[1]].append(card)

    @classmethod
    def remove_available_card(cls, card: Card) -> None:
        cls._available_cards[card.tier[1]].remove(card)

    @classmethod
    def add_tag(cls, card: Card, tag: str) -> None:
        if tag.lower() in cls._tag_cards:
            raise DuplicatedTagError(f"Tag {tag} already added into the pool.")
        
        card.change_tag(tag)
        cls._tag_cards[tag.lower()] = card
    
    @classmethod
    def change_tag(cls, card: Card, tag: str) -> None:
        if tag.lower() in cls._tag_cards:
            raise DuplicatedTagError(f"Tag {tag} already added into the pool.")
        
        if card.tag and card.tag.lower() in cls._tag_cards:
            card = cls._tag_cards.pop(card.tag.lower())
            card.change_tag(tag)
            cls._tag_cards[tag.lower()] = card

    @classmethod
    def remove_tag(cls, card: Card) -> None:
        try:
            card = cls._tag_cards.pop(card.tag.lower())
            card.change_tag(None)
        except KeyError as _:
            return
        
    @classmethod
    def add_card(cls, _id: str, tier: str, **kwargs) -> Card:
        card = Card(cls, _id, tier, **kwargs)
        if card.id in cls._cards:
            raise DuplicatedCardError(f"Card {card.id} in {tier} already added into the pool.")
        
        cls._cards[card.id] = card
        if not card.owner_id:
            cls.add_available_card(card)
        
        if card.tag:
            cls.add_tag(card, card.tag)

        return card
    
    @classmethod
    def get_card(cls, card_id: str) -> Card | None:
        if not card_id:
            return
        card_id = card_id.lstrip("0")
        card = cls._cards.get(card_id)
        if not card:
            card = cls._tag_cards.get(card_id.lower())
        return card
    
    @classmethod
    def roll(cls, amount: int = 3, *, included: list[str] = None, avoid: list[str] = None, luck_rates: float = None) -> list[Card]:
        results = included if included else []

        drop_rates = DROP_RATES.copy()
        if luck_rates:
            drop_rates = {k: v if k == 'common' else v * (1 + luck_rates) for k, v in DROP_RATES.items()}
            total = sum(drop_rates.values())
            drop_rates['common'] = 1 - (total - drop_rates['common'])
        
        if avoid:
            drop_rates = {k: v for k, v in drop_rates.items() if k not in avoid}

        results.extend(cls._rand.choices(list(drop_rates.keys()), weights=drop_rates.values(), k=amount - len(results)))
        cards = [
            card
            for cat, amt in Counter(results).items()
            for card in cls._rand.sample(cls._available_cards[cat], k=amt)
        ]
        cls._rand.shuffle(cards)
        return cards
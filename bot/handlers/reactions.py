"""Automatic reactions to trigger words in messages."""
import random

# Constants
REACTION_PROBABILITY = 0.15

# Trigger words mapped to reaction themes
TRIGGER_REACTIONS = {
    'спать': [
        "<i>Кайо зевнул и устроился рядом</i>",
        "<i>Заяц сладко потянулся и закрыл глаза</i>",
        "<i>Кайо свернулся клубком и захрапел</i>",
    ],
    'есть': [
        "<i>Заяц принёс что-то вкусное</i>",
        "<i>Кайо заинтересованно посмотрел на еду</i>",
        "<i>Заяц громко чавкнул неподалёку</i>",
    ],
    'устал': [
        "<i>Кайо лениво прижался к {user}</i>",
        "<i>Заяц предложил свою спинку для отдыха</i>",
        "<i>Кайо мягко обнял за плечи</i>",
    ],
    'холодно': [
        "<i>Кайо закутался в свой хвост</i>",
        "<i>Заяц прижался к {user} ради тепла</i>",
        "<i>Кайо предложил разделить плед</i>",
    ],
    'грущу': [
        "<i>Заяц слегка фыркнул и коснулся носом {user}</i>",
        "<i>Кайо тихо устроился рядом и не отходит</i>",
        "<i>Заяц принёс маленький цветочек</i>",
    ],
    'привет': [
        "<i>Кайо подпрыгнул и замахал лапками</i>",
        "<i>Заяц радостно затопал ножками</i>",
        "<i>Кайо махнул хвостом в ответ</i>",
    ],
    'люблю': [
        "<i>Кайо покраснел и спрятал мордочку в лапках</i>",
        "<i>Заяц застенчиво отвёл глаза</i>",
        "<i>Кайо тихо мурлыкнул</i>",
    ],
    'скучаю': [
        "<i>Кайо прижался к {user} и не отпускает</i>",
        "<i>Заяц достал фотографию и смотрит на неё</i>",
        "<i>Кайо грустно повесил ушки</i>",
    ],
}

def get_reaction(text, user_mention):
    """Returns a random reaction if trigger word found, else None."""
    text_lower = text.lower()
    
    # Find all matching triggers
    matched_triggers = [trigger for trigger in TRIGGER_REACTIONS if trigger in text_lower]
    
    if not matched_triggers:
        return None
    
    # Pick a random trigger and a random reaction for it
    trigger = random.choice(matched_triggers)
    reactions = TRIGGER_REACTIONS[trigger]
    reaction = random.choice(reactions)
    
    # Format with user mention if placeholder exists
    if '{user}' in reaction:
        return reaction.format(user=user_mention)
    return reaction

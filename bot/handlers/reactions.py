import random

def get_reaction(text, user_mention):
    """
    Returns a random reaction string if any trigger word found in the text.
    Trigger words: спать, есть, устал, холодно, грущу
    Probability: 10-20% (we'll use 15% as a middle value)
    """
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # List of trigger words
    triggers = ['спать', 'есть', 'устал', 'холодно', 'грущу']
    
    # Check if any trigger word is present
    if any(trigger in text_lower for trigger in triggers):
        # 15% chance to return a reaction
        if random.random() < 0.15:
            # List of possible reactions in Russian with HTML formatting
            reactions = [
                "<i>Кайо зевнул и устроился рядом</i>",   # no username
                "<i>Заяц принес что-то вкусное {}</i>",   # with username placeholder
                "<i>Кайо лениво прижался к {}</i>",       # with username placeholder
                "<i>Кайо подпрыгнул и закутался в свой хвост</i>", # no username
                "<i>Заяц слегка фыркнул и коснулся носом {}</i>"   # with username placeholder
            ]
            reaction = random.choice(reactions)
            # If the reaction contains a placeholder, format it with the user_mention
            if '{}' in reaction:
                return reaction.format(user_mention)
            return reaction
    return None
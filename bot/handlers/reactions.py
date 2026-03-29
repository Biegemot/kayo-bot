import random

def get_reaction(text):
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
            # List of possible reactions
            reactions = [
                "😴",
                "🍽️",
                "😩",
                "🥶",
                "😔",
                "Зzzз",
                "Пора есть?",
                "Обниму?",
                "Холодно? Держись за меня!",
                "Не грусти, я рядом!"
            ]
            return random.choice(reactions)
    return None
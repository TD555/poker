from deuces import Card, Evaluator
from typing import List

evaluator = Evaluator()

def read_hands(file_path):
    
    all_hands = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                board, hand = line.strip().split('_')
                all_hands.append((board, hand))
    
    return all_hands


def split_card_into_hands(s: str) -> List[str]:
    return [Card.new(s[i:i+2]) for i in range(0, len(s), 2)]

def calculate_proba(river_cards, our_hand):
    results = f'River: {river_cards}, Our_hand: {our_hand}, Score : {evaluator.evaluate(cards=split_card_into_hands(our_hand), board=split_card_into_hands(river_cards))}'
    return results
    
if __name__=='__main__':
        
    all_hands = read_hands('input.txt')
    
    results = [calculate_proba(river_cards, our_hand) for river_cards, our_hand in all_hands]

    with open("output.txt", 'w') as file:
        file.write('\n'.join(results))
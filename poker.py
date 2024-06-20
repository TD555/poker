import os
import random
from treys import Card, Evaluator, Deck

# Function to read hands from hands.txt
def read_hands(file_path):
    hands = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                hand, cards = line.strip().split(':')
                hands[hand.strip()] = [c.strip() for c in cards.split(',') if c.strip()]
    return hands

# Function to read boards from boards.txt
def read_boards(file_path):
    boards = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                boards.append(line.strip())
    return boards

# Function to expand hands with weights
def expand_hands(file_content, hands):
    ranges = [{'hands': hands[item.split(':')[0]], 'weight': float(item.split(':')[1])} for item in file_content.strip().split(',') if float(item.split(':')[1])]
    return ranges

# Function to read ranges from individual range files
def read_ranges(folder_path, hands):
    ranges = {}
    range_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    for file_name in range_files:
        range_name = os.path.splitext(file_name)[0]
        with open(os.path.join(folder_path, file_name), 'r') as file:
            ranges[range_name] = expand_hands(file.read(), hands)
    return ranges

# Function to parse queries from queries.txt
def parse_queries(file_path):
    queries = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                queries.append(line.strip().split(';'))
    return queries

# Function to split a string of cards into pairs
def split_card_into_hands(s):
    return [s[i:i+2] for i in range(0, len(s), 2)]

import random
import numpy as np

# Function to generate villain hands based on weights
def generate_villain_hands(villain_ranges, known_cards):
    villain_hands = []
    for villain in villain_ranges:
        hands = []
        weights = []
        for hand_data in villain:
            hands.extend(hand_data['hands'])
            weights.extend([hand_data['weight']] * len(hand_data['hands']))
        
        # Normalize weights to probabilities
        total_weight = sum(weights)
        probabilities = [weight / total_weight for weight in weights]

        # Perform weighted random choice
        chosen_hand = random.choices(hands, weights=probabilities, k=1)[0]

        # Convert chosen hand to Card objects
        villain_hand_cards = [Card.new(card) for card in split_card_into_hands(chosen_hand)]

        # print(villain_hand_cards)
        # Ensure chosen hand does not overlap with known cards
        while any(card in known_cards for card in villain_hand_cards):
            chosen_hand = random.choices(hands, weights=probabilities, k=1)[0]
            villain_hand_cards = [Card.new(card) for card in split_card_into_hands(chosen_hand)]

        villain_hands.append(villain_hand_cards)

    return villain_hands



# Function to simulate equity using Monte Carlo simulations
def simulate_equity(our_combos, villain_ranges, board, iterations):
    evaluator = Evaluator()
    ties = 0
    board_cards = split_card_into_hands(board)
    win_probabilities = []

    for our_combo in our_combos:
        our_wins = 0
        valid_hands = our_combo['hands']
        total_weight = sum(combo['weight'] for combo in our_combos)
        
        for hands in valid_hands:
            for _ in range(iterations):
                if any(card in board_cards for card in split_card_into_hands(hands)):
                    continue
                
                deck = Deck()
                known_cards = [Card.new(card) for card in board_cards + split_card_into_hands(hands)]
    
                deck.cards = [card for card in deck.cards if card not in known_cards]
                remaining_board = deck.draw(5 - len(board_cards))
                
                complete_board = [Card.new(card) for card in board_cards] + remaining_board
                our_hand = [Card.new(card) for card in split_card_into_hands(hands)]

                villain_hands = generate_villain_hands(villain_ranges, complete_board + our_hand)
                our_score = evaluator.evaluate(complete_board, our_hand)
                opponent_scores = [evaluator.evaluate(complete_board, opp_hand) for opp_hand in villain_hands]

                if our_score < min(opponent_scores):
                    our_wins += 1
                elif our_score == min(opponent_scores):
                    if opponent_scores.count(min(opponent_scores)) == 1:
                        our_wins += 1
                    else:
                        ties += 1

        win_probabilities.append((our_wins / (iterations * len(valid_hands))) * (our_combo['weight'] / total_weight))

    win_probability = sum(win_probabilities)
    tie_probability = ties / iterations

    return win_probability * 100

# Main function to run the script
def main():
    NUM_SIMULATIONS = int(input("Enter the number of simulations: "))
    hands_file = 'hands.txt'
    boards_file = 'boards.txt'
    queries_file = 'queries.txt'
    ranges_folder = 'ranges'
    
    hands = read_hands(hands_file)
    boards = read_boards(boards_file)
    queries = parse_queries(queries_file)
    ranges = read_ranges(ranges_folder, hands)
    
    results = []
    for query in queries:
        title, our_range_name, *villain_range_names = query
        our_range = ranges[our_range_name]
        villain_ranges = [ranges[villain_name] for villain_name in villain_range_names[:-1]]
        
        for board in boards:
            equity = simulate_equity(our_range, villain_ranges, board, NUM_SIMULATIONS)
            result_line = f"{title}; {our_range_name}; {'; '.join(villain_range_names)}; {board}; {equity:.2f}"
            results.append(result_line)
    
    output_file = 'output.txt'
    with open(output_file, 'w') as file:
        for result in results:
            file.write(result + '\n')
    
    print(f"Simulation completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()

import os
import random
from typing import List, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
from treys import Card, Evaluator, Deck
import time

# Function to read hands from hands.txt
def read_hands(file_path: str) -> Dict[str, List[str]]:
    hands = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                hand, cards = line.strip().split(':')
                hands[hand.strip()] = [c.strip() for c in cards.split(',') if c.strip()]
    return hands

# Function to read boards from boards.txt
def read_boards(file_path: str) -> List[str]:
    boards = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                boards.append(line.strip())
    return boards

# Function to expand hands with weights
def expand_hands(file_content: str, hands: Dict[str, List[str]]) -> List[Dict[str, float]]:
    ranges = [{'hands': hands[item.split(':')[0]], 'weight': float(item.split(':')[1])} for item in file_content.strip().split(',') if float(item.split(':')[1])]
    return ranges

# Function to read ranges from individual range files
def read_ranges(folder_path: str, hands: Dict[str, List[str]]) -> Dict[str, List[Dict[str, float]]]:
    ranges = {}
    range_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    for file_name in range_files:
        range_name = os.path.splitext(file_name)[0]
        with open(os.path.join(folder_path, file_name), 'r') as file:
            ranges[range_name] = expand_hands(file.read(), hands)
    return ranges

# Function to parse queries from queries.txt
def parse_queries(file_path: str) -> List[List[str]]:
    queries = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                queries.append(line.strip().split(';'))
    return queries

# Function to split a string of cards into pairs
def split_card_into_hands(s: str) -> List[str]:
    return [s[i:i+2] for i in range(0, len(s), 2)]

# Function to generate villain hands based on weights
def generate_villain_hands(villain_ranges: List[Dict[str, List[Dict[str, float]]]], known_cards: List[int]) -> List[List[int]]:
    villain_hands = []
    for villain in villain_ranges:
        hands = []
        weights = []
        for hand_data in villain:
            hands.extend(hand_data['hands'])
            weights.extend([hand_data['weight']] * len(hand_data['hands']))
    total_weight = sum(weights)
    probabilities = [weight / total_weight for weight in weights]

    while True:
      chosen_hand = random.choices(hands, weights=probabilities, k=1)[0]
      villain_hand_cards = [Card.new(card) for card in split_card_into_hands(chosen_hand)]
      if not any(card in known_cards for card in villain_hand_cards):
        villain_hands.append(villain_hand_cards)
        break  # Exit loop once a valid hand is found

    return villain_hands


# Function to simulate equity using Monte Carlo simulations
def simulate_equity(our_combos: List[Dict[str, float]], villain_ranges: List[Dict[str, List[Dict[str, float]]]], board: str, iterations: int) -> float:
    evaluator = Evaluator()
    board_cards = [Card.new(card) for card in split_card_into_hands(board)]
    win_probabilities = []

    for our_combo in our_combos:
        our_wins = 0
        valid_hands = our_combo['hands']
        total_weight = sum(combo['weight'] for combo in our_combos)

        for hands in valid_hands:
            hand_cards = [Card.new(card) for card in split_card_into_hands(hands)]
            if any(card in board_cards for card in hand_cards):
                continue

            for _ in range(iterations):
                deck = Deck()
                known_cards = board_cards + hand_cards
                deck.cards = [card for card in deck.cards if card not in known_cards]
                remaining_board = deck.draw(5 - len(board_cards))
                complete_board = board_cards + remaining_board

                villain_hands = generate_villain_hands(villain_ranges, complete_board + hand_cards)
                our_score = evaluator.evaluate(complete_board, hand_cards)
                opponent_scores = [evaluator.evaluate(complete_board, opp_hand) for opp_hand in villain_hands]

                if our_score < min(opponent_scores):
                    our_wins += 1
                elif our_score == min(opponent_scores):
                    if opponent_scores.count(min(opponent_scores)) == 1:
                        our_wins += 1

        win_probabilities.append((our_wins / (iterations * len(valid_hands))) * (our_combo['weight'] / total_weight))

    win_probability = sum(win_probabilities)

    return win_probability * 100

# Function to process a single query
def process_query(query: List[str], hands: Dict[str, List[str]], boards: List[str], ranges: Dict[str, List[Dict[str, float]]], num_simulations: int) -> List[str]:
    results = []
    title, our_range_name, *villain_range_names = query[:-1]
    our_range = ranges[our_range_name]
    villain_ranges = [ranges[villain_name] for villain_name in villain_range_names]

    for board in boards:
        equity = simulate_equity(our_range, villain_ranges, board, num_simulations)
        result_line = f"{title}; {our_range_name}; {'; '.join(villain_range_names)}; {board}; {equity:.2f}"
        results.append(result_line)

    return results

# Main function to run the script
def main():
    NUM_SIMULATIONS = int(input("Enter the number of simulations: "))
    start = time.time()
    hands_file = 'hands.txt'
    boards_file = 'boards.txt'
    queries_file = 'queries.txt'
    ranges_folder = 'ranges'

    hands = read_hands(hands_file)
    boards = read_boards(boards_file)
    queries = parse_queries(queries_file)
    ranges = read_ranges(ranges_folder, hands)

    results = []

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_query, query, hands, boards, ranges, NUM_SIMULATIONS) for query in queries]
        for future in as_completed(futures):
            results.extend(future.result())

    output_file = 'output.txt'
    with open(output_file, 'w') as file:
        for result in results:
            file.write(result + '\n')

    end = time.time()
    
    print(f"Simulation completed. Results saved to {output_file} in {int(end-start)} seconds")

if __name__ == "__main__":
    main()

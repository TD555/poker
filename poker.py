import os
import random
from typing import List, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
from treys import Card, Evaluator, Deck
import time
from itertools import compress

NUM_SIMULATIONS = 10000

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
    ranges = [(hand, float(item.split(':')[1])) for item in file_content.strip().split(',') for hand in hands[item.split(':')[0]] if float(item.split(':')[1])]
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
def generate_villain_hands(villain_ranges, known_cards: List[int]) -> List[List[int]]:
    villain_hands = []
    for villain in villain_ranges:
        hands = []
        weights = []
        
        for hand_data in villain:
            hands.append(hand_data[0])
            weights.append(hand_data[1])

        # Filter out hands that contain known cards
        valid_mask = [not any(Card.new(card) in known_cards for card in split_card_into_hands(hand)) for hand in hands]
        valid_hands = list(compress(hands, valid_mask))
        valid_weights = list(compress(weights, valid_mask))

        if not valid_hands:
            raise ValueError("No valid hands available after filtering out known cards")

        # Normalize the weights of the valid hands
        total_valid_weight = sum(valid_weights)
        valid_probabilities = [weight / total_valid_weight for weight in valid_weights]

        # Select a hand based on the normalized probabilities
        chosen_hand = random.choices(valid_hands, weights=valid_probabilities, k=1)[0]

        villain_hand_cards = [Card.new(card) for card in split_card_into_hands(chosen_hand)]
        villain_hands.append(villain_hand_cards)

    return villain_hands

# Function to simulate equity using Monte Carlo simulations
def simulate_equity(our_hand: str, villain_ranges: List[Dict[str, List[Dict[str, float]]]], board: str, iterations: int) -> Dict[str, float]:
    hand_card = [Card.new(card) for card in split_card_into_hands(our_hand)]
    our_wins = 0
    ties = 0
    villains_wins = [0] * len(villain_ranges)
    evaluator = Evaluator()
    
    for _ in range(iterations):
        board_cards = [Card.new(card) for card in split_card_into_hands(board)]

        deck = Deck()
        known_cards = board_cards + hand_card

        deck.cards = [card for card in deck.cards if card not in known_cards]
        remaining_board = deck.draw(5 - len(board_cards))
        complete_board = board_cards + remaining_board

        villain_hands = generate_villain_hands(villain_ranges, complete_board + hand_card)
        our_score = evaluator.evaluate(complete_board, hand_card)
        opponent_scores = [evaluator.evaluate(complete_board, opp_hand) for opp_hand in villain_hands]

        min_opponent_score = min(opponent_scores)

        if our_score < min_opponent_score:
            our_wins += 1
        elif our_score == min_opponent_score:
            ties += 1
        else:
            for idx, opponent_score in enumerate(opponent_scores):
                if opponent_score == min_opponent_score:
                    villains_wins[idx] += 1

    total_simulations = our_wins + ties + sum(villains_wins)
    win_probability = (our_wins / total_simulations) * 100
    tie_probability = (ties / total_simulations) * 100
    villain_probabilities = [(villain_wins / total_simulations) * 100 for villain_wins in villains_wins]

    return {
        "win_probability": win_probability,
        "tie_probability": tie_probability,
        "villain_probabilities": villain_probabilities
    }

# Function to process a single query
def process_query(query: List[str], boards: List[str], ranges: Dict[str, List[Dict[str, float]]], num_simulations: int) -> List[str]:
    results = []
    title, our_range_name, *villain_range_names = query[:-1]
    our_range = ranges[our_range_name]
    our_hands = [item[0] for item in our_range]
    villain_ranges = [ranges[villain_name] for villain_name in villain_range_names]

    for board in boards[:1]:
        for our_hand in our_hands:
            if any(card in split_card_into_hands(our_hand) for card in split_card_into_hands(board)):
                continue
            equity = simulate_equity(our_hand, villain_ranges, board, num_simulations)
            villain_probs_str = '; '.join(f"{villain_name}; {prob:.2f}" for villain_name, prob in zip(villain_range_names, equity['villain_probabilities']))
            result_line = (
                f"{title}; {our_range_name}; {board}; {our_hand}; {equity['win_probability']:.2f}; "
                f"Tie: {equity['tie_probability']:.2f}; {villain_probs_str}"
            )
            results.append(result_line)

    return results

# Main function to run the script
def main():
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

    print("Simulation started...")
    
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_query, query, boards, ranges, NUM_SIMULATIONS) for query in queries[2:3]]
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

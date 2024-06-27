import os
import random
from typing import List, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
from deuces import Card, Evaluator, Deck
import time

NUM_SIMULATIONS = 10000
games_played = 0
start = time.time()

# Function to read hands from hands.txt
def read_hands(file_path: str) -> Dict[str, List[str]]:
    hands = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                hand, cards = line.strip().split(':')
                hands[hand.strip()] = [c.strip()
                                       for c in cards.split(',') if c.strip()]
    return hands

# Function to read boards from boards.txt
def read_boards(file_path: str) -> List[str]:
    boards = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                boards.append([Card.new(card)
                              for card in split_card_into_hands(line.strip())])
    return boards

# Function to expand hands with weights
def expand_hands(file_content: str, hands: Dict[str, List[str]]) -> List[Dict[str, float]]:
    ranges = [([Card.new(card) for card in split_card_into_hands(hand)], float(item.split(':')[1])) for item in file_content.strip().split(
        ',') for hand in hands[item.split(':')[0]] if float(item.split(':')[1])]
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
def generate_villain_hand(villain_range, known_cards):

    known_cards_set = set(known_cards)

    filtered_hands_weights = [
        (hand_cards, weight) for hand_cards, weight in villain_range
        if all(card not in known_cards_set for card in hand_cards)
    ]

    if not filtered_hands_weights:
        raise ValueError(
            "No valid hands available after filtering out known cards")

    hands, weights = zip(*filtered_hands_weights)

    chosen_hand = random.choices(hands, weights=weights, k=1)[0]

    return chosen_hand


def join_cards(hand):
    return ''.join([Card.int_to_str(card) for card in hand])

# hands_cache = {}

def simulate_equity(our_hand: str, villain_ranges: List[Dict[str, List[Dict[str, float]]]], board: str, iterations: int, title) -> Dict[str, float]:
    global games_played

    known_cards = board + our_hand
    our_wins = 0
    ties = 0
    villains_wins = [0] * len(villain_ranges)
    evaluator = Evaluator()
    if len(board) != 4:
        for _ in range(iterations):

            opponent_scores = []
            deck = Deck()
            # deck.shuffle()
            for card in known_cards:
                deck.cards.remove(card)

            villain_hands = []
            for villain_range in villain_ranges:
                try:
                    villain_hand = generate_villain_hand(
                        villain_range, known_cards + [hand for villain_hand in villain_hands for hand in villain_hand])
                except:
                    continue

                for card in villain_hand:
                    deck.cards.remove(card)

                villain_hands.append(villain_hand)

            remaining_board = deck.draw(5 - len(board))
            complete_board = board + remaining_board

            for villain_hand in villain_hands:
                # joined_hand = str(villain_hand + complete_board)
                # if joined_hand not in hands_cache:
                evaluation = evaluator.evaluate(
                    complete_board, villain_hand)
                opponent_scores.append(evaluation)

                # hands_cache[joined_hand] = evaluation
                # else:
                #     opponent_scores.append(hands_cache[joined_hand])
                # print('cache used')

            if len(opponent_scores) != len(villain_ranges):
                continue

            # joined_hand = str(our_hand + complete_board)
            # if joined_hand not in hands_cache:
            our_score = evaluator.evaluate(
                complete_board, our_hand)
            # our_score = evaluation

            #     hands_cache[joined_hand] = evaluation
            # else:
            #     our_score = hands_cache[joined_hand]

            min_opponent_score = min(opponent_scores)

            if our_score < min_opponent_score:
                our_wins += 1
            elif our_score == min_opponent_score:
                ties += 1
            else:
                for idx, opponent_score in enumerate(opponent_scores):
                    if opponent_score == min_opponent_score:
                        villains_wins[idx] += 1
    else:
        for _ in range(iterations):

            opponent_scores = []
            deck = Deck()
            # deck.shuffle()
            for card in known_cards:
                deck.cards.remove(card)

            villain_hands = []
            for villain_range in villain_ranges:
                try:
                    villain_hand = generate_villain_hand(
                        villain_range, known_cards + [hand for villain_hand in villain_hands for hand in villain_hand])
                except:
                    continue

                for card in villain_hand:
                    deck.cards.remove(card)

                villain_hands.append(villain_hand)

            remaining_board = deck.draw(1)
            complete_board = board + [remaining_board]

            for villain_hand in villain_hands:
                # joined_hand = str(villain_hand + complete_board)
                # if joined_hand not in hands_cache:
                evaluation = evaluator.evaluate(
                    complete_board, villain_hand)
                opponent_scores.append(evaluation)

                # hands_cache[joined_hand] = evaluation
                # else:
                #     opponent_scores.append(hands_cache[joined_hand])
                # print('cache used')

            if len(opponent_scores) != len(villain_ranges):
                continue

            # joined_hand = str(our_hand + complete_board)
            # if joined_hand not in hands_cache:
            our_score = evaluator.evaluate(
                complete_board, our_hand)
            # our_score = evaluation

            #     hands_cache[joined_hand] = evaluation
            # else:
            #     our_score = hands_cache[joined_hand]

            min_opponent_score = min(opponent_scores)

            if our_score < min_opponent_score:
                our_wins += 1
            elif our_score == min_opponent_score:
                ties += 1
            else:
                for idx, opponent_score in enumerate(opponent_scores):
                    if opponent_score == min_opponent_score:
                        villains_wins[idx] += 1

    games_played += iterations
    cur_time = time.time()
    print(f"Games played in {title}: {games_played} in {cur_time - start} seconds.")

    total_simulations = our_wins + ties + sum(villains_wins)
    win_probability = (our_wins / total_simulations) * 100
    tie_probability = (ties / total_simulations) * 100
    villain_probabilities = [
        (villain_wins / total_simulations) * 100 for villain_wins in villains_wins]

    # print(hands_cache)
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
    villain_ranges = [ranges[villain_name]
                      for villain_name in villain_range_names]

    for board in boards[:3]:
        for our_hand in our_hands[:]:
            if any(card in our_hand for card in board):
                continue
            equity = simulate_equity(
                our_hand, villain_ranges, board, num_simulations, query[0])
            villain_probs_str = '; '.join(f"{villain_name}; {prob:.2f}" for villain_name, prob in zip(
                villain_range_names, equity['villain_probabilities']))
            result_line = (
                f"{title}; {our_range_name}; {join_cards(board)}; {join_cards(our_hand)}; {equity['win_probability']:.2f}; "
                f"Tie: {equity['tie_probability']:.2f}; {villain_probs_str}"
            )
            results.append(result_line)

    end = time.time()

    output_file = f"output_{title}.txt"
    print(
        f"Simulation completed. Results for query '{title}' saved to {output_file} file in {int(end-start)} seconds.")
    
    with open(output_file, 'w') as file:
        file.write('\n'.join(results))

# Main function to run the script
def main():
    hands_file = 'hands.txt'
    boards_file = 'boards.txt'
    queries_file = 'queries.txt'
    ranges_folder = 'ranges'

    hands = read_hands(hands_file)
    boards = read_boards(boards_file)
    queries = parse_queries(queries_file)
    ranges = read_ranges(ranges_folder, hands)

    print("Simulation started...")

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(
            process_query, query, boards, ranges, NUM_SIMULATIONS) for query in queries[:]]
        for future in as_completed(futures):
            future.result()

    print('All queries completed.')

if __name__ == "__main__":
    main()

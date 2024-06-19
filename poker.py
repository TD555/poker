import os
import random
import numpy as np

# Define constants
NUM_SIMULATIONS = 10000  # Number of Monte Carlo simulations

# Function to read hands from hands.txt
def read_hands(file_path):
    hands = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Ignore empty lines
                hand, cards = line.strip().split(':')
                hands[hand.strip()] = [c.strip() for c in cards.split(',') if c.strip()]
    return hands

# Function to read boards from boards.txt
def read_boards(file_path):
    boards = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Ignore empty lines
                boards.append(line.strip())
    return boards

# Function to read ranges from individual range files
def read_ranges(folder_path):
    ranges = {}
    range_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    for file_name in range_files:
        range_name = os.path.splitext(file_name)[0]
        ranges[range_name] = []
        with open(os.path.join(folder_path, file_name), 'r') as file:
            for line in file:
                if line.strip():  # Ignore empty lines
                    # print(line.strip().split(','))
                    ranges[range_name].extend([item.split(':') for item in line.strip().split(',')])
    return ranges

# Function to parse queries from queries.txt
def parse_queries(file_path):
    queries = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Ignore empty lines
                queries.append(line.strip().split(';')[:-1])
    return queries

# Function to simulate equity using Monte Carlo simulations
def simulate_equity(our_range, villain_ranges, board, ):
    our_combos = our_range
    villain_combos = [villain_range for villain_range, _ in villain_ranges]
    
    board_cards = board.split() if board else []
    
    our_wins = 0
    total_hands = 0
    
    for _ in range(NUM_SIMULATIONS):
        random.shuffle(our_combos)
        random.shuffle(villain_combos)
        
        our_hand = our_combos[0]
        villain_hand = villain_combos[0]
        
        our_score = evaluate_hand(our_hand, board_cards)
        villain_score = evaluate_hand(villain_hand, board_cards)
        
        if our_score > villain_score:
            our_wins += 1
        elif our_score == villain_score:
            our_wins += 0.5
        
        total_hands += 1
    
    equity = our_wins / total_hands
    return equity

# Function to evaluate the strength of a hand given the board
def evaluate_hand(hand, board):
    # Placeholder function, implement your hand evaluation logic here
    return random.random()  # Replace with actual hand evaluation logic

# Main function to run the script
def main():
    # Read input files
    hands_file = 'hands.txt'
    boards_file = 'boards.txt'
    queries_file = 'queries.txt'
    ranges_folder = 'ranges'
    
    hands = read_hands(hands_file)
    # print(hands)
    boards = read_boards(boards_file)
    queries = parse_queries(queries_file)
    ranges = read_ranges(ranges_folder)
    # Iterate through each query
    results = []
    for query in queries:
        title = query[0]
        our_range_name = query[1]
        villain_range_names = query[2:]
        
        our_range = ranges[our_range_name]
        villain_ranges = [(villain_name, ranges[villain_name]) for villain_name in villain_range_names]
        
        for board in boards:
            equity = simulate_equity(our_range, villain_ranges, board, NUM_SIMULATIONS)
            result_line = f"{title}; {our_range_name}; " + "; ".join([f"{villain_name}; " for villain_name, _ in villain_ranges]) + f"{board}; {equity}"
            results.append(result_line)
    
    # Write results to output file
    output_file = 'output.txt'
    with open(output_file, 'w') as file:
        for result in results:
            file.write(result + '\n')
    
    print(f"Simulation completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()

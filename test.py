from treys import Card, Evaluator, Deck

def calculate_win_probability_with_known_opponents(our_hand, board, opponents_hands, iterations=100000):
    evaluator = Evaluator()
    our_wins = 0
    ties = 0
    
    for _ in range(iterations):
        deck = Deck()
        # Remove known cards from the deck
        known_cards = our_hand + board + [card for hand in opponents_hands for card in hand]
        # print(known_cards)
        for card in known_cards:
            deck.cards.remove(card)
        
        # Draw remaining board cards
        remaining_board = deck.draw(5 - len(board))
        complete_board = board + remaining_board
        
        # Evaluate hands
        our_score = evaluator.evaluate(complete_board, our_hand)
        opponent_scores = [evaluator.evaluate(complete_board, opp_hand) for opp_hand in opponents_hands]
        
        if our_score < min(opponent_scores):
            our_wins += 1
        elif our_score == min(opponent_scores):
            if opponent_scores.count(min(opponent_scores)) == 1:
                our_wins += 1
            else:
                ties += 1

    win_probability = our_wins / iterations
    tie_probability = ties / iterations

    return win_probability, tie_probability

# Example usage
# Our hand: Ah, Kh (Ace of hearts, King of hearts)
# Board: 2c, 7d, Qs (2 of clubs, 7 of diamonds, Queen of spades)
# Opponent hands: [Js, Ts], [8d, 9d]
our_hand = [Card.new('Ah'), Card.new('Ac')]
board = [Card.new('2c'), Card.new('7d'), Card.new('Qs')]
opponents_hands = [
    [Card.new('Js'), Card.new('Ts')],  # Opponent 1 hand
    [Card.new('7s'), Card.new('Qd')],   # Opponent 2 hand
    [Card.new('2s'), Card.new('Qc')] 
]

win_prob, tie_prob = calculate_win_probability_with_known_opponents(our_hand, board, opponents_hands)
print(f"Win probability: {win_prob * 100:.2f}%")
print(f"Tie probability: {tie_prob * 100:.2f}%")

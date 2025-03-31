from flask import Flask, request, render_template_string, redirect
import random

app = Flask(__name__)

# Initialize game state
game_state = {
    "player1_secret": None,  # Player 1's secret number
    "player2_secret": None,  # Player 2's secret number
    "player1_guesses": [],  # Player 1's guesses
    "player2_guesses": [],  # Player 2's guesses
    "current_player": 1,  # 1 for Player 1, 2 for Player 2
    "game_over": False,
    "winner": None,
    "message": "Player 1: Enter your secret 4-digit number (no repeating digits).",
    "setup_phase": True  # True during number selection, False during guessing
}

def evaluate_guess(secret, guess):
    """Evaluate the guess and return (correct_digits, correct_positions)."""
    correct_positions = 0
    correct_digits = 0

    secret_digits = list(secret)
    guess_digits = list(guess)

    # Step 1: Check for correct digits in correct positions
    for i in range(4):
        if secret_digits[i] == guess_digits[i]:
            correct_positions += 1

    # Step 2: Check for correct digits (any position)
    secret_copy = secret_digits.copy()
    guess_copy = guess_digits.copy()

    for i in range(4):
        if secret_copy[i] == guess_copy[i]:
            secret_copy[i] = None
            guess_copy[i] = None

    for i in range(4):
        if guess_copy[i] is not None and guess_copy[i] in secret_copy:
            correct_digits += 1
            secret_copy[secret_copy.index(guess_copy[i])] = None

    return correct_digits, correct_positions

# HTML template for the game
GAME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mastermind - Two Players</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #ff6f61, #de4d86);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            color: #fff;
        }
        .container {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            text-align: center;
            width: 90%;
            max-width: 600px;
        }
        h1 {
            color: #ff6f61;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        p {
            font-size: 1.2em;
            color: #333;
        }
        input[type="text"] {
            padding: 12px;
            font-size: 1.1em;
            width: 100%;
            margin: 15px 0;
            border: 2px solid #de4d86;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            border-color: #ff6f61;
        }
        button {
            padding: 12px 25px;
            background-color: #ff6f61;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.1em;
            transition: background-color 0.3s, transform 0.1s;
        }
        button:hover {
            background-color: #de4d86;
            transform: scale(1.05);
        }
        .message {
            margin: 20px 0;
            font-weight: 600;
            font-size: 1.3em;
            color: #ff6f61;
        }
        .winner-message {
            font-size: 1.5em;
            color: #fff;
            background: linear-gradient(45deg, #ff6f61, #de4d86);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: #fff;
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
            color: #333;
        }
        th {
            background-color: #ff6f61;
            color: white;
        }
        .player-turn {
            font-size: 1.2em;
            color: #de4d86;
            margin: 10px 0;
        }
        .restart {
            background-color: #007bff;
        }
        .restart:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mastermind - Two Players</h1>
        {% if setup_phase %}
        <p>{{ message }}</p>
        <form method="POST" action="/set_secret">
            <input type="text" name="secret" maxlength="4" placeholder="Enter a 4-digit number" required>
            <button type="submit">Submit Secret Number</button>
        </form>
        {% else %}
        <p class="player-turn">Player {{ current_player }}'s Turn</p>
        <p>Guess your opponent's 4-digit number!</p>
        <p class="message">{{ message }}</p>
        {% if game_over %}
        <p class="winner-message">{{ winner }} Wins!</p>
        {% endif %}
        <h2>Player 1's Guesses</h2>
        {% if player1_guesses %}
        <table>
            <tr>
                <th>Guess</th>
                <th>Correct Digits</th>
                <th>Correct Positions</th>
            </tr>
            {% for guess, correct_digits, correct_positions in player1_guesses %}
            <tr>
                <td>{{ guess }}</td>
                <td>{{ correct_digits }}</td>
                <td>{{ correct_positions }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        <h2>Player 2's Guesses</h2>
        {% if player2_guesses %}
        <table>
            <tr>
                <th>Guess</th>
                <th>Correct Digits</th>
                <th>Correct Positions</th>
            </tr>
            {% for guess, correct_digits, correct_positions in player2_guesses %}
            <tr>
                <td>{{ guess }}</td>
                <td>{{ correct_digits }}</td>
                <td>{{ correct_positions }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        {% if not game_over %}
        <form method="POST" action="/guess">
            <input type="text" name="guess" maxlength="4" placeholder="Enter a 4-digit number" required>
            <button type="submit">Submit Guess</button>
        </form>
        {% else %}
        <form method="POST" action="/restart">
            <button type="submit" class="restart">Play Again</button>
        </form>
        {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    """Display the game page."""
    return render_template_string(GAME_PAGE, 
                                 message=game_state["message"], 
                                 player1_guesses=game_state["player1_guesses"],
                                 player2_guesses=game_state["player2_guesses"],
                                 current_player=game_state["current_player"],
                                 game_over=game_state["game_over"],
                                 winner=game_state["winner"],
                                 setup_phase=game_state["setup_phase"])

@app.route('/set_secret', methods=['POST'])
def set_secret():
    """Handle setting the secret numbers for both players."""
    secret = request.form.get('secret').strip()

    # Validate the secret number
    if not secret.isdigit() or len(secret) != 4 or len(set(secret)) != 4:
        game_state["message"] = "Invalid number! Please enter a 4-digit number with no repeating digits."
        return redirect('/')

    if game_state["player1_secret"] is None:
        game_state["player1_secret"] = secret
        game_state["message"] = "Player 2: Enter your secret 4-digit number (no repeating digits)."
        return redirect('/')
    else:
        game_state["player2_secret"] = secret
        game_state["setup_phase"] = False
        game_state["message"] = "Player 1: Guess Player 2's number!"
        game_state["current_player"] = 1
        return redirect('/')

@app.route('/guess', methods=['POST'])
def guess():
    """Handle the player's guess."""
    if game_state["game_over"] or game_state["setup_phase"]:
        return redirect('/')

    guess = request.form.get('guess').strip()

    # Validate the guess
    if not guess.isdigit() or len(guess) != 4 or len(set(guess)) != 4:
        game_state["message"] = "Invalid guess! Please enter a 4-digit number with no repeating digits."
        return redirect('/')

    # Determine which player's turn it is
    if game_state["current_player"] == 1:
        # Player 1 guesses Player 2's number
        secret = game_state["player2_secret"]
        correct_digits, correct_positions = evaluate_guess(secret, guess)
        game_state["player1_guesses"].append((guess, correct_digits, correct_positions))
        if correct_positions == 4:
            game_state["game_over"] = True
            game_state["winner"] = "Player 1"
            game_state["message"] = f"Player 1 guessed the number {secret}!"
        else:
            game_state["current_player"] = 2
            game_state["message"] = "Player 2: Guess Player 1's number!"
    else:
        # Player 2 guesses Player 1's number
        secret = game_state["player1_secret"]
        correct_digits, correct_positions = evaluate_guess(secret, guess)
        game_state["player2_guesses"].append((guess, correct_digits, correct_positions))
        if correct_positions == 4:
            game_state["game_over"] = True
            game_state["winner"] = "Player 2"
            game_state["message"] = f"Player 2 guessed the number {secret}!"
        else:
            game_state["current_player"] = 1
            game_state["message"] = "Player 1: Guess Player 2's number!"

    return redirect('/')

@app.route('/restart', methods=['POST'])
def restart():
    """Restart the game."""
    game_state["player1_secret"] = None
    game_state["player2_secret"] = None
    game_state["player1_guesses"] = []
    game_state["player2_guesses"] = []
    game_state["current_player"] = 1
    game_state["game_over"] = False
    game_state["winner"] = None
    game_state["message"] = "Player 1: Enter your secret 4-digit number (no repeating digits)."
    game_state["setup_phase"] = True
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

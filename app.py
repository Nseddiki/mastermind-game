from flask import Flask, request, render_template_string, redirect
import random

app = Flask(__name__)

# Initialize game state
game_state = {
    "secret_number": None,  # The number to guess
    "guesses": [],  # List of (guess, correct_digits, correct_positions)
    "game_over": False,
    "message": "Welcome to Mastermind! Guess a 4-digit number (no repeating digits)."
}

def generate_secret_number():
    """Generate a 4-digit number with no repeating digits."""
    digits = random.sample(range(0, 10), 4)  # Select 4 unique digits
    return ''.join(map(str, digits))

def evaluate_guess(secret, guess):
    """Evaluate the guess and return (correct_digits, correct_positions)."""
    correct_positions = 0  # Number of digits that are correct and in the correct position
    correct_digits = 0  # Number of digits that are correct (any position)

    # Convert to lists for easier comparison
    secret_digits = list(secret)
    guess_digits = list(guess)

    # Step 1: Check for correct digits in correct positions
    for i in range(4):
        if secret_digits[i] == guess_digits[i]:
            correct_positions += 1

    # Step 2: Check for correct digits (any position)
    # Create copies to avoid counting digits that are already matched in correct positions
    secret_copy = secret_digits.copy()
    guess_copy = guess_digits.copy()

    # Remove digits that are in correct positions to avoid double counting
    for i in range(4):
        if secret_copy[i] == guess_copy[i]:
            secret_copy[i] = None
            guess_copy[i] = None

    # Count remaining correct digits (in wrong positions)
    for i in range(4):
        if guess_copy[i] is not None and guess_copy[i] in secret_copy:
            correct_digits += 1
            # Remove the matched digit from secret_copy to avoid double counting
            secret_copy[secret_copy.index(guess_copy[i])] = None

    return correct_digits, correct_positions

# HTML template for the game
GAME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mastermind</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 90%;
            max-width: 500px;
        }
        h1 {
            color: #333;
        }
        p {
            font-size: 16px;
            color: #555;
        }
        input[type="text"] {
            padding: 10px;
            font-size: 16px;
            width: 100%;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .message {
            margin: 15px 0;
            font-weight: bold;
            color: #d9534f;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        th {
            background-color: #f2f2f2;
        }
        .restart {
            background-color: #007bff;
            margin-top: 10px;
        }
        .restart:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mastermind</h1>
        <p>Guess a 4-digit number (no repeating digits)!</p>
        <p class="message">{{ message }}</p>
        {% if guesses %}
        <table>
            <tr>
                <th>Guess</th>
                <th>Correct Digits</th>
                <th>Correct Positions</th>
            </tr>
            {% for guess, correct_digits, correct_positions in guesses %}
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
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    """Display the game page."""
    # Start a new game if no secret number is set
    if game_state["secret_number"] is None:
        game_state["secret_number"] = generate_secret_number()
        game_state["guesses"] = []
        game_state["game_over"] = False
        game_state["message"] = "Welcome to Mastermind! Guess a 4-digit number (no repeating digits)."
    return render_template_string(GAME_PAGE, 
                                 message=game_state["message"], 
                                 guesses=game_state["guesses"], 
                                 game_over=game_state["game_over"])

@app.route('/guess', methods=['POST'])
def guess():
    """Handle the player's guess."""
    if game_state["game_over"]:
        return redirect('/')

    guess = request.form.get('guess').strip()

    # Validate the guess
    if not guess.isdigit() or len(guess) != 4 or len(set(guess)) != 4:
        game_state["message"] = "Invalid guess! Please enter a 4-digit number with no repeating digits."
        return render_template_string(GAME_PAGE, 
                                     message=game_state["message"], 
                                     guesses=game_state["guesses"], 
                                     game_over=game_state["game_over"])

    # Evaluate the guess
    correct_digits, correct_positions = evaluate_guess(game_state["secret_number"], guess)
    game_state["guesses"].append((guess, correct_digits, correct_positions))

    # Check if the player won
    if correct_positions == 4:
        game_state["message"] = f"Congratulations! You guessed the number {game_state['secret_number']} in {len(game_state['guesses'])} attempts!"
        game_state["game_over"] = True
    else:
        game_state["message"] = "Keep guessing! Use the hints to narrow it down."

    return render_template_string(GAME_PAGE, 
                                 message=game_state["message"], 
                                 guesses=game_state["guesses"], 
                                 game_over=game_state["game_over"])

@app.route('/restart', methods=['POST'])
def restart():
    """Restart the game."""
    game_state["secret_number"] = generate_secret_number()
    game_state["guesses"] = []
    game_state["game_over"] = False
    game_state["message"] = "New game started! Guess a 4-digit number (no repeating digits)."
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

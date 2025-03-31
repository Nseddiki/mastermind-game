from flask import Flask, request, render_template_string, redirect
import random

app = Flask(__name__)

# Initialize game state
game_state = {
    "player1_secret": None,
    "player2_secret": None,
    "player1_guesses": [],
    "player2_guesses": [],
    "current_player": 1,
    "game_over": False,
    "winner": None,
    "message": "Player 1: Enter your secret 4-digit number (no repeating digits).",
    "setup_phase": True,
    "timer": 30  # Timer for each turn (in seconds)
}

def evaluate_guess(secret, guess):
    """Evaluate the guess and return (correct_digits, correct_positions)."""
    correct_positions = 0
    correct_digits = 0

    secret_digits = list(secret)
    guess_digits = list(guess)

    for i in range(4):
        if secret_digits[i] == guess_digits[i]:
            correct_positions += 1

    secret_copy = secret_digits.copy()
    guess_copy = guess_digits.copy()
    for digit in set(guess_copy):
        correct_digits += min(secret_copy.count(digit), guess_copy.count(digit))

    return correct_digits, correct_positions

# HTML template for the game
GAME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mastermind - Two Players</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&family=Lobster&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(45deg, #00c4cc, #7fffd4, #00c4cc);
            background-size: 400%;
            animation: gradient 15s ease infinite;
            margin: 0;
            color: #fff;
            position: relative;
            overflow-x: hidden;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        body::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://www.transparenttextures.com/patterns/stardust.png') repeat;
            opacity: 0.2;
            z-index: -1;
            animation: parallax 50s linear infinite;
        }
        @keyframes parallax {
            0% { background-position: 0 0; }
            100% { background-position: 1000px 1000px; }
        }
        .container {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            text-align: center;
            width: 90%;
            max-width: 600px;
            margin: 20px auto;
            animation: fadeIn 1.5s ease-in-out;
            overflow-y: auto;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 {
            font-family: 'Lobster', cursive;
            font-size: 3em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #00c4cc, #7fffd4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: glow 3s ease-in-out infinite;
        }
        @keyframes glow {
            0%, 100% { text-shadow: 0 0 10px #00c4cc, 0 0 20px #7fffd4; }
            50% { text-shadow: 0 0 20px #00c4cc, 0 0 30px #7fffd4; }
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
            border: 2px solid #7fffd4;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.5s, box-shadow 0.5s;
        }
        input[type="text"]:focus {
            border-color: #00c4cc;
            box-shadow: 0 0 10px rgba(0, 196, 204, 0.5);
        }
        button {
            padding: 12px 25px;
            background: linear-gradient(45deg, #00c4cc, #7fffd4);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.1em;
            transition: transform 0.5s, box-shadow 0.5s;
        }
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(0, 196, 204, 0.5);
        }
        button:active {
            animation: bounce 0.5s;
        }
        @keyframes bounce {
            0% { transform: scale(1); }
            50% { transform: scale(0.95); }
            100% { transform: scale(1); }
        }
        .message {
            margin: 20px 0;
            font-weight: 600;
            font-size: 1.3em;
            color: #00c4cc;
            animation: slideIn 1s ease-in-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .winner-message {
            font-size: 1.5em;
            color: #fff;
            background: linear-gradient(45deg, #00c4cc, #7fffd4);
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
            background: linear-gradient(45deg, #00c4cc, #7fffd4);
            color: white;
        }
        tr {
            animation: zoomIn 0.8s ease-in-out;
        }
        @keyframes zoomIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        tr:hover {
            background-color: rgba(0, 196, 204, 0.1);
            transition: background-color 0.5s;
        }
        .player-turn {
            font-size: 1.2em;
            color: #7fffd4;
            margin: 10px 0;
            animation: slideIn 1s ease-in-out;
        }
        .restart {
            background: linear-gradient(45deg, #ff4500, #ff8c00);
            margin: 10px;
        }
        .restart:hover {
            box-shadow: 0 0 15px rgba(255, 69, 0, 0.5);
        }
        .timer {
            font-size: 1.2em;
            color: #333;
            margin: 10px 0;
        }
        .timer.warning {
            color: #ff4500;
            animation: shake 0.5s infinite;
        }
        @keyframes shake {
            0% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            50% { transform: translateX(5px); }
            75% { transform: translateX(-5px); }
            100% { transform: translateX(0); }
        }
        .audio-control {
            margin: 10px 0;
        }
        .audio-control button {
            background: linear-gradient(45deg, #ff4500, #ff8c00);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mastermind - Two Players</h1>
        <form method="POST" action="/restart" style="display: inline;">
            <button type="submit" class="restart">Restart Game</button>
        </form>
        <div class="audio-control">
            <button onclick="toggleAudio()">Toggle Music</button>
        </div>
        <audio id="backgroundMusic" loop>
            <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        <audio id="winSound">
            <source src="https://www.myinstants.com/media/sounds/applause.mp3" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        {% if setup_phase %}
        <p>{{ message }}</p>
        <form method="POST" action="/set_secret">
            <input type="text" name="secret" maxlength="4" placeholder="Enter a 4-digit number" required>
            <button type="submit">Submit Secret Number</button>
        </form>
        {% else %}
        <p class="player-turn">Player {{ current_player }}'s Turn</p>
        <p>Guess your opponent's 4-digit number!</p>
        <p class="timer" id="timer">Time Left: {{ timer }}s</p>
        <p class="message">{{ message }}</p>
        {% if game_over %}
        <p class="winner-message">{{ winner }} Wins!</p>
        <script>
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
            });
            document.getElementById('winSound').play();
        </script>
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
        <form method="POST" action="/guess" id="guessForm">
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
    <script>
        let timer = {{ timer }};
        let timerInterval;
        const timerElement = document.getElementById('timer');

        function startTimer() {
            timer = {{ timer }};
            timerElement.textContent = `Time Left: ${timer}s`;
            timerElement.classList.remove('warning');
            clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                timer--;
                timerElement.textContent = `Time Left: ${timer}s`;
                if (timer <= 5) {
                    timerElement.classList.add('warning');
                }
                if (timer <= 0) {
                    clearInterval(timerInterval);
                    alert("Time's up! Switching to the other player.");
                    document.getElementById('guessForm').submit();
                }
            }, 1000);
        }

        function toggleAudio() {
            const audio = document.getElementById('backgroundMusic');
            if (audio.paused) {
                audio.play();
            } else {
                audio.pause();
            }
        }

        {% if not setup_phase and not game_over %}
        startTimer();
        {% endif %}

        document.getElementById('guessForm')?.addEventListener('submit', (e) => {
            const guessInput = document.querySelector('input[name="guess"]');
            const guess = guessInput.value;
            const secret = {{ current_player }} === 1 ? "{{ player2_secret }}" : "{{ player1_secret }}";
            const { correct_digits, correct_positions } = evaluate_guess(secret, guess);
            if (correct_positions !== 4) {
                guessInput.classList.add('shake');
                setTimeout(() => {
                    guessInput.classList.remove('shake');
                }, 500);
            }
        });

        function evaluate_guess(secret, guess) {
            let correct_positions = 0;
            let correct_digits = 0;
            const secret_digits = secret.split('');
            const guess_digits = guess.split('');

            for (let i = 0; i < 4; i++) {
                if (secret_digits[i] === guess_digits[i]) {
                    correct_positions++;
                }
            }

            const secret_copy = [...secret_digits];
            const guess_copy = [...guess_digits];
            for (let digit of new Set(guess_copy)) {
                correct_digits += Math.min(secret_copy.filter(x => x === digit).length, guess_copy.filter(x => x === digit).length);
            }

            return { correct_digits, correct_positions };
        }
    </script>
    <style>
        .shake {
            animation: shake 0.5s;
        }
    </style>
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
                                 setup_phase=game_state["setup_phase"],
                                 timer=game_state["timer"],
                                 player1_secret=game_state["player1_secret"] or "",
                                 player2_secret=game_state["player2_secret"] or "")

@app.route('/set_secret', methods=['POST'])
def set_secret():
    """Handle setting the secret numbers for both players."""
    secret = request.form.get('secret').strip()

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

    if not guess.isdigit() or len(guess) != 4 or len(set(guess)) != 4:
        game_state["message"] = "Invalid guess! Please enter a 4-digit number with no repeating digits."
        return redirect('/')

    if game_state["current_player"] == 1:
        secret = game_state["player2_secret"]
        correct_digits, correct_positions = evaluate_guess(secret, guess)
        game_state["player1_guesses"].append((guess, correct_digits, correct_positions))
        if correct_positions == 4:
            game_state["game_over"] = True
            game_state["winner"] = "Player 1"
            game_state["message"] = f"Player 1 guessed the number {secret}!"
        else:
            game_state["current_player"] = 2
            game_state["message"] = "Player 2: Guess Player 1's number! Try a different number!"
    else:
        secret = game_state["player1_secret"]
        correct_digits, correct_positions = evaluate_guess(secret, guess)
        game_state["player2_guesses"].append((guess, correct_digits, correct_positions))
        if correct_positions == 4:
            game_state["game_over"] = True
            game_state["winner"] = "Player 2"
            game_state["message"] = f"Player 2 guessed the number {secret}!"
        else:
            game_state["current_player"] = 1
            game_state["message"] = "Player 1: Guess Player 2's number! Try a different number!"

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

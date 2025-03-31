from flask import Flask, request, render_template_string, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games
                 (room_id TEXT PRIMARY KEY, player1_secret TEXT, player2_secret TEXT,
                  player1_guesses TEXT, player2_guesses TEXT, current_player INTEGER,
                  game_over INTEGER, winner TEXT)''')
    conn.commit()
    conn.close()

init_db()

def evaluate_guess(secret, guess):
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

# HTML template for the game (Web version)
GAME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mastermind - Two Players</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&family=Lobster&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <script src="https://unpkg.com/photon-realtime-js@4.1.4.7/dist/photon-realtime-js.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
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
            animation: fadeIn 0.1s ease-in-out;
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
            transition: border-color 0.1s, box-shadow 0.1s;
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
            transition: transform 0.1s, box-shadow 0.1s, background 0.1s;
            position: relative;
            overflow: hidden;
        }
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(0, 196, 204, 0.5);
        }
        button:active {
            transform: scale(0.95);
            background: linear-gradient(45deg, #7fffd4, #00c4cc);
        }
        button::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.3s, height 0.3s;
        }
        button:active::after {
            width: 200px;
            height: 200px;
        }
        .message {
            margin: 20px 0;
            font-weight: 600;
            font-size: 1.3em;
            color: #00c4cc;
            animation: slideIn 0.1s ease-in-out;
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
            animation: zoomIn 0.1s ease-in-out;
        }
        @keyframes zoomIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        tr:hover {
            background-color: rgba(0, 196, 204, 0.1);
            transition: background-color 0.1s;
        }
        .player-turn {
            font-size: 1.2em;
            color: #7fffd4;
            margin: 10px 0;
            animation: slideIn 0.1s ease-in-out;
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
        .loading {
            display: none;
            font-size: 1em;
            color: #00c4cc;
            margin: 10px 0;
        }
        .loading::after {
            content: '...';
            animation: dots 1s steps(3, end) infinite;
        }
        @keyframes dots {
            0% { content: '.'; }
            33% { content: '..'; }
            66% { content: '...'; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mastermind - Two Players</h1>
        <button class="restart" onclick="restartGame()">Restart Game</button>
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
        <div id="gameContent">
            <p id="message">Waiting for another player to join...</p>
            <div class="loading" id="loading">Loading...</div>
        </div>
    </div>
    <script>
        const socket = io();
        let photonClient;
        let roomId = null;
        let playerId = null;
        let timer = 30;
        let timerInterval;
        const timerElement = document.getElementById('timer');

        // Initialize Photon
        function initPhoton() {
            photonClient = new Photon.LoadBalancing.LoadBalancingClient(Photon.ConnectionProtocol.Ws, 'YOUR_PHOTON_APP_ID', '1.0');
            photonClient.onEvent = (code, content, actorNr) => {
                if (code === 1) { // Custom event for game state update
                    updateGameState(content);
                }
            };
            photonClient.onJoinRoom = () => {
                roomId = photonClient.myRoom().name;
                playerId = photonClient.myActor().actorNr;
                socket.emit('join_room', { room_id: roomId, player_id: playerId });
            };
            photonClient.connectToRegionMaster('EU');
            photonClient.joinRandomRoom({}, 2); // Join a room with max 2 players
        }

        function startTimer() {
            timer = 30;
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
                    submitGuess(null);
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

        async function setSecret(event) {
            event.preventDefault();
            const form = event.target;
            const secret = form.querySelector('input[name="secret"]').value;
            socket.emit('set_secret', { room_id: roomId, player_id: playerId, secret: secret });
        }

        async function submitGuess(event) {
            if (event) event.preventDefault();
            const form = document.getElementById('guessForm');
            const guessInput = form.querySelector('input[name="guess"]');
            const guess = guessInput.value;
            socket.emit('guess', { room_id: roomId, player_id: playerId, guess: guess });
        }

        async function restartGame() {
            socket.emit('restart', { room_id: roomId, player_id: playerId });
        }

        function updateGameState(data) {
            const gameContent = document.getElementById('gameContent');
            let html = '';
            if (data.setup_phase) {
                html = `
                    <p id="message">${data.message}</p>
                    <form id="setSecretForm" onsubmit="setSecret(event)">
                        <input type="text" name="secret" maxlength="4" placeholder="Enter a 4-digit number" required>
                        <button type="submit">Submit Secret Number</button>
                    </form>
                `;
            } else {
                html = `
                    <p class="player-turn" id="playerTurn">Player ${data.current_player}'s Turn</p>
                    <p>Guess your opponent's 4-digit number!</p>
                    <p class="timer" id="timer">Time Left: ${data.timer}s</p>
                    <p class="message" id="message">${data.message}</p>
                    <div class="loading" id="loading">Loading...</div>
                `;
                if (data.game_over) {
                    html += `<p class="winner-message" id="winnerMessage">${data.winner} Wins!</p>`;
                    confetti({
                        particleCount: 100,
                        spread: 70,
                        origin: { y: 0.6 }
                    });
                    document.getElementById('winSound').play();
                }
                html += `
                    <h2>Player 1's Guesses</h2>
                    <table id="player1Guesses">
                        <tr>
                            <th>Guess</th>
                            <th>Correct Digits</th>
                            <th>Correct Positions</th>
                        </tr>
                `;
                data.player1_guesses.forEach(guess => {
                    html += `
                        <tr>
                            <td>${guess[0]}</td>
                            <td>${guess[1]}</td>
                            <td>${guess[2]}</td>
                        </tr>
                    `;
                });
                html += `</table>`;
                html += `
                    <h2>Player 2's Guesses</h2>
                    <table id="player2Guesses">
                        <tr>
                            <th>Guess</th>
                            <th>Correct Digits</th>
                            <th>Correct Positions</th>
                        </tr>
                `;
                data.player2_guesses.forEach(guess => {
                    html += `
                        <tr>
                            <td>${guess[0]}</td>
                            <td>${guess[1]}</td>
                            <td>${guess[2]}</td>
                        </tr>
                    `;
                });
                html += `</table>`;
                if (!data.game_over) {
                    html += `
                        <form id="guessForm" onsubmit="submitGuess(event)">
                            <input type="text" name="guess" maxlength="4" placeholder="Enter a 4-digit number" required>
                            <button type="submit">Submit Guess</button>
                        </form>
                    `;
                } else {
                    html += `<button class="restart" onclick="restartGame()">Play Again</button>`;
                }
            }
            gameContent.innerHTML = html;
            if (!data.setup_phase && !data.game_over) {
                startTimer();
            }
        }

        socket.on('game_state', (data) => {
            updateGameState(data);
            if (photonClient && data.room_id === roomId) {
                photonClient.raiseEvent(1, data); // Broadcast game state to other players
            }
        });

        initPhoton();
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
    return render_template_string(GAME_PAGE)

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    player_id = data['player_id']
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE room_id = ?", (room_id,))
    game = c.fetchone()
    if not game:
        c.execute("INSERT INTO games (room_id, player1_secret, player2_secret, player1_guesses, player2_guesses, current_player, game_over, winner) VALUES (?, NULL, NULL, ?, ?, 1, 0, NULL)",
                  (room_id, str([]), str([])))
        conn.commit()
    conn.close()
    emit_game_state(room_id)

@socketio.on('set_secret')
def handle_set_secret(data):
    room_id = data['room_id']
    player_id = data['player_id']
    secret = data['secret']
    if not secret.isdigit() or len(secret) != 4 or len(set(secret)) != 4:
        update_game_state(room_id, message="Invalid number! Please enter a 4-digit number with no repeating digits.")
        return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE room_id = ?", (room_id,))
    game = c.fetchone()
    if game[1] is None:  # player1_secret
        c.execute("UPDATE games SET player1_secret = ? WHERE room_id = ?", (secret, room_id))
        update_game_state(room_id, message="Player 2: Enter your secret 4-digit number (no repeating digits).")
    else:
        c.execute("UPDATE games SET player2_secret = ?, setup_phase = 0, message = ? WHERE room_id = ?",
                  (secret, "Player 1: Guess Player 2's number!", room_id))
    conn.commit()
    conn.close()
    emit_game_state(room_id)

@socketio.on('guess')
def handle_guess(data):
    room_id = data['room_id']
    player_id = data['player_id']
    guess = data['guess']
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE room_id = ?", (room_id,))
    game = c.fetchone()
    if game[6]:  # game_over
        conn.close()
        return
    if not guess.isdigit() or len(guess) != 4 or len(set(guess)) != 4:
        update_game_state(room_id, message="Invalid guess! Please enter a 4-digit number with no repeating digits.")
        conn.close()
        return
    player1_guesses = eval(game[3])
    player2_guesses = eval(game[4])
    current_player = game[5]
    if current_player == 1:
        secret = game[2]  # player2_secret
        correct_digits, correct_positions = evaluate_guess(secret, guess)
        player1_guesses.append((guess, correct_digits, correct_positions))
        if correct_positions == 4:
            c.execute("UPDATE games SET player1_guesses = ?, game_over = 1, winner = ?, message = ? WHERE room_id = ?",
                      (str(player1_guesses), "Player 1", f"Player 1 guessed the number {secret}!", room_id))
        else:
            c.execute("UPDATE games SET player1_guesses = ?, current_player = 2, message = ? WHERE room_id = ?",
                      (str(player1_guesses), "Player 2: Guess Player 1's number! Try a different number!", room_id))
    else:
        secret = game[1]  # player1_secret
        correct_digits, correct_positions = evaluate_guess(secret, guess)
        player2_guesses.append((guess, correct_digits, correct_positions))
        if correct_positions == 4:
            c.execute("UPDATE games SET player2_guesses = ?, game_over = 1, winner = ?, message = ? WHERE room_id = ?",
                      (str(player2_guesses), "Player 2", f"Player 2 guessed the number {secret}!", room_id))
        else:
            c.execute("UPDATE games SET player2_guesses = ?, current_player = 1, message = ? WHERE room_id = ?",
                      (str(player2_guesses), "Player 1: Guess Player 2's number! Try a different number!", room_id))
    conn.commit()
    conn.close()
    emit_game_state(room_id)

@socketio.on('restart')
def handle_restart(data):
    room_id = data['room_id']
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("UPDATE games SET player1_secret = NULL, player2_secret = NULL, player1_guesses = ?, player2_guesses = ?, current_player = 1, game_over = 0, winner = NULL, message = ?, setup_phase = 1 WHERE room_id = ?",
              (str([]), str([]), "Player 1: Enter your secret 4-digit number (no repeating digits).", room_id))
    conn.commit()
    conn.close()
    emit_game_state(room_id)

def update_game_state(room_id, **kwargs):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE room_id = ?", (room_id,))
    game = c.fetchone()
    data = {
        "room_id": room_id,
        "player1_secret": game[1],
        "player2_secret": game[2],
        "player1_guesses": eval(game[3]),
        "player2_guesses": eval(game[4]),
        "current_player": game[5],
        "game_over": bool(game[6]),
        "winner": game[7],
        "message": game[8] if len(game) > 8 else "Waiting for another player to join...",
        "setup_phase": bool(game[9] if len(game) > 9 else 1),
        "timer": 30
    }
    for key, value in kwargs.items():
        data[key] = value
        if key != "timer":
            c.execute(f"UPDATE games SET {key} = ? WHERE room_id = ?", (value, room_id))
    conn.commit()
    conn.close()
    socketio.emit('game_state', data)

def emit_game_state(room_id):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE room_id = ?", (room_id,))
    game = c.fetchone()
    data = {
        "room_id": room_id,
        "player1_secret": game[1],
        "player2_secret": game[2],
        "player1_guesses": eval(game[3]),
        "player2_guesses": eval(game[4]),
        "current_player": game[5],
        "game_over": bool(game[6]),
        "winner": game[7],
        "message": game[8] if len(game) > 8 else "Waiting for another player to join...",
        "setup_phase": bool(game[9] if len(game) > 9 else 1),
        "timer": 30
    }
    conn.close()
    socketio.emit('game_state', data)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

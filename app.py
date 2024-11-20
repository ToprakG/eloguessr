from flask import Flask, jsonify, render_template, send_from_directory, request # type: ignore
import requests
import random

app = Flask(__name__)

# List of Lichess usernames to fetch random games from
USERS = ["german11"]

# Fetch list of tournaments (created, started, finished)
def fetch_tournaments():
    url = 'https://lichess.org/api/tournament'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        tournaments = data.get('created', []) + data.get('started', []) + data.get('finished', [])
        return tournaments
    else:
        print("Error fetching tournaments")
        return []

# Fetch participants from a tournament by tournament ID
def fetch_tournament_participants(tournament_id):
    url = f'https://lichess.org/api/tournament/{tournament_id}'
    response = requests.get(url)
    
    if response.status_code == 200:
        tournament = response.json()
        participants = tournament.get('standing', {}).get('players', [])
        usernames = [player['name'] for player in participants]
        return usernames
    else:
        print(f"Error fetching participants for tournament {tournament_id}")
        return []

# Add a random participant from a random tournament to USERS
def add_random_user_to_users():
    tournaments = fetch_tournaments()

    if tournaments:
        # Pick a random tournament
        tournament = random.choice(tournaments)
        tournament_id = tournament['id']
        print(f"Chosen Tournament ID: {tournament_id}")
        
        # Fetch participants from the chosen tournament
        participants = fetch_tournament_participants(tournament_id)

        if participants:
            # Choose a random participant and append their username to USERS
            random_user = random.choice(participants)
            USERS.append(random_user)
            print(f"Added {random_user} to USERS")
            return random_user
            # print(f"Added {random_user} to USERS")
        else:
            print("No participants found for the chosen tournament.")
            add_random_user_to_users()
    else:
        return "No tournaments found."

@app.route('/')
def index():
    return render_template('index.html')

import json

@app.route('/get_game', methods=['GET'])
def get_game():
    add_random_user_to_users()
    username = random.choice(USERS)
    url = f'https://lichess.org/api/games/user/{username}?max=1&opening=true&moves=true'
    
    try:
        response = requests.get(url, headers={'Accept': 'application/x-ndjson'})
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch game data'}), 500

        # Parse NDJSON response
        games = [json.loads(line) for line in response.text.strip().split('\n') if line]
        if not games:
            return jsonify({'error': 'No games found'}), 404

        # Process the first game
        game = games[0]
        moves = game.get('moves', '').split(' ')
        players = game.get('players', {})
        print(players)
        white_elo = players.get('white', {}).get('rating', 'Unknown')
        black_elo = players.get('black', {}).get('rating', 'Unknown')
        opening_name = game.get('opening', {}).get('name', 'Unknown')

        data = {
            'id': game.get('id'),
            'moves': moves,
            'white_elo': white_elo,
            'black_elo': black_elo,
            'opening': opening_name,
        }

        return jsonify(data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    
@app.route('/img/chesspieces/wikipedia/<filename>')
def chess_pieces(filename):
    return send_from_directory('static/img/chesspieces/wikipedia', filename)

if __name__ == '__main__':
    app.run(debug=True)

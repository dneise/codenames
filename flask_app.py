import random
from enum import IntEnum
from pathlib import Path
import json
from pprint import pprint
from collections import namedtuple

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    abort,
)
from flask_cors import CORS

APP = Flask(__name__)
CORS(APP)

FILE_DIR = Path(__file__).parent.absolute()
CARDS = open(FILE_DIR / 'cards').read().splitlines()
TABLES = {
    # table_key: table_state
}

class GameState(IntEnum):
    T1_explains = 0
    T1_guess = 1
    T2_explains = 2
    T2_guess = 3
    Game_END = 4


def team_no_and_guess_from_game_state(gs):
    team_no, guess = gs//2 + 1, bool(1 - gs%2)
    return team_no, guess

def advance_game_state(gs):
    return (gs + 1) % 4


@APP.route('/new_tipp/<table_key>/<team>', methods=['POST'])
def new_tipp(table_key, team):
    table_state = TABLES.get(table_key, new_table(table_key))
    TABLES[table_key] = table_state

    print(f'new_tipp {table_key} {team}')

    new_tipp = request.json["new_tipp"]
    table_state["tipps"].append(new_tipp)

    table_state["game_state"] = advance_game_state(table_state["game_state"])

    pprint(table_state)
    return jsonify(table_state)

@APP.route('/reset/<table_key>')
def reset(table_key):
    print(f'RESET {table_key}')
    del TABLES[table_key]
    table_state = TABLES.get(table_key, new_table(table_key))

    pprint(table_state)
    return jsonify(table_state)

@APP.route('/stop_guessing/<table_key>')
def stop_guessing(table_key):
    print(f'stop guessing {table_key}')
    table_state = TABLES.get(table_key, new_table(table_key))
    TABLES[table_key] = table_state

    table_state["game_state"] = advance_game_state(table_state["game_state"])

    pprint(table_state)
    return jsonify(table_state)


@APP.route('/guess/<table_key>/<int:row>/<int:col>', methods=['GET'])
def guess(table_key, row, col):
    table_state = TABLES.get(table_key, new_table(table_key))
    TABLES[table_key] = table_state

    print(f'guess {table_key} {row} {col}')

    card_id = row * 5 + col

    card = table_state['cards'][card_id]
    gs = table_state["game_state"]
    team_no, guess = team_no_and_guess_from_game_state(gs)
    if card["solution"] == team_no:
        # revealed card was correct, no change of game_state
        pass
    elif card["solution"] == 3:
        # bomb was revealed -> game ends
        gs = 4
    else:
        # revealed card was incorred
        gs = advance_game_state(gs)

    card["revealed"] = True
    table_state["game_state"] = gs

    pprint(table_state)
    return jsonify(table_state)

@APP.route('/table/<table_key>', methods=['GET'])
def table(table_key=None):
    table_state = TABLES.get(table_key, new_table(table_key))
    TABLES[table_key] = table_state

    pprint(table_state)
    return jsonify(table_state)

def new_table(table_key):
    random.seed(table_key)
    table_cards = random.sample(CARDS, 25)

    start_team = random.randint(1, 2)  # 1 or 2
    other_team = 3 - start_team        # 2 or 1

    # Team 1: 1, Team 2: 2, Neutral: 0 , Bomb: 3
    table_solution = [3] + [0]*7 + [start_team]*9 + [other_team]*8
    random.shuffle(table_solution)

    revealed = [False]*25

    game_state = GameState.T1_explains if start_team == 1 else GameState.T2_explains

    cards = []
    for i, card_text in enumerate(table_cards):
        cards.append({
            "text": card_text,
            "revealed": revealed[i],
            "solution": table_solution[i],
        })


    table_state = {
        'key': table_key,
        'start_team': start_team,
        'game_state': game_state.value,
        "cards": cards,
        "tipps": []
    }
    return table_state


if __name__ == '__main__':

    @APP.route('/')
    def index_html():
        return send_from_directory(FILE_DIR, "index.html")

    APP.run(
        host='0.0.0.0',
        # host='127.0.0.1',
        port=8080,
        debug=True,
    )

from flask import Flask, request, render_template, session
from flask_socketio import SocketIO
from chess_logic import make_move, puzzlemove, get_puzzle, get_opponent_move

app = Flask(__name__)
app.secret_key = "mein_geheimer_schluessel"
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/standard.html")
def standard():
    return render_template("standard.html")

@app.route("/puzzle.html")
def puzzle():
    return render_template("puzzle.html")

@app.route("/move", methods=["POST"])
def move_route():
    move_data = request.json
    move_uci = move_data.get("move")

    if not move_uci:
        return jsonify({"error": "Kein Zug übermittelt!"})

    return make_move(move_uci)

@app.route("/get_puzzle")
def get_puzzle_route():
    return get_puzzle()

@app.route("/puzzlemove", methods=["POST"])
def puzzlemove_route():
    move_data = request.json
    move_uci = move_data.get("move")

    if not move_uci:
        return jsonify({"error": "Kein Zug übermittelt!"})

    return puzzlemove(move_uci)

@app.route("/get_opponent_move", methods=["GET"])
def get_opponent_move_route():
    return get_opponent_move()

@socketio.on("connect")
def handle_connect():
    socketio.emit("update", {"fen": session.get("fen", "")})

if __name__ == "__main__":
    socketio.run(app, debug=True)
# Diese Datei dient als Server - flask ist quasi die Schnittstelle zwischen Backend und Frontend

from flask import Flask, request, render_template, session, jsonify
from flask_socketio import SocketIO
from chess_logic import make_move, puzzlemove, get_puzzle, get_opponent_move

# Erstellt die Flask app
app = Flask(__name__)

# Wird für session benötigt
app.secret_key = "mein_geheimer_schluessel"


# Startseite wird erstellt (flask syntaxt)
@app.route("/")
def index():
    return render_template("index.html")

#Wenn die Seite auf "/standard.html" zugreifen wird, verlinkt flask auf diese html
@app.route("/standard.html")
def standard():
    return render_template("standard.html")

@app.route("/puzzle.html")
def puzzle():
    return render_template("puzzle.html")


# Diese App wird ausgeführt, sobald move an flask weitergegeben wird, im Javascript in der standard html: "body: JSON.stringify({ "move": move })" -> hier wird der move an diese Funktion übergeben
@app.route("/move", methods=["POST"])
def move_route():
    move_data = request.json #Genau an der Stelle holt er sich die JSON Daten vom Frontend. z.B {"move": "e2e4"})
    move_uci = move_data.get("move") # Extrahiert den Zug als UCI-Notation (Universal Chess Interface)

    # Falls kein Zug übermittelt wurde
    if not move_uci:
        return jsonify({"error": "Kein Zug übermittelt!"})

    return make_move(move_uci) # Führt den Zug aus -> mit der Funktion make_move aus der chess_logic file

#Diese Route lädt das Puzzle des Tages aus Lichess
@app.route("/get_puzzle")
def get_puzzle_route():
    return get_puzzle()

# Diese Route empfängt die Moves vom puzzle aus dem Frontend und verarbeitet diese
@app.route("/puzzlemove", methods=["POST"])
def puzzlemove_route():
    move_data = request.json
    move_uci = move_data.get("move")

    if not move_uci:
        return jsonify({"error": "Kein Zug übermittelt!"})

    return puzzlemove(move_uci)


# Diese Route gibt den nächsten Zug des Gegners zurück -> auch für das Puzzle notwending, da man ja nur jeden zweiten Zug macht
@app.route("/get_opponent_move", methods=["GET"])
def get_opponent_move_route():
    return get_opponent_move()



# Startet die Flask-App 
if __name__ == "__main__":
    app.run(debug=True)
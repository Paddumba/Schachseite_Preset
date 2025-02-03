from flask import Flask, jsonify, request, render_template, session
from flask_socketio import SocketIO
import chess
import requests
import chess.pgn
import io


app = Flask(__name__)
app.secret_key = "mein_geheimer_schluessel"
socketio = SocketIO(app, cors_allowed_origins="*")  # Erlaubt WebSocket-Verbindungen

board = chess.Board()  # Initialisiere das Schachbrett
data= None

# Lädt die Startseite
@app.route("/")
def index():
    return render_template("index.html")


#Lädt die HTML-Seite für das normale Schachspiel.
@app.route("/standard")
def standard():

    return render_template("standard.html")


# Diese Flask App wird vom Frontend aufgerufen, um einen Zug ins Backend zu schicken und dieser Funktion zu prüfen ob er legal ist, zu Checkmate führt, ...
@app.route("/move", methods=["POST"]) #Akzeptiert nur Anfragen, die Daten senden
def make_move(): #Führt einen Zug aus und sendet die neue Stellung an das Frontend.
    
    global board
    move_data = request.json #JSOn Daten werden vom Frontend erhalten zb {move: "e2e4"}
    try:
        move = chess.Move.from_uci(move_data["move"]) #UCI-Zug umwandeln e2e4 etc.
        if move in board.legal_moves: # Überprüft ob der Zug legal ist
            board.push(move) #Zug ausführen

            # Überprüfung ob der Zug Schachmatt, Patt etc ist
            status ="Spiel läuft ..."
            if board.is_checkmate(): # Ist der Zug Schachmatt
                status = "Checkmate!"
            elif board.is_stalemate():
                status="Stalemate!"
            else:
                status ="OK"


            socketio.emit("update", {"fen": board.fen(),  "status": status})  # Neues Brett und Status an alle Clients senden

            return jsonify({"fen": board.fen(), "status": status})
        
        else:
            return jsonify({"error": "Ungültiger Zug!"})
            
    except Exception:
        return jsonify({"error": "Fehlerhafte Eingabe!"})


#Lädt die Seite puzzle html
@app.route("/puzzle")
def puzzle():
    #Lädt die HTML-Seite mit dem Schachbrett.
    return render_template("puzzle.html")



@app.route("/get_puzzle")
def get_puzzle():
    global data #Zugriff auf die globale Variable sodass die Daten hier verarbeitet werden können

    url = "https://lichess.org/api/puzzle/daily"
    response = requests.get(url)

    if response.status_code != 200:
        return jsonify({"error": "Fehler beim Abrufen des Puzzles"}), 500

    data = response.json()
    #print("Lichess API:", data)  # Debugging

    pgn_text = data.get("game", {}).get("pgn", "")
    puzzle_moves = data.get("puzzle", {}).get("solution", [])
    #print("pgn text", pgn_text)
    #print("Puzzle moves", puzzle_moves)

    if not pgn_text or not puzzle_moves:
        return jsonify({"error": "Ungültige Puzzledaten erhalten."}), 500
    
    session["puzzle_moves"] = puzzle_moves
    session["current_move_index"] = 0  # Start des Puzzles


    # 🎯 PGN in ein Schachspiel umwandeln
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)
    #print("game", game)

    # 🎯 Bis zum richtigen Puzzle-Zug vorspulen
    board = game.board()
    initial_ply = data["puzzle"].get("initialPly", 0)
    initial_ply +=1
    #print("Intial ply", initial_ply)
    for move in game.mainline_moves():
        board.push(move)
        initial_ply -= 1
        if initial_ply == 0:
            break  # Wir sind jetzt am Start des Puzzles

    # 🎯 FEN extrahieren
    puzzle_fen = board.fen()
    

    return jsonify({"fen": puzzle_fen, "solution": puzzle_moves})



@app.route("/puzzlemove", methods=["POST"])
def puzzlemove():
    global board, session, data

    if "puzzle_data" not in session:
        return jsonify({"error": "Kein Puzzle geladen!"}), 500

    puzzle_moves = session["puzzle_moves"]
    
    move_data = request.json
    move_uci = move_data.get("move") 
    print(move_uci)
    if not move_uci:
        return jsonify({"error": "Kein Zug übermittelt!"})
    
    current_move_index=session["current_move_index"]
    print("currentmove", current_move_index)

    try:
        move = chess.Move.from_uci(move_uci)

        # Prüfen, ob der Zug korrekt ist
        current_move_index = session.get("current_move_index", 0)
        print("move_index", current_move_index)
        print("len_puzzzlemoves", len(puzzle_moves))
        print(move_uci, puzzle_moves[current_move_index] )

        if current_move_index >= len(puzzle_moves) or move_uci != puzzle_moves[current_move_index]:
            return jsonify({"error": "Falscher Zug! Versuche es erneut."})
            
        else:
            # ✅ Richtiger Zug -> ausführen
            board.push(move)
            current_move_index += 1
            session["current_move_index"] = current_move_index

            if current_move_index % 2 == 0:
            # Spielerzug - serverseitig verwalten
                status = "Spielerzug"
            else:
                # Computerzug - wird sofort vom Frontend durchgeführt
                opponent_move_uci = puzzle_moves[current_move_index]
                opponent_move = chess.Move.from_uci(opponent_move_uci)
                board.push(opponent_move)
                current_move_index += 1
                session["current_move_index"] = current_move_index
                status = "Computerzug"

            # Status und das Schachbrett (FEN) zurück an das Frontend senden
            return jsonify({"fen": board.fen(), "status": status})

    except Exception:
        return jsonify({"error": "Fehlerhafte Eingabe!"})





# Das Socketio ist für eine bidirektionale Kommunikation -> wenn also mehrere Spieler an einem Spiel spielen wird das Spiel für beide Spieler immer automatisch aktualisiert!
@socketio.on("connect")
def handle_connect():
    #Sendet die aktuelle Brettstellung, wenn sich ein Client verbindet.
    socketio.emit("update", {"fen": board.fen()})




if __name__ == "__main__":
    socketio.run(app, debug=True)
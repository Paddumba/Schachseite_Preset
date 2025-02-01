from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO
import chess
from custom import setup_custom_game


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Erlaubt WebSocket-Verbindungen

board = chess.Board()  # Initialisiere das Schachbrett
knookbard = setup_custom_game()

@app.route("/")
def index():
    #Lädt die HTML-Seite mit dem Schachbrett.
    return render_template("index.html")

@app.route("/standard")
def standard():
    #Lädt die HTML-Seite mit dem Schachbrett.
    return render_template("standard.html")

@app.route("/knook")
def knook():
    #Lädt die HTML-Seite mit dem Schachbrett.
    return render_template("knook.html")


@app.route("/board", methods=["GET"])
def get_board():
    #Gibt das aktuelle Brett als FEN zurück.
    return jsonify({"fen": board.fen()}) # Konvertiert die FEN in eine json Antwort, die das Frontend benutzen kann

@app.route("/move", methods=["POST"]) #Akzeptiert nur Anfragen, die Daten senden
def make_move(): #Führt einen Zug aus und sendet die neue Stellung an das Frontend.
    global knookbard
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


# Das Socketio ist für eine bidirektionale Kommunikation -> wenn also mehrere Spieler an einem Spiel spielen wird das Spiel für beide Spieler immer automatisch aktualisiert!
@socketio.on("connect")
def handle_connect():
    #Sendet die aktuelle Brettstellung, wenn sich ein Client verbindet.
    socketio.emit("update", {"fen": board.fen()})

if __name__ == "__main__":
    socketio.run(app, debug=True)
# In dieser Datei wird die gesamte Spiellogik gespeichert

import chess
import requests
import io
import chess.pgn
from flask import session, jsonify

# Initialisiere die Schachbretter
puzzle_board = chess.Board()
standard_board = chess.Board()



# Führt den Zug im Standard Spiel aus
def make_move(move_uci):
    global standard_board

    # 🛠️ Falls noch kein Standardspiel gestartet wurde oder aus einem Puzzle gewechselt wurde, setze das Brett zurück
    if "standard_mode" not in session or not session["standard_mode"]:

        standard_board = chess.Board()  # Starte mit der Standardstellung
        session["standard_mode"] = True  # Merke dir, dass jetzt ein Standardspiel läuft
        session["fen"] = standard_board.fen()  # Setze die FEN neu


    try:

        move = chess.Move.from_uci(move_uci) # Konvertiert die UCI-Notation (z. B. "e2e4") in einen Schachzug

        if move in standard_board.legal_moves: #Prüft ob der Zug legal ist
            standard_board.push(move)

            # Überprüfe den Spielstatus -> dies ist wichtig für das Frontend, sodass der Status angezeigt werden kann
            status = "Spiel läuft ..."
            if standard_board.is_checkmate():
                status = "Checkmate!"
                session["standard_mode"] = False  
            elif standard_board.is_stalemate():
                status = "Stalemate!"
                session["standard_mode"] = False  
            else:
                status = "OK"

            session["fen"] = standard_board.fen() # Aktualisiere die Session mit der neuen Stellung

            return jsonify({"fen": standard_board.fen(), "status": status}) #Übergibt an das Frontend die fen und den status. Im Frontend ist das die Zeile: let data = await response.json();
        
        else:
            return jsonify({"error": "Ungültiger Zug!"}) # Falls der Zug illegal ist
    
    # Falls die try fehlt -> es irgendeinen Fehler gibt
    except Exception as e:
        return jsonify({"error": f"Fehlerhafte Eingabe! Details: {str(e)}"})








# Holt das Tagespuzzle von Lichess
def get_puzzle():
    
    global puzzle_board


    # Setzt Standardspiel-Session zurück, weil jetzt ein Puzzle gespielt wird
    session["standard_mode"] = False  

    # Die nächsten beiden Befehle sind Lichess API Befehle um das Puzzle zu holen und in response zu speichern
    url = "https://lichess.org/api/puzzle/daily"
    response = requests.get(url)

    if response.status_code != 200:
        return jsonify({"error": "Fehler beim Abrufen des Puzzles"}), 500

    data = response.json()# Umwandlung der Antwort in JSON

    pgn_text = data.get("game", {}).get("pgn", "") #Hier wird aus der Antwort die pgn ausgelesen, die ist nachher für das Vorspulen wichtig

    puzzle_moves = data.get("puzzle", {}).get("solution", []) #Die Lösungszüge des Puzzles

    #Debugging
    if not pgn_text or not puzzle_moves:
        return jsonify({"error": "Ungültige Puzzledaten erhalten."}), 500

    # PGN in ein Schachspiel umwandeln - auch das ist wichtig für das Vorspulen
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)

    # Bis zum richtigen Puzzle-Zug vorspulen
    puzzle_board = game.board()
    initial_ply = data["puzzle"].get("initialPly", 0) + 1 #Wenn das Puzzle am Move 38 kommt steht hier in initialply die Zahl 38

    for move in game.mainline_moves():
        puzzle_board.push(move)
        initial_ply -= 1
        if initial_ply == 0:
            break  # Wir sind jetzt am Start des Puzzles
           
           
    # Speichert die Brettstellung, die Lösung und den Index im Session-Speicher. Das ist wichtig, da verschiedene Funktionen auf diese Variablen zugreifen und über die session Funktion von flask werden diese zwischengespeichert  
    session["fen"] = puzzle_board.fen()
    session["puzzle_moves"] = puzzle_moves
    session["current_move_index"] = 0

    return jsonify({"fen": session["fen"], "solution": puzzle_moves}) #Antwort an das Frontend








#Führt einen Spielerzug im Puzzlemodus aus
def puzzlemove(move_uci):
    
    global puzzle_board

    if "puzzle_moves" not in session:
        return jsonify({"error": "Kein Puzzle geladen!"}), 500

    puzzle_moves = session["puzzle_moves"]
    current_move_index = session.get("current_move_index", 0)

    if not move_uci:
        return jsonify({"error": "Kein Zug übermittelt!"})

    try:
        if "fen" in session:
            puzzle_board = chess.Board(session["fen"])  # Stelle die korrekte Stellung wieder her

        move = chess.Move.from_uci(move_uci)

        # Prüfen, ob der Zug korrekt ist
        if current_move_index >= len(puzzle_moves) or move_uci != puzzle_moves[current_move_index]:
            return jsonify({"error": "Falscher Zug! Versuche es erneut."})

        #  Spielerzug ausführen
        puzzle_board.push(move)
        current_move_index += 1
        session["current_move_index"] = current_move_index
        session["fen"] = puzzle_board.fen()

        # 🎯 Prüfen, ob das Puzzle vorbei ist
        if current_move_index >= len(puzzle_moves):
            return jsonify({"fen": session["fen"], "message": "Glückwunsch! Puzzle gelöst!"})

        return jsonify({"fen": session["fen"], "status": "OK", "waiting_for_opponent": True}) # Hier wird an das Frontend zurückgegeben, dass der Gegnerzug nun dran ist, falls das Puzzle nicht vorbei ist

    except Exception as e:
        return jsonify({"error": f"Fehlerhafte Eingabe! Details: {str(e)}"})








#  Führt den nächsten Gegnerzug im Puzzle aus
def get_opponent_move():

    global puzzle_board

    if "puzzle_moves" not in session:
        return jsonify({"error": "Kein Puzzle geladen!"}), 500

    puzzle_moves = session["puzzle_moves"]
    current_move_index = session.get("current_move_index", 0)

    if current_move_index >= len(puzzle_moves):
        return jsonify({"opponent_move": None})  # Kein weiterer Zug

    # ✅ Gegnerzug ausführen
    opponent_move_uci = puzzle_moves[current_move_index]
    opponent_move = chess.Move.from_uci(opponent_move_uci)
    puzzle_board.push(opponent_move)
    current_move_index += 1
    session["current_move_index"] = current_move_index
    session["fen"] = puzzle_board.fen()

    return jsonify({"fen": puzzle_board.fen(), "opponent_move": opponent_move_uci})
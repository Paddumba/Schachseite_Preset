import chess
import requests
import io
import chess.pgn
from flask import session, jsonify

# Initialisiere das Schachbrett
puzzle_board = chess.Board()
standard_board = chess.Board()

def make_move(move_uci):
    """ Führt einen Spielerzug im normalen Schachspiel aus """
    global standard_board

    try:
        move = chess.Move.from_uci(move_uci)
        if move in standard_board.legal_moves:
            standard_board.push(move)

            # Überprüfe den Spielstatus
            status = "Spiel läuft ..."
            if standard_board.is_checkmate():
                status = "Checkmate!"
            elif standard_board.is_stalemate():
                status = "Stalemate!"
            else:
                status = "OK"

            return jsonify({"fen": standard_board.fen(), "status": status})
        else:
            return jsonify({"error": "Ungültiger Zug!"})
    
    except Exception as e:
        return jsonify({"error": f"Fehlerhafte Eingabe! Details: {str(e)}"})


def get_puzzle():
    """ Holt das Tagespuzzle von Lichess und bereitet das Brett vor """
    global puzzle_board

    url = "https://lichess.org/api/puzzle/daily"
    response = requests.get(url)

    if response.status_code != 200:
        return jsonify({"error": "Fehler beim Abrufen des Puzzles"}), 500

    data = response.json()
    pgn_text = data.get("game", {}).get("pgn", "")
    puzzle_moves = data.get("puzzle", {}).get("solution", [])

    if not pgn_text or not puzzle_moves:
        return jsonify({"error": "Ungültige Puzzledaten erhalten."}), 500

    # 🎯 PGN in ein Schachspiel umwandeln
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)

    # 🎯 Bis zum richtigen Puzzle-Zug vorspulen
    puzzle_board = game.board()
    initial_ply = data["puzzle"].get("initialPly", 0) + 1

    for move in game.mainline_moves():
        puzzle_board.push(move)
        initial_ply -= 1
        if initial_ply == 0:
            break  # Wir sind jetzt am Start des Puzzles

    session["fen"] = puzzle_board.fen()
    session["puzzle_moves"] = puzzle_moves
    session["current_move_index"] = 0

    return jsonify({"fen": session["fen"], "solution": puzzle_moves})


def puzzlemove(move_uci):
    """ Führt einen Spielerzug im Puzzlemodus aus """
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

        # ✅ Spielerzug ausführen
        puzzle_board.push(move)
        current_move_index += 1
        session["current_move_index"] = current_move_index
        session["fen"] = puzzle_board.fen()

        # 🎯 Prüfen, ob das Puzzle vorbei ist
        if current_move_index >= len(puzzle_moves):
            return jsonify({"fen": session["fen"], "message": "Glückwunsch! Puzzle gelöst!"})

        return jsonify({"fen": session["fen"], "status": "OK", "waiting_for_opponent": True})

    except Exception as e:
        return jsonify({"error": f"Fehlerhafte Eingabe! Details: {str(e)}"})


def get_opponent_move():
    """ Führt den nächsten Gegnerzug im Puzzle aus """
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
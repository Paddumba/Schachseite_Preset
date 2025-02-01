import chess

class SimpleChessGame:
    def __init__(self):
        self.board = chess.Board()

    def play(self):
        """Hauptspiel-Schleife"""
        while not self.board.is_game_over():
            print(self.board)  # Schachbrett anzeigen
            move_uci = input(f"{'Weiß' if self.board.turn else 'Schwarz'} am Zug (z.B. e2e4): ")

            try:
                move = chess.Move.from_uci(move_uci)
                if move in self.board.legal_moves:
                    self.board.push(move)
                else:
                    print("Ungültiger Zug! Bitte einen legalen Zug eingeben.")
            except ValueError:
                print("Falsches Format! Bitte UCI-Notation nutzen (z.B. e2e4).")
        
        # Spielende
        print("\nSpiel vorbei!")
        if self.board.is_checkmate():
            print(f"Schachmatt! {'Schwarz' if self.board.turn else 'Weiß'} gewinnt!")
        elif self.board.is_stalemate():
            print("Patt! Unentschieden.")
        elif self.board.is_insufficient_material():
            print("Unentschieden wegen zu wenig Material.")
        elif self.board.is_seventyfive_moves():
            print("Remis nach 75 Zügen ohne Bauernzug oder Schlagzug.")
        elif self.board.is_fivefold_repetition():
            print("Remis durch fünffache Stellungswiederholung.")
        else:
            print("Unbekannter Spiel-Endzustand.")

# Spiel starten
game = SimpleChessGame()
game.play()
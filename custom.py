import chess

class Knook(chess.Piece):
    def __init__(self, color):
        self.color = color
        self.piece_type = chess.PAWN  # Wird als "Knook" behandelt

    def moves(self, square, board):
        """
        Berechnet alle möglichen Züge für den Knook auf dem Schachbrett.
        Der Knook bewegt sich wie ein Turm und wie ein Springer.
        """
        possible_moves = []
        
        # Turmbewegungen: horizontale und vertikale Züge
        for direction in [chess.NORTH, chess.SOUTH, chess.EAST, chess.WEST]:
            for i in range(1, 8):  # Turm kann sich bis zu 7 Felder weit bewegen
                target_square = square + i * direction
                if board.is_valid(target_square):
                    piece_at_target = board.piece_at(target_square)
                    if piece_at_target is None:  # Freies Feld
                        possible_moves.append(target_square)
                    elif piece_at_target.color != self.color:  # Gegnerische Figur
                        possible_moves.append(target_square)
                        break  # Kann nach der gegnerischen Figur nicht weiterziehen
                    else:
                        break  # Blockiert durch eine eigene Figur
                else:
                    break  # Außerhalb des Schachbretts
        
        # Springerbewegungen: "L"-förmige Züge
        knight_moves = [
            6, 10, 15, 17, -6, -10, -15, -17  # Bewegungsrichtungen eines Springers
        ]
        
        for move in knight_moves:
            target_square = square + move
            if board.is_valid(target_square):
                piece_at_target = board.piece_at(target_square)
                if piece_at_target is None:  # Freies Feld
                    possible_moves.append(target_square)
                elif piece_at_target.color != self.color:  # Gegnerische Figur
                    possible_moves.append(target_square)

        return possible_moves
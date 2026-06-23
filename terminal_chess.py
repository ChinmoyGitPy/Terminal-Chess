import os
import sys
import copy

#display pieces

vals_u = [("K","K"),("Q","Q"),("B","B"),("N","N"),("R","R"),("P","P")]
vals_l = [("K","k"),("Q","q"),("B","b"),("N","n"),("R","r"),("P","p")]
PIECES_WHITE = {(piece_type,"white"):piece for piece_type,piece in vals_u}
PIECES_BLACK = {(piece_type,"black"):piece for piece_type,piece in vals_l}
PIECES = PIECES_BLACK | PIECES_WHITE

#ansi colour codes

RESET  = "\033[0m"
BOLD  = "\033[1m"
DIM  = "\033[2m"
CYAN  = "\033[96m"
GREEN  = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
GREY = "\033[90m"

def apply_colour(text,colour):
    return f"{colour}{text}{RESET}"

def create_board():
    board = [[None]*8 for _ in range(8)]
    
    back_rank = ["R", "N", "B", "Q", "K", "B", "N", "R"]

    for col, piece in enumerate(back_rank):
        board[0][col] = (piece,"black")
        board[7][col] = (piece,"white")

    for col in range(8):
        board[1][col] = ("P","black")
        board[6][col] = ("P","white")

    return board

# helper functions

def is_on_board(row,col):
    return 0 <= row < 8 and 0 <= col < 8

def get_opponent_colour(colour):
    return "black" if colour == "white" else "white"

#move generation

def candidate_moves(board,row,col,game_state):
    piece = board[row][col]
    if not piece:
        return []
    
    piece_type, piece_colour = piece 
    opponent_colour = get_opponent_colour(piece_colour)
    candidate_moves = []

#sliding func

    def slide(delta_row,delta_col):
        next_row = row + delta_row
        next_col = col + delta_col

        while is_on_board(next_row,next_col):
            square_contents = board[next_row][next_col]
            if square_contents is None:
                candidate_moves.append((next_row,next_col))
            elif square_contents[1] == opponent_colour:
                candidate_moves.append((next_row, next_col))
                break
            else:
                break
            next_row += delta_row
            next_col += delta_col

#pawn

    if piece_type == "P":
        move_direction = -1 if piece_colour == "white" else 1
        pawn_starting_row = 6 if piece_colour == "white" else 1
        one_step_row = row + move_direction
        if is_on_board(one_step_row,col) and board[one_step_row][col] is None:
            candidate_moves.append((one_step_row,col))

            if row == pawn_starting_row:
                two_step_row = row+2* move_direction
                if board[two_step_row][col] is None:
                    candidate_moves.append((two_step_row,col))
        
        for side_step in (-1,1):
            capture_row = row + move_direction
            capture_col = col + side_step
            if is_on_board(capture_row, capture_col):
                target = board[capture_row][capture_col]
                if target and target[1] == opponent_colour:
                    candidate_moves.append((capture_row,capture_col))
                if game_state.get("ep") == (capture_row,capture_col):
                    candidate_moves.append((capture_row,capture_col))

#knight

    elif piece_type == "N":
        knight_jumps =[
            (-2, -1), (-2, +1),(+2, -1), (+2, +1),(-1, -2), (-1, +2),(+1, -2), (+1, +2)  
        ]
        for delta_row, delta_col in knight_jumps:
            target_row = row + delta_row
            target_col = col + delta_col

            if is_on_board(target_row,target_col):
                target = board[target_row][target_col]
                if target is None or target [1] == opponent_colour:
                    candidate_moves.append((target_row,target_col))

#bishop

    elif piece_type == "B":
        for direction in [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]:
            slide(*direction)

#rook

    elif piece_type == "R":
        for direction in [(-1, 0), (+1, 0), (0, -1), (0, +1)]:
            slide(*direction)

#queen

    elif piece_type == "Q":
        for direction in [
            (-1, -1), (-1, +1), (+1, -1), (+1, +1),(-1,  0), (+1,  0), ( 0, -1), ( 0, +1)
        ]:
            slide(*direction)

#king

    elif piece_type == "K":
        for delta_row in (-1,0,1):
            for delta_col in (-1,0,1):
                if delta_row == 0 and delta_col == 0:
                    continue
                target_row = row + delta_row
                target_col = col + delta_col
                if is_on_board(target_row,target_col):
                    target = board[target_row][target_col]
                    if target is None or target[1] == opponent_colour:
                        candidate_moves.append((target_row,target_col))

#castling

        castling_rights = game_state.get("castling", {})
        king_home_row = 7 if piece_colour == "white" else 0

        if row == king_home_row and col == 4:
            temp_state = dict(game_state)
            temp_state["ep"] = None

            #kingside

            if (
                castling_rights.get(piece_colour, {}).get("K") and
                board[king_home_row][5] is None and
                board[king_home_row][6] is None and
                not is_square_attacked(board, king_home_row,4,opponent_colour,temp_state) and
                not is_square_attacked(board, king_home_row,5,opponent_colour,temp_state)
            ):
                candidate_moves.append((king_home_row,6))

                #queenside

            if (
                castling_rights.get(piece_colour, {}).get("Q") and
                board[king_home_row][3] is None and
                board[king_home_row][2] is None and
                board[king_home_row][1] is None and
                not is_square_attacked(board, king_home_row,4,opponent_colour,temp_state) and
                not is_square_attacked(board, king_home_row,3,opponent_colour,temp_state)
            ):
                candidate_moves.append((king_home_row,2))

    return candidate_moves

def is_square_attacked(board,row,col,attacking_colour,game_state):
    temp_state = dict(game_state)
    temp_state["ep"] = None
    temp_state["castling"] = {"white": {"K": False, "Q": False}, "black": {"K": False, "Q": False}}

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece[1] == attacking_colour:
                if (row,col) in candidate_moves(board,r,c,temp_state):
                    return True
    return False

def find_king(board,colour):
    for row in range(8):
        for col in range(8):
            if board[row][col] == ("K",colour):
                return row,col
    raise ValueError(f"No {colour} king found on the board")

def is_king_in_check(board,colour,game_state):
    king_row, king_col = find_king(board,colour)
    return is_square_attacked(board,king_row,king_col, get_opponent_colour(colour), game_state)

def apply_move(board,from_row,from_col,to_row,to_col,game_state):
    new_board = copy.deepcopy(board)
    new_state = copy.deepcopy(game_state)
    piece_type, piece_colour = new_board[from_row][from_col]
    opponent_colour = get_opponent_colour(piece_colour)
    own_home_row = 7 if piece_colour == "white" else 0
    opponent_home_row = 0 if piece_colour == "white" else 7

    new_state["ep"] = None

    #en passant

    if piece_type == "P" and (to_row,to_col) == game_state.get("ep"):
        pawn_advance_direction = -1 if piece_colour == "white" else 1
        captured_pawn_row = to_row - pawn_advance_direction
        new_board[captured_pawn_row][to_col] = None 

    if piece_type == "P" and abs(to_row - from_row) == 2:
        skipped_row = (from_row + to_row) // 2
        new_state["ep"] =(skipped_row,from_col)

        #rook movement in castling

    if piece_type == "K" and abs(to_col - from_col) == 2:
        if to_col == 6:
            new_board[own_home_row][5] = new_board[own_home_row][7]
            new_board[own_home_row][7] = None
        else:
            new_board[own_home_row][3] = new_board[own_home_row][0]
            new_board[own_home_row][0] = None

    if piece_type == "K":
        new_state["castling"][piece_colour] = {"K": False, "Q":False}

    if piece_type == "R":
        if from_col == 7:
            new_state["castling"][piece_colour]["K"] = False
        if from_col == 0:
            new_state["castling"][piece_colour]["Q"] = False
            
    if (to_row, to_col) == (opponent_home_row,7):
        new_state["castling"][opponent_colour]["K"] = False
    if (to_row, to_col) == (opponent_home_row,0):
        new_state["castling"][opponent_colour]["Q"] = False

    new_board[to_row][to_col] = (piece_type,piece_colour)
    new_board[from_row][from_col] = None

    if piece_type == "P" and (to_row == 0 or to_row == 7):
        new_board[to_row][to_col] = ("Q", piece_colour)

    return new_board, new_state

def legal_moves(board,row,col,game_state):
    piece = board[row][col]
    if not piece:
        return []
    piece_colour = piece[1]
    legal = []
    for target_row, target_col in candidate_moves(board,row,col,game_state):
        board_after_move, state_after_move = apply_move(
            board, row, col, target_row, target_col, game_state)
        
        if not is_king_in_check(board_after_move,piece_colour,state_after_move):
            legal.append((target_row,target_col))
        
    return legal

def all_legal_moves(board,colour,game_state):
    all_moves = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece[1] == colour:
                for target_row, target_col in legal_moves(board,row,col,game_state):
                    all_moves.append((row,col,target_row,target_col))
    return all_moves

def is_checkmate(board,colour,game_state):
    no_legal_moves = not all_legal_moves(board,colour,game_state)
    king_is_in_check = is_king_in_check(board,colour,game_state)
    return no_legal_moves and king_is_in_check

def is_stalemate(board,colour,game_state):
    no_legal_moves = not all_legal_moves(board,colour,game_state)
    king_not_in_check = not is_king_in_check(board,colour,game_state)
    return no_legal_moves and king_not_in_check

horizontal_seperator = "+-----"*8+"+"

def cell_display(board,row,col,selected_square,valid_move_squares,last_move_squares,check_king_square):
    piece = board[row][col]

    is_selected_piece = selected_square and (row,col) == selected_square
    is_valid_destination = (row,col) in valid_move_squares
    is_last_move_square = (row,col) in last_move_squares
    is_king_in_check_square = check_king_square and (row,col) == check_king_square

    if piece:
        letter = PIECES[piece]

        if is_selected_piece:
            return apply_colour(f"[{letter}]", CYAN + BOLD)
        elif is_king_in_check_square:
            return apply_colour(f"!{letter}!", RED + BOLD)
        elif is_last_move_square:
            return apply_colour(f"~{letter}~", YELLOW)
        else:
            colour_code = WHITE + BOLD if piece[1] == "white" else GREY
            return apply_colour(f" {letter} ", colour_code)
        
    else:
        if is_valid_destination:
            return apply_colour(" * ",GREEN+BOLD)
        else:
            return "   "
        
def draw_board(board,game_state,selected_squares=None,valid_moves=None,last_move=None):
    valid_move_set = set(valid_moves or [])
    last_move_set = set()
    if last_move:
        from_row, from_col, to_row, to_col = last_move
        last_move_set = {(from_row,from_col),(to_row,to_col)}

    check_king_square = None
    for colour in ("white","black"):
        if is_king_in_check(board,colour,game_state):
            check_king_square = find_king(board,colour)

    column_header = "  " + "".join(f"  {chr(ord('a') + c)}   " for c in range(8))
    print(apply_colour(column_header, GREY))
    
    print(apply_colour(f"  {horizontal_seperator}", GREY))

    for row in range(8):
        rank_label = str(8-row)

        
        row_display = apply_colour(f"{rank_label} ", GREY)

        for col in range(8):
            cell_content = cell_display(board,row,col,selected_squares,valid_move_set,last_move_set,check_king_square)
            row_display += apply_colour("|", GREY) + f" {cell_content} "
        row_display += apply_colour("|", GREY) + apply_colour(f" {rank_label}", GREY)
        print(row_display)
        print(apply_colour(f"  {horizontal_seperator}", GREY))

    
    print(apply_colour(column_header, GREY))
    print()

def draw_status_bar(board,game_state,current_player_colour,message=""):

    captured_by_white = game_state.get("captured_by_white", [])
    captured_by_black = game_state.get("captured_by_black", [])

    white_captures_display = " ".join(captured_by_white) if captured_by_white else "-"
    black_captures_display = " ".join(captured_by_black) if captured_by_black else "-"

    is_in_check = is_king_in_check(board,current_player_colour,game_state)

    print(f"  {BOLD}Turn {game_state['move_number']}  |  {current_player_colour.upper()} to move{RESET}")
    print(f"  White captured: {white_captures_display}")
    print(f"  Black captured: {black_captures_display}")

    if is_in_check:
        print(apply_colour(f"\n  *** {current_player_colour.upper()} IS IN CHECK! ***", RED + BOLD))

    print()
    print(f"  {BOLD}Input:{RESET} square (e2) to select/move  |  e2e4 to move directly")
    print(f"         u=undo  r=restart  q=quit")
    print(f"  {DIM}White=UPPERCASE  black=lowercase  [X]=selected  *=valid move{RESET}")

    if message:
        # Show a highlighted message 
        print(apply_colour(f"\n  >> {message}", YELLOW))

    print()

def parse_square_notation(token):
    if (len(token) == 2
            and token[0] in "abcdefgh"
            and token[1] in "12345678"):
        col = ord(token[0]) - ord("a")
        row = 8 - int(token[1])
        return (row,col)
    return None

def parse_player_input(raw_input):

    cleaned = raw_input.strip().lower()

    if cleaned in ("q", "quit", "exit"):
        return ("command", "q")
    if cleaned in ("r", "restart", "new"):
        return ("command", "r")
    if cleaned in ("u", "undo", "z"):
        return ("command", "u")
    if len(cleaned) == 4:
        from_square = parse_square_notation(cleaned[:2])
        to_square   = parse_square_notation(cleaned[2:])
        if from_square and to_square:
            return ("move", from_square, to_square)
    square = parse_square_notation(cleaned)
    if square:
        return ("square", square)
    return ("invalid", cleaned)

def create_new_game_state():
    return {
        "castling": {
            "white": {"K": True, "Q": True},   
            "black": {"K": True, "Q": True},
        },
        "ep": None,              
        "move_number": 1,
        "captured_by_white": [],
        "captured_by_black": []
    }

def reset_game():
     return (
        create_board(),
        create_new_game_state(),
        "white",   
        None,     
        [],       
        None
    )

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def commit_move(board,game_state,current_player,from_row,from_col,to_row,to_col):

    en_passant_square = game_state.get("ep")

    captured_piece = board[to_row][to_col]

    piece_type = board[from_row][from_col][0]
    if piece_type == "P" and (to_row,to_col) == en_passant_square:
        pawn_direction = -1 if current_player == "white" else 1
        captured_piece = board[to_row - pawn_direction][to_col]

    new_board, new_state = apply_move(board, from_row, from_col, to_row, to_col, game_state)

    if piece_type == "P" and (to_row == 0 or to_row == 7):
        clear_screen()
        draw_board(new_board,new_state)

        promotion_options = {
            "q":"Q","r":"R","b":"B","n":"N"
        }

        while True:
            try:
                choice = input(
                    "  Promote to? Q=Queen  R=Rook  B=Bishop  N=Knight  [Q]: "
                ).strip().lower()
            except (EOFError,KeyboardInterrupt):
                choice = ""

            if choice == "" or choice not in promotion_options:
                choice = "q" 

            if choice in promotion_options:
                new_board[to_row][to_col] = (promotion_options[choice], current_player)
                break
        
    if captured_piece:
        capture_key = "captured_by_white" if current_player == "white" else "captured_by_black"
        new_state[capture_key].append(captured_piece[0])

    next_player = get_opponent_colour(current_player)
    if current_player == "black":
        new_state["move_number"] += 1

    return (
        new_board,new_state,next_player,None,[],(from_row,from_col,to_row,to_col)
    )

def run_game():
    board, game_state, current_player, selected_squares,valid_moves, last_move = reset_game()

    move_history = []

    status_message = ""

    while True:
        clear_screen()
        draw_board(board,game_state,selected_squares, valid_moves, last_move)
        draw_status_bar(board, game_state, current_player, status_message)
        status_message = ""

        if is_checkmate(board,current_player,game_state):
            winner=get_opponent_colour(current_player)
            print(apply_colour(f" CHECKMATE!\n  {winner.upper()} wins! \n", GREEN + BOLD))
            input("Press Enter to play again...")
            board, game_state, current_player, selected_squares,valid_moves, last_move = reset_game()
            continue

        if is_stalemate(board,current_player,game_state):
            print(apply_colour(f" STALEMATE It's a draw! \n", YELLOW + BOLD))
            input("Press Enter to play again...")
            board, game_state, current_player, selected_squares,valid_moves, last_move = reset_game()
            continue

        try:
            raw = input(" > ")
        except (EOFError,KeyboardInterrupt):
            print("\n  Goodbye...")
            sys.exit(0)

        parsed= parse_player_input(raw)

        if parsed[0] == "command":
            cmd = parsed[1]

            if cmd == "q":
                print("  GoodBye...")
                sys.exit(0)
            
            if cmd == "r":
                board, game_state, current_player, selected_squares,valid_moves, last_move = reset_game()
                move_history = []
                continue

            if cmd == "u":
                if move_history:
                    board, game_state,current_player, last_move = move_history.pop()
                    selected_squares = None
                    valid_moves = []
                else:
                    status_message = "Nothing to undo"
                continue

        elif parsed[0] == "move":
            from_square, to_square = parsed[1],parsed[2]
            from_row, from_col = from_square
            to_row, to_col = to_square

            piece_on_from = board[from_row][from_col]

            if not piece_on_from:
                status_message = f"No piece on {raw[:2].lower()}."
                continue
            if piece_on_from[1] != current_player:
                status_message = f"That's {piece_on_from[1]}'s piece, it's {current_player}'s turn."
                continue

            legal = legal_moves(board,from_row,from_col,game_state)
            if (to_row,to_col) not in legal:
                status_message = "Illegal move!!!!"
                continue

            move_history.append((
                copy.deepcopy(board),copy.deepcopy(game_state),current_player,last_move
            ))

            board, game_state, current_player, selected_squares, valid_moves, last_move = \
                commit_move(board,game_state,current_player,from_row,from_col,to_row,to_col)
            
        elif parsed[0] == "square":
            target_square = parsed[1]
            target_row, target_col = target_square
            piece_on_target = board[target_row][target_col]

            if selected_squares is None:
                if not piece_on_target:
                    status_message = "No piece there, pick one of your piece."
                elif piece_on_target[1] != current_player:
                    status_message = f"That's {piece_on_target[1]}'s piece, it's {current_player}'s turn."
                else:
                    legal = legal_moves(board,target_row,target_col,game_state)
                    if not legal:
                        status_message = "That piece has no legal moves."
                    else:
                        selected_squares = target_square
                        valid_moves = legal

            else:

                selected_row, selected_col = selected_squares
                if (target_row,target_col) == selected_squares:
                    selected_squares = None
                    valid_moves = []

                elif (target_row,target_col) in valid_moves:
                    move_history.append((
                        copy.deepcopy(board),copy.deepcopy(game_state),current_player,last_move
                    ))
                    board,game_state,current_player,selected_squares, valid_moves,last_move = \
                        commit_move(board,game_state,current_player,selected_row,selected_col,target_row,target_col)
                    
                elif piece_on_target and piece_on_target[1] == current_player:
                    legal = legal_moves(board,target_row,target_col,game_state)
                    if legal:
                        selected_squares = target_square
                        valid_moves = legal
                    else:
                        status_message = "That piece has no legal moves bro..." 
                else:
                    status_message = "That ain't a legal place"

        else:
            status_message = (
                f"unknown input '{parsed[1]}'. "
                f"Try: e2  or  e2e4  or  u/r/q"
            )


if __name__ == "__main__":
    print("""
+---------------------------------------+
|        TERMINAL CHESS                 |
|         by hyles :)                   |
+---------------------------------------+

Guide:
    e2      select the piece on e2 (valid moves appear as *)
    e4      move your selected piece to e4
    e2e4    move from e2 to e4 in one command
    u       undo last move
    r       restart the game
    q       quit

    uppercase = White pieces   lowercase = Black pieces
    [K]  = selected piece      *  = valid destination
    ~R~  = last move square    !k! = king in check
""")
    input("  Press Enter to start... ")
    run_game()
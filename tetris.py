"""
Created on Tue May 21 20:46:49 2019

@author: sean
"""
from tkinter import *
import random
import winsound
from PIL import Image, ImageTk
import pygame

class AnimatedGIF(Label, object):
    def __init__(self, master, path_to_gif):
        self._master = master
        self._loc = 0

        im = Image.open(path_to_gif)
        self._frames = []
        i = 0
        try:
            while True:
                temp = im.copy()
                self._frames.append(ImageTk.PhotoImage(temp.convert('RGBA')))

                i += 1
                im.seek(i)
        except EOFError: pass

        self._len = len(self._frames)

        try:
            self._delay = im.info['duration']
        except:
            self._delay = 100

        self._callback_id = None

        super(AnimatedGIF, self).__init__(master, image=self._frames[0])
        super(AnimatedGIF, self).config(bg="white")

    def _run(self):
        try:
            self._loc += 1
            if self._loc == self._len:
                self._loc = 0
    
            self.configure(image=self._frames[self._loc])
            self._callback_id = self._master.after(self._delay, self._run)
        except:
            pass

    def pack(self, *args, **kwargs):
        self._run()
        super(AnimatedGIF, self).pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self._run()
        super(AnimatedGIF, self).grid(*args, **kwargs)

    def place(self, *args, **kwargs):
        self._run()
        super(AnimatedGIF, self).place(*args, **kwargs)
class Shape():
    def __init__(self, coords = None):
        if not coords:
            self.__coords = random.choice(Tetris.SHAPES)
        else:
            self.__coords = coords

    @property
    def coords(self):
        return self.__coords

    def rotate(self):  
        self.__coords = self.__rotate()

    def rotate_directions(self):
        rotated = self.__rotate()
        directions = [(rotated[i][0] - self.__coords[i][0],
                       rotated[i][1] - self.__coords[i][1]) for i in range(len(self.__coords))]

        return directions

    @property
    def matrix(self):
        return [[1 if (j, i) in self.__coords else 0 \
                 for j in range(max(self.__coords, key=lambda x: x[0])[0] + 1)] \
                 for i in range(max(self.__coords, key=lambda x: x[1])[1] + 1)]

    def drop(self, board, offset):
        off_x, off_y = offset
        last_level = len(board) - len(self.matrix) + 1
        for level in range(off_y, last_level):
            for i in range(len(self.matrix)):
                for j in range(len(self.matrix[0])):
                    if board[level+i][off_x+j] == 1 and self.matrix[i][j] == 1:
                        return level - 1
        return last_level - 1  

    def __rotate(self):
        max_x = max(self.__coords, key=lambda x:x[0])[0]
        new_original = (max_x, 0)

        rotated = [(new_original[0] - coord[1],
                    new_original[1] + coord[0]) for coord in self.__coords]

        min_x = min(rotated, key=lambda x:x[0])[0]
        min_y = min(rotated, key=lambda x:x[1])[1]
        return [(coord[0] - min_x, coord[1] - min_y) for coord in rotated]

class Piece():
    def __init__(self, canvas, start_point, shape = None, color="gray"):
        self.color = color
        self.__shape = shape
        if not shape:
            self.__shape = Shape()
        self.canvas = canvas
        self.boxes = self.__create_boxes(start_point)

    @property
    def shape(self):
        return self.__shape

    def move(self, direction):
        if all(self.__can_move(self.canvas.coords(box), direction) for box in self.boxes):
            x, y = direction
            for box in self.boxes:
                self.canvas.move(box,
                                 x * Tetris.BOX_SIZE,
                                 y * Tetris.BOX_SIZE)
            return True
        return False

    def rotate(self):
        directions = self.__shape.rotate_directions()
        if all(self.__can_move(self.canvas.coords(self.boxes[i]), directions[i]) for i in range(len(self.boxes))):
            self.__shape.rotate()
            for i in range(len(self.boxes)):
                x, y = directions[i]
                self.canvas.move(self.boxes[i],
                                 x * Tetris.BOX_SIZE,
                                 y * Tetris.BOX_SIZE)

    @property
    def offset(self):
        return (min(int(self.canvas.coords(box)[0]) // Tetris.BOX_SIZE for box in self.boxes),
                min(int(self.canvas.coords(box)[1]) // Tetris.BOX_SIZE for box in self.boxes))

    def predict_movement(self, board):                                         #下拉到底用的著
        level = self.__shape.drop(board, self.offset)
        min_y = min([self.canvas.coords(box)[1] for box in self.boxes])
        return (0, level - (min_y // Tetris.BOX_SIZE))

    def predict_drop(self, board):
        level = self.__shape.drop(board, self.offset)
        self.remove_predicts()

        min_y = min([self.canvas.coords(box)[1] for box in self.boxes])
        for box in self.boxes:
            x1, y1, x2, y2 = self.canvas.coords(box)
            box = self.canvas.create_rectangle(x1,
                                               level * Tetris.BOX_SIZE + (y1 - min_y),
                                               x2,
                                               (level + 1) * Tetris.BOX_SIZE + (y1 - min_y),
                                               fill="yellow",
                                               tags = "predict")
            
    def remove_predicts(self):
        for i in self.canvas.find_withtag('predict'):
            self.canvas.delete(i) 
        self.canvas.update()

    def __create_boxes(self, start_point):
        boxes = []
        off_x, off_y = start_point
        for coord in self.__shape.coords:
            x, y = coord
            box = self.canvas.create_rectangle(x * Tetris.BOX_SIZE + off_x,
                                               y * Tetris.BOX_SIZE + off_y,
                                               x * Tetris.BOX_SIZE + Tetris.BOX_SIZE + off_x,
                                               y * Tetris.BOX_SIZE + Tetris.BOX_SIZE + off_y,
                                               fill=self.color,
                                               tags="game")
            boxes += [box]
        return boxes

    def __can_move(self, box_coords, new_pos):
        x, y = new_pos
        x = x * Tetris.BOX_SIZE
        y = y * Tetris.BOX_SIZE
        x_left, y_up, x_right, y_down = box_coords

        overlap = set(self.canvas.find_overlapping((x_left + x_right) / 2 + x, 
                                                   (y_up + y_down) / 2 + y, 
                                                   (x_left + x_right) / 2 + x,
                                                   (y_up + y_down) / 2 + y))
        other_items = set(self.canvas.find_withtag('game')) - set(self.boxes)

        if y_down + y > Tetris.GAME_HEIGHT or \
           x_left + x < 0 or \
           x_right + x > Tetris.GAME_WIDTH or \
           overlap & other_items:
           return False
        return True

class GameCanvas(Canvas):
    def clean_line(self, boxes_to_delete):
        for box in boxes_to_delete:
            self.delete(box)
        self.update()                                                          #如何更新?

    def drop_boxes(self, boxes_to_drop):
        for box in boxes_to_drop:
            self.move(box, 0, Tetris.BOX_SIZE)
    def barrier(self,plus):
        ran=random.randrange(int(Tetris.GAME_WIDTH/Tetris.BOX_SIZE-1))
        for i in range(plus):
            for a in range(int(Tetris.GAME_WIDTH/Tetris.BOX_SIZE-1)):
                if a!=ran:
                    self.create_rectangle(a*20+10,Tetris.GAME_HEIGHT-20*(i+1),a*20+30,Tetris.GAME_HEIGHT-20*i,fill="blue",tag="game")
    def barrier2(self,plus):
        ran=random.randrange(int(Tetris.GAME_WIDTH/Tetris.BOX_SIZE-1))
        for i in range(plus):
            for a in range(int(Tetris.GAME_WIDTH/Tetris.BOX_SIZE-1)):
                if a!=ran:
                    self.create_rectangle(a*20+10,Tetris.GAME_HEIGHT-20*(i+1),a*20+30,Tetris.GAME_HEIGHT-20*i,fill="red",tag="game")
    def rise_boxes(self,plus):
        for box in self.find_withtag('game'):
            self.move(box, 0,-20*plus) #-Tetris.BOX_SIZE
        self.barrier(plus)
        self.update()
    def rise_boxes2(self,plus):
        for box in self.find_withtag('game'):
            self.move(box, 0,-20*plus) #-Tetris.BOX_SIZE
        self.barrier2(plus)
        self.update()

    def completed_lines(self, y_coords):
        cleaned_lines = 0
        y_coords = sorted(y_coords)
        for y in y_coords:
            if sum(1 for box in self.find_withtag('game') if self.coords(box)[3] == y) == \
               ((Tetris.GAME_WIDTH - 20) // Tetris.BOX_SIZE):
                self.clean_line([box
                                for box in self.find_withtag('game')
                                if self.coords(box)[3] == y])

                self.drop_boxes([box
                                 for box in self.find_withtag('game')
                                 if self.coords(box)[3] < y])
                cleaned_lines += 1
        return cleaned_lines

    def game_board(self):
        board = [[0] * ((Tetris.GAME_WIDTH - 20) // Tetris.BOX_SIZE)\
                 for _ in range(Tetris.GAME_HEIGHT // Tetris.BOX_SIZE)]
        for box in self.find_withtag('game'):
            x, y, _, _ = self.coords(box)
            board[int(y // Tetris.BOX_SIZE)][int(x // Tetris.BOX_SIZE)] = 1
        return board
    def boxes(self):
        return self.find_withtag('game') == self.find_withtag(fill="blue")
    
class Tetris():
    SHAPES = ([(0, 0), (1, 0), (0, 1), (1, 1)],     # Square
              [(0, 0), (1, 0), (2, 0), (3, 0)],     # Line
              [(2, 0), (0, 1), (1, 1), (2, 1)],     # Right L
              [(0, 0), (0, 1), (1, 1), (2, 1)],     # Left L
              [(0, 1), (1, 1), (1, 0), (2, 0)],     # Right Z
              [(0, 0), (1, 0), (1, 1), (2, 1)],     # Left Z
              [(1, 0), (0, 1), (1, 1), (2, 1)])     # T

    BOX_SIZE = 20
    GAME_WIDTH = 300
    GAME_HEIGHT = 500
    GAME_START_POINT = GAME_WIDTH / 2 / BOX_SIZE * BOX_SIZE - BOX_SIZE
    
    def __init__(self, root, predictable = True):
#        self._blockcount = 0
#        self._blockcount2 = 0
        self.speed = 500
        self.predictable = predictable

        self.root = root
        self.root.bind("<Key>", self.game_control)
        self.root.bind("<space>",self.playmusic)
        self.open=BooleanVar()
        self.fm1 = Frame(self.root)
        self.fm2 = Frame(self.root)
        
        self.__game_canvas()                                                   #建立遊戲canvas
        self.__next_piece_canvas()                                             #建立遊戲canvas
        self.have_been_over = False
        self.open.set(True)
    def playmusic(self,event):
        self.open.set(not(self.open.get()))
        if self.open.get():
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
    
    def __game_canvas(self):
        self.canvas = GameCanvas(self.fm1, 
                             width = Tetris.GAME_WIDTH, 
                             height = Tetris.GAME_HEIGHT)
        self.canvas.pack(padx=5 , pady=10, side=LEFT)
        self.canvas2 = GameCanvas(self.fm2, 
                             width = Tetris.GAME_WIDTH, 
                             height = Tetris.GAME_HEIGHT)
        self.canvas2.pack(padx=5 , pady=10, side="right")
    def __next_piece_canvas(self):
        self.next_canvas = Canvas(self.fm1,
                                 width = 100,
                                 height = 100)
        self.next_canvas.pack(padx=5 , pady=10)
        self.next_canvas2 = Canvas(self.fm2,
                                 width = 100,
                                 height = 100)
        self.next_canvas2.pack(padx=5 , pady=10)
        
        self.fm1.pack(side=LEFT)
        self.fm2.pack(side=RIGHT)
        
    def game_control(self, event):                                              #遊戲控制
        if self.can_control1:
            if event.char in ["a", "A"]:                                            #(放向鍵沒功用)
                self.current_piece.move((-1, 0))
                self.update_predict()
            elif event.char in ["d", "D"]:
                self.current_piece.move((1, 0))
                self.update_predict()
            elif event.char in ["s", "S"]:
                self.hard_drop()
                self.can_control1 = False
            elif event.char in ["w", "W"]:
                self.current_piece.rotate()
                self.update_predict()
        if self.can_control2:
            if event.char == "4":
                self.current_piece2.move((-1, 0))
                self.update_predict2()
            elif event.char == "6":
                self.current_piece2.move((1, 0))
                self.update_predict2()
            elif event.char == "5":
                self.hard_drop2()
                self.can_control2 = False
            elif event.char == "8":
                self.current_piece2.rotate()
                self.update_predict2()
    def new_game(self):
        self.blockcount = 0
        self.blockcount2 = 0
        self.speed = 500
        self.can_control1 = True
        self.can_control2 = True
        self.plus1=0
        self.plus2=0

        self.canvas.delete("all")
        self.canvas2.delete("all")
        self.next_canvas.delete("all")
        self.next_canvas2.delete("all")

        self.__draw_canvas_frame()
        self.__draw_next_canvas_frame()

        self.current_piece = Piece(self.canvas, (Tetris.GAME_START_POINT, 0), color="red")
        self.next_piece = Piece(self.next_canvas, (20,20), color="red")
        
        self.current_piece2 = Piece(self.canvas2, (Tetris.GAME_START_POINT, 0), color="blue")
        self.next_piece2 = Piece(self.next_canvas2, (20,20), color="blue")

        self.game_board = [[0] * ((Tetris.GAME_WIDTH - 20) // Tetris.BOX_SIZE)\
                           for _ in range(Tetris.GAME_HEIGHT // Tetris.BOX_SIZE)]
        self.game_board2 = [[0] * ((Tetris.GAME_WIDTH - 20) // Tetris.BOX_SIZE)\
                           for _ in range(Tetris.GAME_HEIGHT // Tetris.BOX_SIZE)]
        
    def start(self):
        pygame.mixer.init()
        pygame.mixer.music.load('bgm.mp3')
        pygame.mixer.music.play(-1)
        self.have_been_over = False
        self.new_game()
        self.root.after(self.speed, None)
        self.drop()
        self.drop2()    
    def update_piece(self):
#        if not self.next_piece:
#            self.next_piece = Piece(self.next_canvas, (20,20), color="red")                 #建立第一塊拼圖(大概ㄅ)   
        self.current_piece = Piece(self.canvas, (Tetris.GAME_START_POINT, 0), self.next_piece.shape, color="red")
        self.next_canvas.delete("all")#刷新畫面
        self.__draw_next_canvas_frame()#刷新畫面
        self.next_piece = Piece(self.next_canvas, (20,20), color="red")
        self.update_predict()
        
    def update_piece2(self):
#        if not self.next_piece2:
#            self.next_piece2 = Piece(self.next_canvas2, (20,20))    
        self.current_piece2 = Piece(self.canvas2, (Tetris.GAME_START_POINT, 0), self.next_piece2.shape, color="blue")
        self.next_canvas2.delete("all")
        self.__draw_next_canvas_frame()#刷新畫面
        self.next_piece2 = Piece(self.next_canvas2, (20,20), color="blue")
        self.update_predict2()
    def drop(self):
        if not self.current_piece.move((0,1)):
            self.plus1 += self.completed_lines()
            if self.plus2:
                self.canvas.rise_boxes(self.plus2)
                self.plus2 = 0
            self.game_board = self.canvas.game_board()
            if self.is_game_over():
                return
            else:
                self.can_control1 = True
#                self._blockcount += 1
            self.update_piece()
        self.update_predict()
        if not self.have_been_over:
            self.root.after(self.speed, self.drop)
    def drop2(self):
        if not self.current_piece2.move((0,1)):
            self.plus2 += self.completed_lines2()
            if self.plus1:
                self.canvas2.rise_boxes2(self.plus1)
                self.plus1 = 0
            self.game_board2 = self.canvas2.game_board()
            if self.is_game_over2():
                return
            else:
                self.can_control2 = True
#                self._blockcount2 += 1
            self.update_piece2()
        self.update_predict2()
        if not self.have_been_over:
            self.root.after(self.speed, self.drop2)
        
    def hard_drop(self):                                                       #下拉到底
        self.current_piece.move(self.current_piece.predict_movement(self.game_board))
        winsound.PlaySound('hit.wav', winsound.SND_ASYNC)
    def hard_drop2(self):                                                       #下拉到底
        self.current_piece2.move(self.current_piece2.predict_movement(self.game_board2))
        winsound.PlaySound('hit.wav', winsound.SND_ASYNC)
    def update_predict(self):
        if self.predictable:
            self.current_piece.predict_drop(self.game_board)
    def update_predict2(self):
        if self.predictable:
            self.current_piece2.predict_drop(self.game_board2)
        
    def is_game_over(self):
        for box in self.canvas.find_withtag('game'):
                if self.canvas.coords(box)[3] <= 40:
                    self.have_been_over = True
                    self.can_control1 = False
                    self.can_control2 = False
                    
                    self.current_piece.remove_predicts()
                    
                    self.play_again_btn = Button(self.root, text="Play Again", command=self.play_again)
                    self.quit_btn = Button(self.root, text="Quit", command=self.quit) 
                    self.play_again_btn.place(x = Tetris.GAME_WIDTH + 10, y = 200, width=100, height=25)
                    self.quit_btn.place(x = Tetris.GAME_WIDTH + 140, y = 200, width=100, height=25)
                    self.result_label = Label(self.root, text="Player2 win!!",
                                              font=("微軟正黑體",25,"bold"))
                    self.result_label.place(x = Tetris.GAME_WIDTH + 15,y = 250)
                    return True
        return False
    
    def is_game_over2(self):
        for box in self.canvas2.find_withtag('game'):
                if self.canvas2.coords(box)[3] <= 40:
                    self.have_been_over = True
                    self.can_control1 = False
                    self.can_control2 = False
                    
                    self.current_piece2.remove_predicts()
                    
                    self.play_again_btn = Button(self.root, text="Play Again", command=self.play_again)
                    self.quit_btn = Button(self.root, text="Quit", command=self.quit) 
                    self.play_again_btn.place(x = Tetris.GAME_WIDTH + 10, y = 200, width=100, height=25)
                    self.quit_btn.place(x = Tetris.GAME_WIDTH + 140, y = 200, width=100, height=25)
                    self.result_label = Label(self.root, text="Player1 win!!",
                                              font=("微軟正黑體",25,"bold"))
                    self.result_label.place(x = Tetris.GAME_WIDTH + 15,y = 250)
                    return True
        return False

    def play_again(self):
        self.play_again_btn.destroy()
        self.quit_btn.destroy()
        self.result_label.destroy()
        self.start()

    def quit(self):
        self.root.destroy()     

    def completed_lines(self):
        y_coords = [self.canvas.coords(box)[3] for box in self.current_piece.boxes]
        completed_line = self.canvas.completed_lines(y_coords)
        return completed_line
    def completed_lines2(self):
        y_coords2 = [self.canvas2.coords(box)[3] for box in self.current_piece2.boxes]
        completed_line2 = self.canvas2.completed_lines(y_coords2)
        return completed_line2

    def __draw_canvas_frame(self):
        self.canvas.create_line(10, 0, 10, self.GAME_HEIGHT, fill = "red", tags = "line")
        self.canvas.create_line(self.GAME_WIDTH-10, 0, self.GAME_WIDTH-10, self.GAME_HEIGHT, fill = "red", tags = "line")
        self.canvas.create_line(10, self.GAME_HEIGHT, self.GAME_WIDTH-10, self.GAME_HEIGHT, fill = "red", tags = "line")
        
        self.canvas.create_line(10, 0, self.GAME_WIDTH-10, 0, fill = "red", tags = "line")
        self.canvas.create_line(10, 40, self.GAME_WIDTH-10, 40, fill = "red", tags = "line")
        
        self.canvas2.create_line(10, 0, self.GAME_WIDTH-10, 0, fill = "blue", tags = "line")
        self.canvas2.create_line(10, 40, self.GAME_WIDTH-10, 40, fill = "blue", tags = "line")
        
        self.canvas2.create_line(10, 0, 10, self.GAME_HEIGHT, fill = "blue", tags = "line")
        self.canvas2.create_line(self.GAME_WIDTH-10, 0, self.GAME_WIDTH-10, self.GAME_HEIGHT, fill = "blue", tags = "line")
        self.canvas2.create_line(10, self.GAME_HEIGHT, self.GAME_WIDTH-10, self.GAME_HEIGHT, fill = "blue", tags = "line")

    def __draw_next_canvas_frame(self):
        self.next_canvas.create_rectangle(10, 10, 100, 100, tags="frame",outline="darkred") 
        self.next_canvas2.create_rectangle(10, 10, 100, 100, tags="frame",outline="darkblue") 
        
    def __get_blockcount(self):
        return self._blockcount
    
    def __set_blockcount(self, blockcount):
        self._blockcount = blockcount

    blockcount = property(__get_blockcount, __set_blockcount)
    
def scrolling():
    try:
        for label in labels:
            x = (int(label.place_info()['x'])-2) %860
            label.place(x=x,y=0)
        if not start_bool.get():
            root.after(15,scrolling)
    except:
        pass
def game_start():
    winsound.PlaySound('hit.wav', winsound.SND_ASYNC)
    start_bool.set(True)
    for widget in root.winfo_children():
        widget.destroy()
    game = Tetris(root)
    game.start()

if __name__ == '__main__':
    root = Tk()
    root.title('Shiroki_Tetris')
    root.iconbitmap('cube_head.ico')
    root.geometry("860x550")
    root.configure(bg = "white")
    
    l = AnimatedGIF(root, "photo.gif")
    l.pack(side=BOTTOM)
    
    start_bool = BooleanVar()
    start_bool.set(False)
    
    title = list("Tetris")
    labels = [Label(root,text=text,bg="white",font=("微軟正黑體",40)) for text in title]
    x = 550
    for label in labels:
        label.place(x=x,y=0)
        x = x+40
        
    Button(root,text="Game Start",width=20,command=game_start).place(x=710,y=500)
    Button(root,text="Exit",width=20,command=root.destroy).place(x=710,y=525)
    root.after(100,scrolling)
        
    root.mainloop()

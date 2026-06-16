import tkinter as tk
win=tk.Tk()
y=0

def sayHi():
    global y
    y +=1
    print(y)

win.geometry("200x100")
b=tk.Button(
        win,
        text='Click Me',
        command=sayHi
)
b.pack()
win.mainloop()

    
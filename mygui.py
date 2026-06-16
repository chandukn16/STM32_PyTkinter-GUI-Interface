import tkinter as tk

# Create the main window
win = tk.Tk()
win.title("My First GUI Application")
win.geometry("300x200")
win.configure(bg='#f0f0f0')

# Counter variable
y = 0

def sayHi():
    global y
    y += 1
    print(f"Button clicked {y} time(s)")
    
    # Update the label to show click count
    counter_label.config(text=f"Clicked: {y} times")
    
    # Update button text
    b.config(text=f"Click Me ({y})")

# Create a nice label
title_label = tk.Label(
    win,
    text="🎉 My First GUI App",
    font=("Arial", 16, "bold"),
    bg='#f0f0f0',
    fg='#333333'
)
title_label.pack(pady=20)

# Counter display
counter_label = tk.Label(
    win,
    text="Clicked: 0 times",
    font=("Arial", 12),
    bg='#f0f0f0',
    fg='#666666'
)
counter_label.pack(pady=10)

# Create a styled button
b = tk.Button(
    win,
    text='Click Me',
    command=sayHi,
    font=("Arial", 12, "bold"),
    bg='#4CAF50',
    fg='white',
    padx=20,
    pady=10,
    cursor='hand2'
)
b.pack(pady=20)

# Add exit button
exit_btn = tk.Button(
    win,
    text='Exit',
    command=win.destroy,
    font=("Arial", 10),
    bg='#f44336',
    fg='white',
    padx=15,
    pady=5,
    cursor='hand2'
)
exit_btn.pack(pady=10)

# This line is crucial - it keeps the window open
win.mainloop()
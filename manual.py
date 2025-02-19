import sqlite3
import tkinter as tk
from tkinter import Label, Button, Text, END, messagebox

# Function to set up the database
def setup_database():
    conn = sqlite3.connect("lidl_ocr_data.db")  # Create or connect to the Lidl database
    cursor = conn.cursor()

    # Create a table to store recognized data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lidl_ocr_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            weight TEXT,
            price_per_piece TEXT,
            barcode TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to save recognized data to the database
def save_to_database(product_name, weight, price_per_piece, barcode):
    conn = sqlite3.connect("lidl_ocr_data.db")
    cursor = conn.cursor()

    # Insert structured data into the table
    cursor.execute('INSERT INTO lidl_ocr_data (product_name, weight, price_per_piece, barcode) VALUES (?, ?, ?, ?)',
                   (product_name, weight, price_per_piece, barcode))
    conn.commit()
    conn.close()
    print("Data saved to database!")

# Function to manually input information
def manually_input_data():
    # Retrieve data from the user input
    product_name = product_name_entry.get()
    weight = weight_entry.get()
    price_per_piece = price_per_piece_entry.get()
    barcode = barcode_entry.get()

    # Display results in the text output area
    text_output.delete(1.0, END)
    text_output.insert(END, f"Product Name: {product_name}\n")
    text_output.insert(END, f"Weight: {weight}\n")
    text_output.insert(END, f"Price per Piece: {price_per_piece}\n")
    text_output.insert(END, f"Barcode: {barcode}\n")

    # Ask the user to confirm the data
    if messagebox.askyesno("Confirm Data", f"Is this correct?\n\n"
                                          f"Product Name: {product_name}\n"
                                          f"Weight: {weight}\n"
                                          f"Price per Piece: {price_per_piece}\n"
                                          f"Barcode: {barcode}"):

        save_to_database(product_name, weight, price_per_piece, barcode)
        messagebox.showinfo("Saved", "Data has been saved to the database.")
    else:
        messagebox.showinfo("Not Saved", "Data was not saved to the database.")

# Set up the database when the script starts
setup_database()

# Set up the GUI
root = tk.Tk()
root.title("Lidl Product Data Input")

# Add widgets to the GUI
product_name_label = Label(root, text="Product Name:")
product_name_label.pack(pady=5)
product_name_entry = tk.Entry(root, width=50)
product_name_entry.pack(pady=5)

weight_label = Label(root, text="Weight (e.g., 180g):")
weight_label.pack(pady=5)
weight_entry = tk.Entry(root, width=50)
weight_entry.pack(pady=5)

price_per_piece_label = Label(root, text="Price per Piece (e.g., 1.99 €):")
price_per_piece_label.pack(pady=5)
price_per_piece_entry = tk.Entry(root, width=50)
price_per_piece_entry.pack(pady=5)

barcode_label = Label(root, text="Barcode:")
barcode_label.pack(pady=5)
barcode_entry = tk.Entry(root, width=50)
barcode_entry.pack(pady=5)

# Display output text area
text_output = Text(root, height=10, width=50, wrap=tk.WORD, font=("Arial", 10))
text_output.pack(pady=10)

# Add buttons
input_button = Button(root, text="Input Data", command=manually_input_data, width=20, height=2)
input_button.pack(pady=10)

quit_button = Button(root, text="Quit", command=root.destroy, width=20, height=2)
quit_button.pack(pady=10)

# Start the GUI loop
root.mainloop()

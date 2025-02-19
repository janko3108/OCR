import cv2
import sqlite3
import tkinter as tk
from tkinter import Label, Button, Text, END, filedialog, messagebox
from easyocr import Reader
from pyzxing import BarCodeReader
import re

# Initialize EasyOCR reader
reader = Reader(['en'])

# Initialize the ZXing barcode reader
barcode_reader = BarCodeReader()

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

# Function to trim and clean barcode data
def clean_barcode(barcode):
    if barcode:
        # Decode byte string to normal string, then strip non-numeric characters
        barcode = barcode.decode("utf-8") if isinstance(barcode, bytes) else barcode
        return re.sub(r'[^0-9]', '', barcode)  # Keep only numeric characters
    return None

# Function to parse OCR output into structured data

def parse_lidl_ocr_output(ocr_text):
    """
    Parse the OCR output to extract product details for Lidl labels.
    """
    # Split OCR text into lines and clean
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    print("Cleaned OCR Lines:", lines)  # Debugging

    # Merge lines into a single text for easier regex parsing
    cleaned_text = " ".join(lines)
    print("Merged Cleaned Text:", cleaned_text)  # Debugging

    # Extract product name (combine consecutive lines until encountering numeric data)
    product_name_parts = []
    for line in lines:
        if re.search(r'\d+g', line, re.IGNORECASE) or re.search(r'€', line) or re.search(r'\d+', line):
            break
        product_name_parts.append(line)
    product_name = " ".join(product_name_parts) if product_name_parts else "Unknown Product"

    # Extract weight (e.g., "180g")
    weight = next((line for line in lines if re.search(r'\d+\s?g', line, re.IGNORECASE)), "Unknown Weight")

    # Extract price per piece (large number followed by "€")
    price_per_piece_match = re.search(r'(\d+[.,]\d+)\s*€', cleaned_text)
    price_per_piece = price_per_piece_match.group(1).replace(',', '.') + " €" if price_per_piece_match else "Unknown Price per Piece"

    # Debugging: Log parsed data
    print("Parsed Data:")
    print("Product Name:", product_name)
    print("Weight:", weight)
    print("Price per Piece:", price_per_piece)

    return product_name, weight, price_per_piece


# Function to handle barcode scanning
def scan_barcode(image_path):
    """
    Scan the barcode from the image using ZXing.
    """
    result = barcode_reader.decode(image_path)
    if result and 'parsed' in result[0]:
        barcode = clean_barcode(result[0]['parsed'])
        print("Detected Barcode:", barcode)
        return barcode
    return "Unknown Barcode"

# Function to handle image upload and processing
def upload_and_process_lidl_image():
    file_path = filedialog.askopenfilename(
        title="Select a Lidl Image",
        filetypes=(("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*"))
    )
    if not file_path:
        return  # No file selected

    try:
        # Load image and perform OCR
        image = cv2.imread(file_path)
        results = reader.readtext(image)
        ocr_text = "\n".join([result[1] for result in results])
        print("Complete OCR Text:\n", ocr_text)

        # Parse OCR output
        product_name, weight, price_per_piece = parse_lidl_ocr_output(ocr_text)

        # Scan barcode
        barcode = scan_barcode(file_path)

        # Display results
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

    except Exception as e:
        messagebox.showerror("Error", f"Failed to process the image.\nError: {e}")

# Set up the database when the script starts
setup_database()

# Set up the GUI
root = tk.Tk()
root.title("Lidl Product OCR Scanner")

# Add widgets to the GUI
text_output = Text(root, height=10, width=50, wrap=tk.WORD, font=("Arial", 10))
text_output.pack(pady=10)

upload_button = Button(root, text="Upload Lidl Image", command=upload_and_process_lidl_image, width=20, height=2)
upload_button.pack(pady=10)

quit_button = Button(root, text="Quit", command=root.destroy, width=20, height=2)
quit_button.pack(pady=10)

# Start the GUI loop
root.mainloop()

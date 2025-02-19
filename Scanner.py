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
zxing_reader = BarCodeReader()

# Function to set up the database
def setup_database():
    conn = sqlite3.connect("ocr_data.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            product_name TEXT,
            weight TEXT,
            price_per_piece TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to save recognized data to the database
def save_to_database(barcode, product_name, weight, price_per_piece):
    conn = sqlite3.connect("ocr_data.db")
    cursor = conn.cursor()

    cursor.execute('INSERT INTO ocr_data (barcode, product_name, weight, price_per_piece) VALUES (?, ?, ?, ?)',
                   (barcode, product_name, weight, price_per_piece))
    conn.commit()
    conn.close()
    print("Data saved to database!")

# Function to adjust improperly formatted prices
def adjust_price(price):
    """
    Adjust prices without decimal points by inserting a decimal point
    before the last two digits (e.g., 427 -> 4.27).
    """
    if price.isdigit() and len(price) > 2:  # If it's a number and has more than 2 digits
        adjusted_price = f"{price[:-2]}.{price[-2:]}"  # Insert a decimal point
        return adjusted_price
    return price  # Return as-is if already formatted

# Function to parse OCR output into structured data
def parse_ocr_output(ocr_text):
    """
    Parse the OCR output to extract product details (name, weight, price per piece).
    """
    # Split OCR text into lines and clean
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    print("Cleaned OCR Lines:", lines)

    # Merge lines into a single text for easier regex parsing
    cleaned_text = " ".join(lines).replace("€lkom", "€/kom")
    print("Merged Cleaned Text:", cleaned_text)

    # Extract product name (first meaningful line with mostly alphabetic characters)
    product_name = next((line for line in lines if re.match(r'^[A-Za-z\s]+$', line)), "Unknown Product")

    # Extract weight (e.g., "300g")
    weight = next((line for line in lines if re.search(r'\d+\s?g', line, re.IGNORECASE)), "Unknown Weight")

    # Extract price per piece (e.g., "4.27 €/kom")
    price_per_piece = "Unknown Price"
    price_match = re.search(r'\b(\d{3,})\b\s?€/kom', cleaned_text)  # Match numbers with 3+ digits before €/kom
    if price_match:
        raw_price = price_match.group(1)
        adjusted_price = adjust_price(raw_price)  # Adjust price dynamically
        price_per_piece = f"{adjusted_price} €/kom"

    # Debugging: Log parsed data
    print("Parsed Data:")
    print("Product Name:", product_name)
    print("Weight:", weight)
    print("Price per Piece:", price_per_piece)

    return product_name, weight, price_per_piece

# Function to scan barcode using ZXing
# Function to clean and trim barcode to numeric values only
def clean_barcode(barcode):
    if barcode:
        # Decode if it's a byte string, then keep only numeric characters
        barcode = barcode.decode("utf-8") if isinstance(barcode, bytes) else barcode
        return re.sub(r'\D', '', barcode)  # Remove all non-numeric characters
    return "Unknown Barcode"

# Updated barcode scanning function
def scan_barcode(image_path):
    result = zxing_reader.decode(image_path)
    if result and 'parsed' in result[0]:
        raw_barcode = result[0]['parsed']
        cleaned_barcode = clean_barcode(raw_barcode)
        print("Detected Barcode:", cleaned_barcode)
        return cleaned_barcode
    return "Unknown Barcode"


# Function to handle image upload and processing
def upload_and_process_image():
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=(("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*"))
    )
    if not file_path:
        return  # No file selected

    try:
        # Scan barcode
        barcode = scan_barcode(file_path)

        # Load image and perform OCR
        image = cv2.imread(file_path)
        results = reader.readtext(image)
        ocr_text = "\n".join([result[1] for result in results])
        print("Complete OCR Text:\n", ocr_text)

        # Parse OCR output
        product_name, weight, price_per_piece = parse_ocr_output(ocr_text)

        # Display results
        text_output.delete(1.0, END)
        text_output.insert(END, f"Barcode: {barcode}\n")
        text_output.insert(END, f"Product Name: {product_name}\n")
        text_output.insert(END, f"Weight: {weight}\n")
        text_output.insert(END, f"Price per Piece: {price_per_piece}\n")

        # Ask the user to confirm the data
        if messagebox.askyesno("Confirm Data", f"Is this correct?\n\n"
                                              f"Barcode: {barcode}\n"
                                              f"Product Name: {product_name}\n"
                                              f"Weight: {weight}\n"
                                              f"Price per Piece: {price_per_piece}"):

            save_to_database(barcode, product_name, weight, price_per_piece)
            messagebox.showinfo("Saved", "Data has been saved to the database.")
        else:
            messagebox.showinfo("Not Saved", "Data was not saved to the database.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to process the image.\nError: {e}")

# Set up the database when the script starts
setup_database()

# Set up the GUI
root = tk.Tk()
root.title("Product OCR Scanner with Barcode")

# Add widgets to the GUI
text_output = Text(root, height=10, width=50, wrap=tk.WORD, font=("Arial", 10))
text_output.pack(pady=10)

upload_button = Button(root, text="Upload Image", command=upload_and_process_image, width=20, height=2)
upload_button.pack(pady=10)

quit_button = Button(root, text="Quit", command=root.destroy, width=20, height=2)
quit_button.pack(pady=10)

# Start the GUI loop
root.mainloop()

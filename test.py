pdf_path = "/Users/sourabh/Desktop/file_handler/Hiper Automotive Assignment (5).pdf"

with open(pdf_path, "rb") as f:
    content = f.read()
    size = len(content)
    chksum = sum(content) % 256

print("File Size:", size)
print("start_byte =", 0)
print("end_byte =", size - 1)
print("checksum =", chksum)

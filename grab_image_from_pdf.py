
"""
This is a function to grab an image from a pdf, based on this:
https://nedbatchelder.com/blog/200712/extracting_jpgs_from_pdfs.html
"""
import os


def extract_image(pdf_bytes):
    """Searches pdf bytes for the image start and end marks, returns bytes
    """
    start_mark = b"\xff\xd8"
    end_mark = b"\xff\xd9"
    byte_end_fix = 2

    assert(type(pdf_bytes) == bytes)
    
    start_byte = pdf_bytes.find(start_mark)
    if start_byte < 0:
        return None
    end_byte = pdf_bytes.find(end_mark)
    end_byte += byte_end_fix
    jpg_bytes = pdf_bytes[start_byte:end_byte]
    return jpg_bytes

def process_folder(input_folder, output_folder):
    
    files = os.listdir(input_folder)
    pdfs = [file for file in files if file.endswith(".pdf")]
    
    for pdf in pdfs:
        jpg_filepath = os.path.join(output_folder, pdf[:-4] + ".jpg")
        pdf_filepath = os.path.join(input_folder, pdf)
        with open(pdf_filepath, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        jpg_bytes = extract_image(pdf_bytes)
        if jpg_bytes is not None:
            with open(jpg_filepath, "wb") as jpg_file:
                jpg_file.write(jpg_bytes)
    return



if __name__ == "__main__":
    process_folder(input_folder="./pdfs", output_folder="./jpgs")
    


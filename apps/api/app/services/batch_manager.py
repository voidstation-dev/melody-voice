import csv
import io
import os


def parse_batch_file(filename: str, content: bytes) -> list[str]:
    """
    Parses an uploaded batch file (.txt or .csv) and returns a list of text strings.
    For .txt: splits by newline, ignoring empty lines.
    For .csv: looks for a 'text' column, or uses the first column if no header.
    """
    ext = os.path.splitext(filename)[1].lower()
    items = []
    
    text_str = content.decode("utf-8-sig", errors="replace")
    
    if ext == ".csv":
        reader = csv.reader(io.StringIO(text_str))
        rows = list(reader)
        if not rows:
            return []
            
        header = [h.strip().lower() for h in rows[0]]
        if "text" in header:
            text_index = header.index("text")
            for row in rows[1:]:
                if len(row) > text_index:
                    val = row[text_index].strip()
                    if val:
                        items.append(val)
        else:
            # Assume first column is text
            for row in rows:
                if row:
                    val = row[0].strip()
                    if val:
                        items.append(val)
    else:
        # Default to txt (newline separated)
        for line in text_str.splitlines():
            val = line.strip()
            if val:
                items.append(val)
                
    return items

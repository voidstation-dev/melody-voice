import re


def split_text_into_chunks(text: str, max_chars: int = 450) -> list[str]:
    """
    Splits a long text into chunks of maximum max_chars characters.
    Attempts to split by sentence boundaries (., !, ?) first.
    If a sentence is longer than max_chars, it splits by words (spaces).
    If a word is longer than max_chars, it hard-splits.
    """
    text = text.strip()
    if not text:
        return []

    # Replace newlines with spaces for TTS purposes, or keep them if preferred?
    # Keeping newlines might be better, but CapCut usually ignores them.
    text = re.sub(r"\s+", " ", text)

    chunks = []

    # Simple regex to split by sentence endings while keeping the delimiter
    # This splits on (. | ! | ?) followed by space
    sentences = re.split(r"(?<=[.!?])\s+", text)

    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if (
            len(current_chunk) + len(sentence) + (1 if current_chunk else 0)
            <= max_chars
        ):
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            # Current chunk is full, push it
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # If the sentence itself is larger than max_chars, we must split it by words
            if len(sentence) > max_chars:
                words = sentence.split(" ")
                for word in words:
                    if (
                        len(current_chunk) + len(word) + (1 if current_chunk else 0)
                        <= max_chars
                    ):
                        if current_chunk:
                            current_chunk += " " + word
                        else:
                            current_chunk = word
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)

                        # Hard split word if it's monstrously long
                        if len(word) > max_chars:
                            sub_chunks = [
                                word[i : i + max_chars]
                                for i in range(0, len(word), max_chars)
                            ]
                            for sc in sub_chunks[:-1]:
                                chunks.append(sc)
                            current_chunk = sub_chunks[-1]
                        else:
                            current_chunk = word
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def slugify_vietnamese(text: str) -> str:
    if not text:
        return "capvoice-audio"

    # Take first sentence or first 60 chars
    text = text.split("\n")[0].strip()
    sentences = re.split(r"[.!?]", text)
    first_sentence = sentences[0].strip() if sentences else text
    if len(first_sentence) > 60:
        first_sentence = first_sentence[:60].rsplit(" ", 1)[0]

    text = first_sentence.lower()
    text = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", text)
    text = re.sub(r"[èéẹẻẽêềếệểễ]", "e", text)
    text = re.sub(r"[ìíịỉĩ]", "i", text)
    text = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", text)
    text = re.sub(r"[ùúụủũưừứựửữ]", "u", text)
    text = re.sub(r"[ỳýỵỷỹ]", "y", text)
    text = re.sub(r"[đ]", "d", text)

    # Replace non-alphanumeric with dash
    text = re.sub(r"[^a-z0-9]+", "-", text)
    slug = text.strip("-")

    return slug or "capvoice-audio"

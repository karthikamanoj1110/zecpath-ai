import re

def rebuild_text_for_nlp(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    sentences = []
    buffer = []

    for line in lines:

        # skip visual separators
        if re.fullmatch(r"[_\-]{5,}", line):
            if buffer:
                sentences.append(" ".join(buffer))
                buffer = []
            continue

        # remove isolated pipes
        if line == "|":
            continue

        buffer.append(line)

        # flush if line ends a logical phrase
        if line.endswith((".", ":", ")", ",")):
            sentences.append(" ".join(buffer))
            buffer = []

    if buffer:
        sentences.append(" ".join(buffer))

    text = " ".join(sentences)

    # cleanup spaces before punctuation
    text = re.sub(r"\s+([,.:;)])", r"\1", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

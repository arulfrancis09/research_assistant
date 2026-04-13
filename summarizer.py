from __future__ import annotations

import re
from collections import Counter
from typing import List


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in", "is", "it",
    "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "this", "these",
    "those", "their", "there", "which", "about", "into", "than", "also", "can", "may", "more", "most",
}


def _sentence_split(text: str) -> List[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    cleaned = [c.strip() for c in chunks if len(c.strip()) > 25]
    if cleaned:
        return cleaned

    line_chunks = [line.strip() for line in text.splitlines()]
    return [line for line in line_chunks if len(line) > 25]


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def summarize_text(text: str, topic: str, max_sentences: int = 5) -> str:
    sentences = _sentence_split(text)
    if not sentences:
        return ""

    topic_tokens = set(_tokenize(topic))
    all_tokens = _tokenize(text)
    token_freq = Counter(all_tokens)

    def sentence_score(sentence: str) -> float:
        tokens = _tokenize(sentence)
        if not tokens:
            return 0.0
        base = sum(token_freq[t] for t in tokens) / max(len(tokens), 1)
        topic_boost = sum(2.0 for t in tokens if t in topic_tokens)
        length_penalty = 0.0 if 12 <= len(tokens) <= 45 else 0.3
        return base + topic_boost - length_penalty

    ranked = sorted(sentences, key=sentence_score, reverse=True)
    selected = ranked[:max_sentences]
    selected_in_order = [s for s in sentences if s in set(selected)]
    return " ".join(selected_in_order)


def summarize_documents(doc_summaries: List[str], topic: str, limit: int = 8) -> List[str]:
    bullets: List[str] = []
    seen = set()
    for summary in doc_summaries:
        for sentence in _sentence_split(summary):
            norm = re.sub(r"\W+", "", sentence.lower())
            if norm and norm not in seen:
                bullets.append(sentence)
                seen.add(norm)
            if len(bullets) >= limit:
                return bullets
    return bullets

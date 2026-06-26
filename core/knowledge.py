import logging
from typing import List, Dict
from rank_bm25 import BM25Okapi

from data.knowledge_base import CHUNKS

log = logging.getLogger(__name__)

_bm25 = None
_tokenized_corpus = None


def _build_index():
    global _bm25, _tokenized_corpus
    _tokenized_corpus = [
        (chunk["title"] + " " + " ".join(chunk.get("keywords", [])) + " " + chunk["text"])
        .lower()
        .split()
        for chunk in CHUNKS
    ]
    _bm25 = BM25Okapi(_tokenized_corpus)
    log.info("BM25 index built: %d chunks", len(CHUNKS))


def search(query: str, top_k: int = 4) -> List[Dict]:
    global _bm25
    if _bm25 is None:
        _build_index()

    tokens = query.lower().split()
    scores = _bm25.get_scores(tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [CHUNKS[i] for i in top_indices if scores[i] > 0]


def build_context(query: str) -> str:
    chunks = search(query)
    if not chunks:
        return ""
    parts = []
    for chunk in chunks:
        parts.append(f"=== {chunk['title']} ===\n{chunk['text']}")
    return "\n\n".join(parts)


SYSTEM_PROMPT = """Ты HR-помощник компании INNORTO. Отвечаешь на вопросы сотрудников строго по базе знаний компании.

Правила:
1. Отвечай только на основе предоставленного контекста — не придумывай данные.
2. Если вопрос о конкретном человеке или отделе — дай ФИО, должность, телефон, email и краткие обязанности.
3. Если данных нет — честно скажи: «В базе знаний нет информации по этому вопросу. Обратись в отдел заботы: zabotainnorto@gmail.com».
4. Форматируй ответ в HTML для Telegram:
   - <b>жирный</b> для имён, заголовков, ключевых фактов
   - <i>курсив</i> для должностей и дополнительных пояснений
   - • для списков (обычный символ, не HTML)
   - Эмодзи: 👤 перед именем, 📞 перед телефоном, ✉️ перед email, 🏷 перед должностью
5. Структура ответа на вопрос о сотруднике:
   👤 <b>Имя Фамилия</b>
   🏷 <i>Должность / Отдел</i>
   📞 телефон
   ✉️ email

   <b>Отвечает за:</b>
   • ...
6. Заверши ответ разделителем и примечанием:
   ━━━━━━━━━━━━━━━━━━━━
   <i>💡 Ответ сформирован на основе корпоративной базы знаний</i>
"""

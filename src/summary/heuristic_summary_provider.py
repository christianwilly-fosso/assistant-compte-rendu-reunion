"""Heuristic French summary provider — no API needed."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from src.reports.report_model import ActionItem, MeetingReport, UNSPECIFIED
from src.summary.summary_provider import SummaryProvider

_SENTENCE_BOUNDARY = re.compile(r"(?<=[\.!?…])\s+(?=[A-ZÉÈÀÂÎÔÙÇ0-9«\"])")
_TOKEN_PATTERN = re.compile(r"[a-zàâäéèêëîïôöùûüç]+", re.IGNORECASE)

_DECISION_PATTERNS = (
    r"\b(?:on a décidé|nous avons décidé|décision\s*:|il a été décidé|on retient|on garde|on choisit|on opte|on valide|on confirme|on tranche|nous validons|nous confirmons)\b",
)

_ACTION_PATTERNS = (
    r"\bil faut\b",
    r"\bon doit\b",
    r"\bnous devons\b",
    r"\bà faire\b",
    r"\bsera responsable\b",
    r"\bse charge de\b",
    r"\bse chargera de\b",
    r"\bd['’]ici\b",
    r"\bavant le\b",
    r"\bprochaine étape\b",
    r"\bje vais\b",
    r"\btu vas\b",
    r"\bdoit\s+(?:envoyer|préparer|écrire|contacter|appeler|valider|finaliser|relancer|tester)\b",
)

_PENDING_PATTERNS = (
    r"\bà discuter\b",
    r"\bà voir\b",
    r"\bà étudier\b",
    r"\ben suspens\b",
    r"\bà clarifier\b",
    r"\bplus tard\b",
    r"\bon reverra\b",
    r"\bon en reparlera\b",
    r"\bquestion ouverte\b",
)

_RESPONSIBLE_HINTS = re.compile(
    r"\b(?:par|pour)\s+([A-ZÉÈÀÂ][a-zàâäéèêëîïôöùûüç]+)\b"
)
_DUE_DATE_HINTS = re.compile(
    r"\b(?:d['’]ici|avant le|pour le|au plus tard le)\s+([^,.;]+)",
    re.IGNORECASE,
)

_FRENCH_STOPWORDS = frozenset({
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "à", "au", "aux",
    "en", "dans", "pour", "par", "sur", "avec", "sans", "que", "qui", "quoi", "dont",
    "où", "ce", "cet", "cette", "ces", "il", "elle", "ils", "elles", "on", "nous",
    "vous", "je", "tu", "moi", "toi", "se", "sa", "son", "ses", "leur", "leurs",
    "mon", "ma", "mes", "ton", "ta", "tes", "notre", "votre", "nos", "vos",
    "est", "sont", "était", "été", "être", "avoir", "a", "ai", "as", "ont",
    "pas", "ne", "ni", "plus", "moins", "très", "trop", "peu", "tout", "tous",
    "alors", "donc", "puis", "ensuite", "aussi", "comme", "mais", "car",
    "ça", "cela", "ceci", "celui", "celle", "ceux", "celles", "y", "lui",
    "déjà", "encore", "bien", "quand", "comment", "pourquoi", "si",
})

_SUMMARY_MAX_SENTENCES = 5
_DISCUSSED_MAX_SENTENCES = 8


@dataclass(frozen=True)
class _ScoredSentence:
    text: str
    score: float
    index: int


class HeuristicSummaryProvider(SummaryProvider):
    """Build a meeting report using simple French heuristics.

    The goal is not to rival an LLM but to give a useful, free baseline
    that runs offline.
    """

    def __init__(
        self,
        summary_max_sentences: int = _SUMMARY_MAX_SENTENCES,
        discussed_max_sentences: int = _DISCUSSED_MAX_SENTENCES,
    ) -> None:
        self._summary_max_sentences = summary_max_sentences
        self._discussed_max_sentences = discussed_max_sentences
        self._decision_re = _compile_any(_DECISION_PATTERNS)
        self._action_re = _compile_any(_ACTION_PATTERNS)
        self._pending_re = _compile_any(_PENDING_PATTERNS)

    def generate_report(self, transcription: str) -> MeetingReport:
        text = (transcription or "").strip()
        if not text:
            return MeetingReport(full_transcription="")

        sentences = self._split_sentences(text)
        if not sentences:
            return MeetingReport(full_transcription=text)

        decisions = self._collect_matches(sentences, self._decision_re)
        pending = self._collect_matches(sentences, self._pending_re)
        action_sentences = self._collect_matches(sentences, self._action_re)
        actions = [self._build_action(sentence) for sentence in action_sentences]

        discussed = self._select_discussed_points(sentences)
        executive_summary = self._build_executive_summary(sentences)
        subject = self._infer_subject(sentences)

        return MeetingReport(
            title="Compte rendu de réunion",
            date=None,
            participants=[],
            subject=subject,
            executive_summary=executive_summary,
            discussed_points=discussed,
            decisions=decisions,
            action_items=actions,
            pending_points=pending,
            full_transcription=text,
            whatsapp_summary="",
        )

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        normalised = re.sub(r"\s+", " ", text).strip()
        if not normalised:
            return []
        raw_sentences = _SENTENCE_BOUNDARY.split(normalised)
        return [sentence.strip() for sentence in raw_sentences if sentence.strip()]

    @staticmethod
    def _collect_matches(sentences: list[str], pattern: re.Pattern[str]) -> list[str]:
        return [sentence for sentence in sentences if pattern.search(sentence)]

    @staticmethod
    def _build_action(sentence: str) -> ActionItem:
        responsible_match = _RESPONSIBLE_HINTS.search(sentence)
        due_match = _DUE_DATE_HINTS.search(sentence)
        return ActionItem(
            description=sentence,
            responsible=responsible_match.group(1).strip() if responsible_match else None,
            due_date=due_match.group(1).strip() if due_match else None,
            status="À faire",
        )

    def _select_discussed_points(self, sentences: list[str]) -> list[str]:
        ranked = self._rank_sentences(sentences)
        top = ranked[: self._discussed_max_sentences]
        top.sort(key=lambda scored: scored.index)
        return [scored.text for scored in top]

    def _build_executive_summary(self, sentences: list[str]) -> str:
        ranked = self._rank_sentences(sentences)
        top = ranked[: self._summary_max_sentences]
        if not top:
            return UNSPECIFIED
        top.sort(key=lambda scored: scored.index)
        return " ".join(scored.text for scored in top)

    @staticmethod
    def _rank_sentences(sentences: list[str]) -> list[_ScoredSentence]:
        frequencies = _compute_word_frequencies(sentences)
        scored: list[_ScoredSentence] = []
        for index, sentence in enumerate(sentences):
            tokens = [token.lower() for token in _TOKEN_PATTERN.findall(sentence)]
            if not tokens:
                continue
            base = sum(frequencies.get(token, 0.0) for token in tokens) / len(tokens)
            scored.append(_ScoredSentence(text=sentence, score=base, index=index))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored

    @staticmethod
    def _infer_subject(sentences: list[str]) -> str | None:
        if not sentences:
            return None
        first = sentences[0]
        return first if len(first) <= 160 else first[:157].rstrip() + "…"


def _compute_word_frequencies(sentences: list[str]) -> dict[str, float]:
    counter: Counter[str] = Counter()
    for sentence in sentences:
        for token in _TOKEN_PATTERN.findall(sentence.lower()):
            if token in _FRENCH_STOPWORDS or len(token) <= 2:
                continue
            counter[token] += 1
    if not counter:
        return {}
    max_frequency = max(counter.values())
    return {word: count / max_frequency for word, count in counter.items()}


def _compile_any(patterns: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile("|".join(patterns), re.IGNORECASE)

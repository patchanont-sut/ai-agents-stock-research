"""Thai translation support for completed analysis results.

Agents own financial reasoning in English. This service owns the Thai copies
used by the UI's language toggle.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from config import settings
from .models import AnalysisResult

logger = logging.getLogger(__name__)

VALUATION_VERDICT_TH = {
    "fair": "มูลค่าเหมาะสม",
    "fair value": "มูลค่าเหมาะสม",
    "fairly valued": "มูลค่าเหมาะสม",
    "fairly valued.": "มูลค่าเหมาะสม",
    "undervalued": "ต่ำกว่ามูลค่าที่เหมาะสม",
    "under valued": "ต่ำกว่ามูลค่าที่เหมาะสม",
    "overvalued": "สูงกว่ามูลค่าที่เหมาะสม",
    "over valued": "สูงกว่ามูลค่าที่เหมาะสม",
}

RECOMMENDATION_TH = {
    "BUY": "ซื้อ",
    "HOLD": "ถือ",
    "SELL": "ขาย",
}

MEMO_HEADING_TH = {
    "Decision Rationale": "เหตุผลของคำแนะนำ",
    "Bull Case": "กรณีเชิงบวก",
    "Bear Case": "กรณีเชิงลบ",
    "Key Risks": "ความเสี่ยงสำคัญ",
    "What Would Change the View": "ปัจจัยที่อาจเปลี่ยนมุมมอง",
    "Executive Summary": "สรุปผู้บริหาร",
}


@dataclass
class TranslationReport:
    attempted: int = 0
    translated: int = 0
    failed: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failed and not self.missing_required


TranslationField = tuple[str, Any, str, str, bool]


def has_thai(value: Any) -> bool:
    if isinstance(value, str):
        return any("\u0e00" <= char <= "\u0e7f" for char in value)
    if isinstance(value, list):
        return any(has_thai(item) for item in value)
    return False


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return text[start:end].strip()
    if text.startswith("```"):
        start = text.index("```") + 3
        end = text.index("```", start)
        return text[start:end].strip()
    return text


class ThaiTranslationService:
    def __init__(self):
        self.url = settings.get_deepseek_chat_url()
        self.headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }

    async def translate_analysis(self, result: AnalysisResult) -> TranslationReport:
        report = TranslationReport()
        self._apply_static_translations(result)
        fields = self._fields(result)
        pending: dict[str, tuple[TranslationField, Any]] = {}

        for index, field_spec in enumerate(fields):
            label, obj, source_attr, target_attr, _required = field_spec
            current = getattr(obj, source_attr)
            existing = getattr(obj, target_attr)

            if not current:
                continue
            if self._is_valid_translation(existing, current):
                report.translated += 1
                continue

            pending[f"field_{index}"] = (field_spec, current)

        report.attempted = len(pending)

        if pending:
            payload = {
                field_id: current
                for field_id, (_, current) in pending.items()
            }
            translated: dict[str, Any] = {}
            failed_ids: set[str] = set()
            async with httpx.AsyncClient(timeout=120) as client:
                for batch in self._batches(payload):
                    try:
                        translated.update(await self._translate_payload(client, batch))
                    except Exception as e:
                        logger.error("Thai translation batch failed: %s", e)
                        failed_ids.update(batch.keys())

                for field_id, (field_spec, current) in pending.items():
                    label, obj, _source_attr, target_attr, required = field_spec
                    value = translated.get(field_id)
                    if self._is_valid_translation(value, current):
                        setattr(obj, target_attr, value)
                        report.translated += 1
                        continue

                    try:
                        fallback_value = await self._translate_value(client, current)
                        if self._is_valid_translation(fallback_value, current):
                            setattr(obj, target_attr, fallback_value)
                            report.translated += 1
                            if field_id in failed_ids:
                                logger.info("Thai translation recovered via single-field fallback: %s", label)
                            continue
                    except Exception as e:
                        logger.error("Thai translation fallback failed for %s: %s", label, e)

                    if required:
                        report.failed.append(label)

        report.missing_required = self._missing_required(fields)
        return report

    def inspect_analysis(self, result: AnalysisResult) -> TranslationReport:
        """Check translation coverage without calling the translation API."""
        self._apply_static_translations(result)
        fields = self._fields(result)
        report = TranslationReport()

        for field_spec in fields:
            label, obj, source_attr, target_attr, required = field_spec
            current = getattr(obj, source_attr)
            if not current:
                continue
            if self._is_valid_translation(getattr(obj, target_attr), current):
                report.translated += 1
            elif required:
                report.missing_required.append(label)

        return report

    def _batches(self, payload: dict[str, Any], max_chars: int = 6000) -> list[dict[str, Any]]:
        batches: list[dict[str, Any]] = []
        current: dict[str, Any] = {}
        current_chars = 0

        for key, value in payload.items():
            size = len(json.dumps({key: value}, ensure_ascii=False))
            if current and current_chars + size > max_chars:
                batches.append(current)
                current = {}
                current_chars = 0
            current[key] = value
            current_chars += size

        if current:
            batches.append(current)
        return batches

    def _apply_static_translations(self, result: AnalysisResult) -> None:
        if result.valuation and not has_thai(result.valuation.verdict_th):
            verdict_key = result.valuation.verdict.strip().lower()
            translated = VALUATION_VERDICT_TH.get(verdict_key)
            if translated:
                result.valuation.verdict_th = translated

        memo = result.investment_memo
        if memo is None:
            return

        if memo.recommendation and not has_thai(memo.recommendation_th):
            mapped = RECOMMENDATION_TH.get(memo.recommendation.strip())
            if mapped:
                memo.recommendation_th = mapped

        for section in memo.sections:
            if section.heading and not has_thai(section.heading_th):
                mapped = MEMO_HEADING_TH.get(section.heading.strip())
                if mapped:
                    section.heading_th = mapped
            for citation in section.citations:
                pass  # citations translated via LLM
        for kc in memo.key_citations:
            pass  # key citations translated via LLM

    async def _translate_payload(self, client: httpx.AsyncClient, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Translate this JSON object from English to natural Thai for a financial dashboard. "
            "Keep the exact same field_ keys and value shapes. If a value is an array, return an array with the same length. "
            "Keep stock symbols, company names, numbers, and financial terms such as P/E, PEG, EPS, Beta, BUY, HOLD, and SELL in English. "
            "Return ONLY valid JSON. No markdown, no explanations.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
        request = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional Thai translator for investment analysis. Return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8192,
            "temperature": 0.2,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
        }

        response = await client.post(self.url, headers=self.headers, json=request)
        response.raise_for_status()
        data = response.json()

        message = data.get("choices", [{}])[0].get("message", {})
        content = message.get("content") or message.get("reasoning_content") or ""
        parsed = json.loads(_strip_code_fence(content))
        if not isinstance(parsed, dict):
            raise ValueError("Translator returned non-object JSON")
        return parsed

    async def _translate_value(self, client: httpx.AsyncClient, value: Any) -> Any:
        return (await self._translate_payload(client, {"value": value})).get("value", value)

    def _is_valid_translation(self, translated: Any, original: Any) -> bool:
        if isinstance(original, list):
            return (
                isinstance(translated, list)
                and len(translated) == len(original)
                and all(
                    has_thai(new_value)
                    for old_value, new_value in zip(original, translated)
                    if old_value
                )
            )
        return isinstance(translated, str) and has_thai(translated)

    def _missing_required(self, fields: list[TranslationField]) -> list[str]:
        return [
            label
            for label, obj, source_attr, target_attr, required in fields
            if (
                required
                and getattr(obj, source_attr)
                and not self._is_valid_translation(getattr(obj, target_attr), getattr(obj, source_attr))
            )
        ]

    def _fields(self, result: AnalysisResult) -> list[TranslationField]:
        fields: list[TranslationField] = []

        def add(label: str, obj: Any, source_attr: str, target_attr: str, required: bool = False):
            if obj is None:
                return
            fields.append((label, obj, source_attr, target_attr, required))

        add("research.company_profile", result.research, "company_profile", "company_profile_th")
        add("research.summary", result.research, "summary", "summary_th")
        add("sentiment.explanation", result.sentiment, "explanation", "explanation_th")
        add("bull.thesis", result.bull_case, "thesis", "thesis_th", required=True)
        add("bull.evidence", result.bull_case, "evidence", "evidence_th")
        add("bull.catalysts", result.bull_case, "catalysts", "catalysts_th")
        add("bear.thesis", result.bear_case, "thesis", "thesis_th", required=True)
        add("bear.evidence", result.bear_case, "evidence", "evidence_th")
        add("bear.risk_factors", result.bear_case, "risk_factors", "risk_factors_th")
        add("risk.macro_factors", result.risk, "macro_factors", "macro_factors_th")
        add("risk.company_factors", result.risk, "company_factors", "company_factors_th")
        add("risk.summary", result.risk, "summary", "summary_th", required=True)
        add("valuation.verdict", result.valuation, "verdict", "verdict_th")
        add("valuation.explanation", result.valuation, "explanation", "explanation_th", required=True)
        add("debate.summary", result.debate, "summary", "summary_th")
        add("cio.reasoning", result.cio_decision, "reasoning", "reasoning_th", required=True)
        add("cio.key_points", result.cio_decision, "key_points", "key_points_th")

        if result.debate:
            for index, turn in enumerate(result.debate.turns):
                add(f"debate.turns[{index}].content", turn, "content", "content_th", required=True)

        memo = result.investment_memo
        if memo:
            add("memo.title", memo, "title", "title_th")
            add("memo.executive_summary", memo, "executive_summary", "executive_summary_th", required=True)
            if memo.recommendation and not has_thai(memo.recommendation_th):
                add("memo.recommendation", memo, "recommendation", "recommendation_th")
            for si, section in enumerate(memo.sections):
                if section.heading and not has_thai(section.heading_th):
                    add(f"memo.sections[{si}].heading", section, "heading", "heading_th")
                add(f"memo.sections[{si}].content", section, "content", "content_th", required=True)
                for ci, citation in enumerate(section.citations):
                    add(f"memo.sections[{si}].citations[{ci}].quote_or_summary", citation, "quote_or_summary", "quote_or_summary_th")
            for ki, kc in enumerate(memo.key_citations):
                add(f"memo.key_citations[{ki}].quote_or_summary", kc, "quote_or_summary", "quote_or_summary_th")

        return fields

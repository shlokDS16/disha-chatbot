"""LLM-powered file summariser for OCR-extracted documents.

Pipeline:
  1. OCR extracts raw text (handled elsewhere, in services/ocr.py).
  2. Heuristic regex pulls out common blood-report markers as structured
     `KeyFinding`s (for the UI's highlighted strip).
  3. Groq LLM is given the actual OCR text and produces:
       - a detailed, plain-language analysis of what the document says
       - a short "what it means" paragraph
       - personalised next steps
     in the requested language.
  4. If the LLM is unavailable we fall back to templated copy so the UI
     still renders something sensible.

The response (see schemas.FileSummary) intentionally exposes both the raw
OCR text AND the structured LLM output so the frontend can render
"Document contents" + "Summary" side by side.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.config import Settings
from app.errors import DishaError
from app.models.schemas import FileSummary, KeyFinding, Language, Severity
from app.services.groq_client import chat_complete

_log = logging.getLogger("disha.file_summary")


# ── Heuristic structured extraction ─────────────────────────────────

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("HbS", re.compile(r"\bhb\s?s\b[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%?", re.I)),
    ("HbA", re.compile(r"\bhb\s?a\b(?!\s?2)[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%?", re.I)),
    ("HbA2", re.compile(r"\bhb\s?a\s?2\b[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%?", re.I)),
    ("HbF", re.compile(r"\bhb\s?f\b[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%?", re.I)),
    (
        "Haemoglobin",
        re.compile(
            r"\b(?:haemoglobin|hemoglobin|hb)\b[^0-9%]*([0-9]+(?:\.[0-9]+)?)\s*g/?d?l?",
            re.I,
        ),
    ),
    (
        "Platelets",
        re.compile(
            r"\bplatelets?\b[^0-9]*([0-9]+(?:[.,][0-9]+)?)\s*(?:lakh|10\^?3|x\s*10\^?9)?",
            re.I,
        ),
    ),
]


def _severity_for(label: str, value: float) -> Severity:
    if label == "HbS":
        if value >= 60:
            return Severity.CRITICAL
        if value >= 30:
            return Severity.WARNING
        if value > 0:
            return Severity.INFO
        return Severity.NORMAL
    if label == "HbA2":
        if value > 3.5:
            return Severity.WARNING
        return Severity.NORMAL
    if label == "HbF":
        if value > 2:
            return Severity.INFO
        return Severity.NORMAL
    if label == "Haemoglobin":
        if value < 8:
            return Severity.CRITICAL
        if value < 11:
            return Severity.WARNING
        return Severity.NORMAL
    return Severity.INFO


_NATIVE_LABELS: dict[str, dict[Language, str]] = {
    "HbS": {Language.EN: "HbS", Language.HI: "HbS", Language.MR: "HbS"},
    "HbA": {Language.EN: "HbA", Language.HI: "HbA", Language.MR: "HbA"},
    "HbA2": {Language.EN: "HbA2", Language.HI: "HbA2", Language.MR: "HbA2"},
    "HbF": {Language.EN: "HbF", Language.HI: "HbF", Language.MR: "HbF"},
    "Haemoglobin": {
        Language.EN: "Haemoglobin",
        Language.HI: "हीमोग्लोबिन",
        Language.MR: "हिमोग्लोबिन",
    },
    "Platelets": {
        Language.EN: "Platelets",
        Language.HI: "प्लेटलेट्स",
        Language.MR: "प्लेटलेट्स",
    },
}


def _extract_findings(text: str, language: Language) -> list[KeyFinding]:
    findings: list[KeyFinding] = []
    seen: set[str] = set()
    for raw_label, pattern in _PATTERNS:
        if raw_label in seen:
            continue
        m = pattern.search(text)
        if not m:
            continue
        seen.add(raw_label)
        try:
            value = float(m.group(1).replace(",", ""))
        except (ValueError, IndexError):
            continue
        findings.append(
            KeyFinding(
                label_native=_NATIVE_LABELS[raw_label][language],
                label_en=raw_label,
                value=m.group(1),
                severity=_severity_for(raw_label, value),
            )
        )
    return findings


# ── LLM-based narrative summary ─────────────────────────────────────

_LANG_NAME = {Language.EN: "English", Language.HI: "Hindi", Language.MR: "Marathi"}

_SYSTEM_PROMPT_TEMPLATE = (
    "You are Disha, a careful, warm genetic-counselling assistant helping "
    "people in tribal Maharashtra (India) understand medical documents. "
    "You will be given the raw text of a document the user uploaded — it "
    "may be a blood report, prescription, resume, any PDF/scan. "
    "Produce JSON only, no prose outside the JSON. Write all human-readable "
    "text in {lang_name}. Keep language simple (8th-grade level), never "
    "give a diagnosis, and gently recommend consulting a doctor / ASHA "
    "worker. If the document is not a medical report (e.g. a resume, "
    "letter), say so in the summary and describe what it actually is."
)

_USER_PROMPT_TEMPLATE = (
    "Document OCR text (may contain noise):\n"
    "---\n{ocr_text}\n---\n\n"
    "Return JSON with exactly these keys:\n"
    "{{\n"
    '  "document_type": "<one short phrase, e.g. \'Blood report\', \'Resume\', '
    '\'Prescription\', \'Unclear\'>",\n'
    '  "detailed_analysis": "<3-6 sentence paragraph describing what the '
    'document contains in plain {lang_name}. Summarise sections, values, '
    'names — whatever is actually present>",\n'
    '  "what_it_means": "<2-4 sentences interpreting what the user should '
    'take away, in {lang_name}. Cautious, non-diagnostic>",\n'
    '  "next_steps": ["<step 1>", "<step 2>", "<step 3>"]\n'
    "}}\n\n"
    "Rules:\n"
    "- All output text must be in {lang_name}.\n"
    "- next_steps must be 2-4 actionable items, each under 20 words.\n"
    "- Never invent test values that are not present in the text.\n"
    "- If the document is not a medical report, next_steps should describe "
    "what the user might want to do with the document instead (e.g. 'Upload "
    "a blood report if you want Disha to analyse lab values')."
)


def _fallback_summary(
    text: str, language: Language, findings: list[KeyFinding]
) -> dict[str, Any]:
    is_medical = bool(findings) or bool(
        re.search(r"\bhb\s?[sa2f]?\b|haemoglobin|platelet|blood", text, re.I)
    )
    doc_type_by_lang = {
        Language.EN: ("Blood report" if is_medical else "Document"),
        Language.HI: ("रक्त रिपोर्ट" if is_medical else "दस्तावेज़"),
        Language.MR: ("रक्त अहवाल" if is_medical else "दस्तऐवज"),
    }
    preview = text.strip().replace("\n", " ")[:300]
    analysis = {
        Language.EN: (
            f"The uploaded document appears to be a "
            f"{doc_type_by_lang[Language.EN].lower()}. "
            f"Here is the first portion of extracted text: \"{preview}\""
        ),
        Language.HI: (
            f"अपलोड किया गया दस्तावेज़ {doc_type_by_lang[Language.HI]} जैसा दिखता है। "
            f"निकाले गए टेक्स्ट का पहला हिस्सा: \"{preview}\""
        ),
        Language.MR: (
            f"अपलोड केलेला दस्तऐवज {doc_type_by_lang[Language.MR]} असल्याचे दिसते. "
            f"काढलेल्या मजकुराचा पहिला भाग: \"{preview}\""
        ),
    }
    means = {
        Language.EN: (
            "Automatic interpretation is unavailable right now. Please share "
            "this document with your ASHA worker or doctor for a confirmed reading."
        ),
        Language.HI: (
            "अभी स्वचालित व्याख्या उपलब्ध नहीं है। कृपया अपनी ASHA कार्यकर्ता "
            "या डॉक्टर के साथ यह दस्तावेज़ साझा करें।"
        ),
        Language.MR: (
            "आत्ता स्वयंचलित विश्लेषण उपलब्ध नाही. कृपया हा दस्तऐवज तुमच्या "
            "ASHA कार्यकर्ता किंवा डॉक्टरांना दाखवा."
        ),
    }
    steps = {
        Language.EN: [
            "Share this report with your ASHA worker or doctor.",
            "Ask for an Hb HPLC test if not already done.",
            "If you are planning pregnancy, consult a genetic counsellor.",
        ],
        Language.HI: [
            "यह रिपोर्ट अपनी ASHA कार्यकर्ता या डॉक्टर को दिखाएँ।",
            "यदि Hb HPLC जाँच नहीं हुई है तो करवाएँ।",
            "यदि गर्भावस्था की योजना है तो आनुवंशिक सलाहकार से मिलें।",
        ],
        Language.MR: [
            "हा अहवाल तुमच्या ASHA कार्यकर्ता किंवा डॉक्टरांना दाखवा.",
            "जर Hb HPLC चाचणी झाली नसेल तर करून घ्या.",
            "गर्भधारणेची योजना असल्यास अनुवंशिक सल्लागाराला भेटा.",
        ],
    }
    return {
        "document_type": doc_type_by_lang[language],
        "detailed_analysis": analysis[language],
        "what_it_means": means[language],
        "next_steps": steps[language],
    }


def _parse_llm_json(raw: str) -> dict[str, Any] | None:
    """Pull the first JSON object out of the LLM response."""
    if not raw:
        return None
    # Strip common code fences.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
    # Greedy first-object grab.
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _llm_analyse(
    settings: Settings, text: str, language: Language
) -> dict[str, Any] | None:
    if not text.strip():
        return None
    # Truncate long OCR output — Groq prompt limits + we want focused analysis.
    snippet = text if len(text) < 8000 else text[:8000] + "\n...[truncated]"
    lang_name = _LANG_NAME[language]
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(lang_name=lang_name)
    user_prompt = _USER_PROMPT_TEMPLATE.format(ocr_text=snippet, lang_name=lang_name)
    try:
        answer, _ = chat_complete(
            settings=settings,
            system_prompt=system_prompt,
            user_text=user_prompt,
            max_tokens=900,
            temperature=0.3,
        )
    except DishaError as e:
        _log.info("LLM summary unavailable: %s", e.message)
        return None
    parsed = _parse_llm_json(answer)
    if not parsed:
        _log.warning("LLM summary did not return parsable JSON; got %r", answer[:200])
    return parsed


# ── Public API ──────────────────────────────────────────────────────


def summarise_ocr_text(
    text: str, language: Language, settings: Settings | None = None
) -> FileSummary:
    findings = _extract_findings(text, language)
    llm_out: dict[str, Any] | None = None
    if settings is not None:
        llm_out = _llm_analyse(settings, text, language)
    data = llm_out or _fallback_summary(text, language, findings)

    next_steps = data.get("next_steps") or []
    if not isinstance(next_steps, list):
        next_steps = [str(next_steps)]
    next_steps = [str(s).strip() for s in next_steps if str(s).strip()][:5]

    return FileSummary(
        language=language,
        key_findings=findings,
        what_it_means=str(data.get("what_it_means") or "").strip(),
        next_steps=next_steps,
        document_type=str(data.get("document_type") or "").strip() or None,
        detailed_analysis=str(data.get("detailed_analysis") or "").strip() or None,
        full_text=text.strip() or None,
    )


def summary_to_dict(summary: FileSummary) -> dict[str, Any]:
    return summary.model_dump(mode="json")

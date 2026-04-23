"""Punnett square calculator for sickle-cell / β-thalassemia parental genotypes.

Uses simplified single-locus Mendelian inheritance on the HBB allele. Alleles:
  A  — normal β-globin
  S  — sickle mutation
  C  — HbC mutation
  b  — β-thalassemia mutation

Genotype combinations we support (matching HbGenotype enum):
  AA, AS, SS, SC, S_beta_thal
"""
from __future__ import annotations

from collections import Counter

from app.models.schemas import (
    HbGenotype,
    Language,
    PunnettCell,
    PunnettData,
    PunnettNarrative,
    PunnettProbabilities,
    PunnettResponse,
    Severity,
)

# Genotype → individual alleles carried.
_ALLELES: dict[HbGenotype, tuple[str, str]] = {
    HbGenotype.AA: ("A", "A"),
    HbGenotype.AS: ("A", "S"),
    HbGenotype.SS: ("S", "S"),
    HbGenotype.SC: ("S", "C"),
    HbGenotype.S_BETA_THAL: ("S", "b"),
}


# Offspring allele-pair → offspring genotype label (order-insensitive).
def _pair_to_genotype(a: str, b: str) -> HbGenotype:
    pair = tuple(sorted([a, b]))
    mapping: dict[tuple[str, str], HbGenotype] = {
        ("A", "A"): HbGenotype.AA,
        ("A", "S"): HbGenotype.AS,
        ("S", "S"): HbGenotype.SS,
        ("C", "S"): HbGenotype.SC,
        ("b", "S"): HbGenotype.S_BETA_THAL,
        # Heterozygote carriers we fold into AS bucket visually; AC / Ab are
        # simple carriers too. The UI groups carriers under AS for the prototype.
        ("A", "C"): HbGenotype.AS,
        ("A", "b"): HbGenotype.AS,
        # Compound clinical phenotypes we do not separately visualise.
        ("C", "C"): HbGenotype.SC,
        ("b", "b"): HbGenotype.S_BETA_THAL,
        ("C", "b"): HbGenotype.S_BETA_THAL,
    }
    return mapping[pair]


_SEVERITY: dict[HbGenotype, Severity] = {
    HbGenotype.AA: Severity.NORMAL,
    HbGenotype.AS: Severity.CARRIER,
    HbGenotype.SS: Severity.AFFECTED,
    HbGenotype.SC: Severity.AFFECTED,
    HbGenotype.S_BETA_THAL: Severity.AFFECTED,
}


def _build_grid(
    p1: HbGenotype, p2: HbGenotype
) -> tuple[list[list[PunnettCell]], Counter]:
    a1, a2 = _ALLELES[p1]
    b1, b2 = _ALLELES[p2]
    p1_alleles = [a1, a2]
    p2_alleles = [b1, b2]

    grid: list[list[PunnettCell]] = []
    tally: Counter = Counter()
    for pa in p1_alleles:
        row: list[PunnettCell] = []
        for pb in p2_alleles:
            genotype = _pair_to_genotype(pa, pb)
            row.append(
                PunnettCell(
                    genotype=genotype,
                    probability=0.25,
                    severity=_SEVERITY[genotype],
                )
            )
            tally[genotype] += 1
        grid.append(row)
    return grid, tally


def _counts_to_probabilities(counts: Counter) -> PunnettProbabilities:
    total = sum(counts.values()) or 1
    return PunnettProbabilities(
        AA=counts.get(HbGenotype.AA, 0) / total,
        AS=counts.get(HbGenotype.AS, 0) / total,
        SS=counts.get(HbGenotype.SS, 0) / total,
        SC=counts.get(HbGenotype.SC, 0) / total,
        S_beta_thal=counts.get(HbGenotype.S_BETA_THAL, 0) / total,
    )


def _risk_level(
    probs: PunnettProbabilities,
) -> str:
    affected = probs.SS + probs.SC + probs.S_beta_thal
    carrier = probs.AS
    if affected >= 1.0:
        return "certain"
    if affected >= 0.5:
        return "very_high"
    if affected >= 0.25:
        return "high"
    if affected > 0:
        return "moderate"
    if carrier > 0:
        return "low"
    return "none"


# Narrative templates — short, plain language, three languages.
_HEADLINES: dict[str, dict[Language, str]] = {
    "none": {
        Language.EN: "No risk of sickle cell disease in children.",
        Language.HI: "बच्चों में सिकल सेल रोग का कोई खतरा नहीं।",
        Language.MR: "मुलांमध्ये सिकल सेल आजाराचा धोका नाही.",
    },
    "low": {
        Language.EN: "Children may be carriers — but none will be affected.",
        Language.HI: "बच्चे वाहक हो सकते हैं — लेकिन कोई बीमार नहीं होगा।",
        Language.MR: "मुले वाहक असू शकतात — पण कोणी आजारी होणार नाही.",
    },
    "moderate": {
        Language.EN: "Some risk your child could be affected.",
        Language.HI: "कुछ जोखिम है कि बच्चा प्रभावित हो सकता है।",
        Language.MR: "मुलाला आजार होण्याचा थोडा धोका आहे.",
    },
    "high": {
        Language.EN: "1 in 4 chance of an affected child — please talk to a counsellor.",
        Language.HI: "4 में से 1 बच्चा प्रभावित हो सकता है — कृपया सलाहकार से बात करें।",
        Language.MR: "4 पैकी 1 मूल बाधित होऊ शकते — कृपया सल्लागाराशी बोला.",
    },
    "very_high": {
        Language.EN: "High chance each child will have sickle cell disease.",
        Language.HI: "हर बच्चे के सिकल सेल रोग से प्रभावित होने की अधिक संभावना।",
        Language.MR: "प्रत्येक मूल सिकल सेल आजाराने बाधित होण्याची जास्त शक्यता.",
    },
    "certain": {
        Language.EN: "Every child will have sickle cell disease.",
        Language.HI: "हर बच्चे को सिकल सेल रोग होगा।",
        Language.MR: "प्रत्येक मुलाला सिकल सेल आजार होईल.",
    },
}

_BODIES: dict[Language, str] = {
    Language.EN: (
        "This is an estimate based on the Hb genotype pair. Please confirm via "
        "HPLC and meet a genetic counsellor before planning pregnancy."
    ),
    Language.HI: (
        "यह अनुमान Hb जीनोटाइप पर आधारित है। कृपया HPLC से पुष्टि करें और "
        "गर्भावस्था से पहले आनुवंशिक सलाहकार से मिलें।"
    ),
    Language.MR: (
        "हा अंदाज Hb जीनोटाइपवर आधारित आहे. कृपया HPLC ने खात्री करा आणि "
        "गर्भधारणेपूर्वी अनुवंशिक सल्लागाराला भेटा."
    ),
}


def calculate_punnett(
    parent1: HbGenotype, parent2: HbGenotype, language: Language
) -> PunnettResponse:
    grid, counts = _build_grid(parent1, parent2)
    probs = _counts_to_probabilities(counts)
    risk = _risk_level(probs)
    narrative = PunnettNarrative(
        headline=_HEADLINES[risk][language],
        body=_BODIES[language],
        risk_level=risk,  # type: ignore[arg-type]
    )
    return PunnettResponse(
        probabilities=probs,
        narrative=narrative,
        visual_data=PunnettData(p1=parent1, p2=parent2, probabilities=probs, grid=grid),
    )

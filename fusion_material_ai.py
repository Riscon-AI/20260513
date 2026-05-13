from __future__ import annotations

import csv
import json
import math
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Element:
    symbol: str
    name: str
    atomic_radius_pm: float
    melting_point_c: float
    density_g_cm3: float
    valence_electrons: float
    electronegativity: float
    thermal_conductivity_w_mk: float
    activation_risk: float
    cost_risk: float
    ductility_prior: float


@dataclass
class ScreeningIntent:
    prompt: str
    allowed_elements: list[str]
    required_elements: list[str]
    excluded_elements: list[str]
    min_w_fraction: float | None
    min_nbta_fraction: float | None
    max_density: float | None
    min_melting_point: float
    weights: dict[str, float]
    seed: int = 42


@dataclass
class Candidate:
    formula: str
    composition: dict[str, float]
    descriptors: dict[str, float]
    scores: dict[str, float]
    uncertainty: float
    rank_score: float
    recommendation: str
    risk_flags: list[str]
    next_tests: list[str]


ELEMENTS: dict[str, Element] = {
    "W": Element("W", "Tungsten", 139, 3422, 19.25, 6, 2.36, 173, 0.36, 0.55, 0.22),
    "Mo": Element("Mo", "Molybdenum", 139, 2623, 10.28, 6, 2.16, 138, 0.45, 0.35, 0.36),
    "Cr": Element("Cr", "Chromium", 128, 1907, 7.19, 6, 1.66, 94, 0.50, 0.25, 0.30),
    "Ta": Element("Ta", "Tantalum", 146, 3017, 16.69, 5, 1.50, 57.5, 0.62, 0.70, 0.66),
    "Nb": Element("Nb", "Niobium", 146, 2477, 8.57, 5, 1.60, 54, 0.40, 0.45, 0.72),
    "Ti": Element("Ti", "Titanium", 147, 1668, 4.51, 4, 1.54, 22, 0.22, 0.20, 0.76),
    "V": Element("V", "Vanadium", 134, 1910, 6.11, 5, 1.63, 30.7, 0.35, 0.35, 0.70),
    "Hf": Element("Hf", "Hafnium", 159, 2233, 13.31, 4, 1.30, 23, 0.75, 0.75, 0.58),
    "Zr": Element("Zr", "Zirconium", 160, 1855, 6.52, 4, 1.33, 22.6, 0.25, 0.25, 0.72),
    "Re": Element("Re", "Rhenium", 137, 3186, 21.02, 7, 1.90, 48, 0.88, 0.95, 0.45),
}

DEFAULT_ELEMENTS = ["W", "Ta", "Nb", "Ti", "V", "Mo", "Hf", "Zr"]

KOREAN_ELEMENT_ALIASES = {
    "텅스텐": "W",
    "탄탈럼": "Ta",
    "탄탈륨": "Ta",
    "나이오븀": "Nb",
    "니오븀": "Nb",
    "티타늄": "Ti",
    "바나듐": "V",
    "몰리브덴": "Mo",
    "하프늄": "Hf",
    "지르코늄": "Zr",
    "크롬": "Cr",
    "레늄": "Re",
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalize_composition(composition: dict[str, float]) -> dict[str, float]:
    clean = {k: float(v) for k, v in composition.items() if v > 0 and k in ELEMENTS}
    total = sum(clean.values())
    if total <= 0:
        raise ValueError("Composition must contain at least one supported element.")
    if total > 1.5:
        return {k: v / total for k, v in clean.items()}
    return {k: v / total for k, v in clean.items()}


def formula_from_composition(composition: dict[str, float]) -> str:
    ordered = sorted(composition.items(), key=lambda item: (-item[1], item[0]))
    parts = []
    for symbol, fraction in ordered:
        percent = fraction * 100
        if abs(percent - round(percent)) < 0.05:
            rendered = str(int(round(percent)))
        else:
            rendered = f"{percent:.1f}"
        parts.append(f"{symbol}{rendered}")
    return "".join(parts)


def weighted(composition: dict[str, float], attr: str) -> float:
    return sum(getattr(ELEMENTS[symbol], attr) * fraction for symbol, fraction in composition.items())


def mixing_entropy_r(composition: dict[str, float]) -> float:
    return -sum(fraction * math.log(fraction) for fraction in composition.values() if fraction > 0)


def size_mismatch_percent(composition: dict[str, float]) -> float:
    average_radius = weighted(composition, "atomic_radius_pm")
    return 100 * math.sqrt(
        sum(fraction * (1 - ELEMENTS[symbol].atomic_radius_pm / average_radius) ** 2 for symbol, fraction in composition.items())
    )


def electronegativity_spread(composition: dict[str, float]) -> float:
    average_en = weighted(composition, "electronegativity")
    return math.sqrt(
        sum(fraction * (ELEMENTS[symbol].electronegativity - average_en) ** 2 for symbol, fraction in composition.items())
    )


def refractory_fraction(composition: dict[str, float]) -> float:
    return sum(fraction for symbol, fraction in composition.items() if ELEMENTS[symbol].melting_point_c >= 1800)


def bcc_stability_score(vec: float, size_delta: float, entropy_r: float) -> float:
    if vec <= 6.3:
        vec_score = 1.0
    elif vec <= 6.87:
        vec_score = 1 - (vec - 6.3) / 0.57 * 0.45
    else:
        vec_score = max(0.15, 0.55 - (vec - 6.87) * 0.35)
    size_score = clamp(1 - max(0, size_delta - 5.0) / 7.0)
    entropy_score = clamp(entropy_r / math.log(5))
    return clamp(0.55 * vec_score + 0.25 * size_score + 0.20 * entropy_score)


def estimate_scores(composition_input: dict[str, float]) -> Candidate:
    composition = normalize_composition(composition_input)
    formula = formula_from_composition(composition)

    avg_mp = weighted(composition, "melting_point_c")
    avg_density = weighted(composition, "density_g_cm3")
    avg_vec = weighted(composition, "valence_electrons")
    avg_thermal = weighted(composition, "thermal_conductivity_w_mk")
    avg_activation = weighted(composition, "activation_risk")
    avg_cost = weighted(composition, "cost_risk")
    entropy_r = mixing_entropy_r(composition)
    size_delta = size_mismatch_percent(composition)
    en_spread = electronegativity_spread(composition)
    refractory = refractory_fraction(composition)

    w_fraction = composition.get("W", 0.0)
    mo_fraction = composition.get("Mo", 0.0)
    ta_fraction = composition.get("Ta", 0.0)
    nb_fraction = composition.get("Nb", 0.0)
    ti_fraction = composition.get("Ti", 0.0)
    v_fraction = composition.get("V", 0.0)
    zr_fraction = composition.get("Zr", 0.0)
    hf_fraction = composition.get("Hf", 0.0)
    cr_fraction = composition.get("Cr", 0.0)
    re_fraction = composition.get("Re", 0.0)

    bcc_score = bcc_stability_score(avg_vec, size_delta, entropy_r)
    entropy_score = clamp(entropy_r / math.log(5))
    density_score = clamp(1 - (avg_density - 7.0) / 10.0)
    thermal_score = clamp((avg_thermal - 20.0) / 140.0)

    high_temp_score = clamp((avg_mp - 1750) / 1300)
    refractory_boost = clamp((w_fraction + mo_fraction + ta_fraction + nb_fraction) * 0.75 + refractory * 0.25)
    high_temp_score = clamp(0.68 * high_temp_score + 0.32 * refractory_boost)

    ductility_prior = weighted(composition, "ductility_prior")
    ductility_boost = 0.18 * (ti_fraction + v_fraction + nb_fraction + zr_fraction) + 0.08 * ta_fraction
    brittleness_penalty = 0.18 * max(0, w_fraction - 0.55) + 0.08 * mo_fraction + 0.10 * cr_fraction
    mismatch_penalty = 0.045 * max(0, size_delta - 5.5)
    ductility_score = clamp(ductility_prior + ductility_boost + 0.08 * entropy_score - brittleness_penalty - mismatch_penalty)

    activation_score = clamp(1 - avg_activation + 0.05 * (ti_fraction + v_fraction + zr_fraction) - 0.10 * (hf_fraction + re_fraction))
    synthesis_score = clamp(0.38 * bcc_score + 0.25 * entropy_score + 0.20 * clamp(1 - size_delta / 10) + 0.17 * density_score)
    manufacturability_score = clamp(0.55 * ductility_score + 0.25 * density_score + 0.20 * clamp(1 - avg_cost))

    known_family_bonus = 0.0
    element_set = set(composition)
    if element_set.issubset({"W", "Ti", "Zr", "Hf"}) and "W" in element_set:
        known_family_bonus += 0.06
    if element_set.issubset({"W", "Ti", "V", "Zr", "Ta", "Nb"}) and "W" in element_set:
        known_family_bonus += 0.05
    if {"Nb", "Ta", "Ti", "V"}.issubset(element_set):
        known_family_bonus += 0.06

    uncertainty = 0.16
    uncertainty += 0.04 * max(0, len(composition) - 4)
    uncertainty += 0.10 * cr_fraction + 0.18 * re_fraction
    uncertainty += 0.03 if max(composition.values()) < 0.32 else 0
    uncertainty += 0.06 if size_delta > 8 else 0
    uncertainty = clamp(uncertainty - known_family_bonus, 0.08, 0.60)

    scores = {
        "ductility": ductility_score,
        "high_temperature": high_temp_score,
        "bcc_stability": bcc_score,
        "low_activation": activation_score,
        "synthesizability": synthesis_score,
        "manufacturability": manufacturability_score,
        "density": density_score,
        "thermal_transport": thermal_score,
    }

    rank_score = 100 * (
        0.30 * scores["ductility"]
        + 0.20 * scores["high_temperature"]
        + 0.15 * scores["bcc_stability"]
        + 0.15 * scores["low_activation"]
        + 0.10 * scores["synthesizability"]
        + 0.10 * scores["manufacturability"]
    )
    rank_score *= 1 - 0.35 * uncertainty

    risk_flags: list[str] = []
    if ductility_score < 0.48:
        risk_flags.append("연성 예측이 낮음: 인장/굽힘 시험 우선 필요")
    if avg_mp < 1900:
        risk_flags.append("평균 융점이 낮음: 고열 하중 조건 재검토")
    if activation_score < 0.45:
        risk_flags.append("방사화/핵변환 리스크가 큼: 핵자료 기반 재평가 필요")
    if size_delta > 8:
        risk_flags.append("원자 크기 불일치가 큼: 단상 BCC 형성 위험")
    if bcc_score < 0.62:
        risk_flags.append("BCC 안정성 점수가 낮음: CALPHAD/DFT 검증 필요")
    if avg_density > 15:
        risk_flags.append("밀도가 높음: 구조 부품 적용 시 중량 부담")
    if uncertainty > 0.36:
        risk_flags.append("모델 불확실성이 높음: 탐색 후보로만 취급")

    if rank_score >= 68 and len(risk_flags) <= 1:
        recommendation = "우선 DFT/소량 합성 후보"
    elif rank_score >= 58:
        recommendation = "2차 계산 검증 후보"
    elif rank_score >= 48:
        recommendation = "조건 조정 후 재탐색"
    else:
        recommendation = "보류"

    next_tests = [
        "CALPHAD 또는 DFT로 형성에너지와 BCC 단상 안정성 확인",
        "고온 탄성상수, Cauchy pressure, Pugh ratio 등 연성 지표 계산",
        "소량 아크멜팅/분말공정 합성 후 XRD/SEM-EDS 상분석",
        "상온 및 고온 인장시험으로 연신율 검증",
        "중성자 조사, He/H 보유, swelling proxy 평가",
    ]

    descriptors = {
        "avg_melting_point_c": avg_mp,
        "avg_density_g_cm3": avg_density,
        "avg_vec": avg_vec,
        "avg_thermal_conductivity_w_mk": avg_thermal,
        "mixing_entropy_r": entropy_r,
        "size_mismatch_percent": size_delta,
        "electronegativity_spread": en_spread,
        "refractory_fraction": refractory,
    }

    return Candidate(
        formula=formula,
        composition={symbol: round(fraction * 100, 3) for symbol, fraction in composition.items()},
        descriptors={key: round(value, 4) for key, value in descriptors.items()},
        scores={key: round(value, 4) for key, value in scores.items()},
        uncertainty=round(uncertainty, 4),
        rank_score=round(rank_score, 2),
        recommendation=recommendation,
        risk_flags=risk_flags,
        next_tests=next_tests,
    )


def apply_intent_ranking(candidate: Candidate, intent: ScreeningIntent) -> Candidate:
    weighted_score = 100 * sum(
        candidate.scores.get(score_name, 0) * weight for score_name, weight in intent.weights.items()
    )
    weighted_score *= 1 - 0.35 * candidate.uncertainty
    candidate.rank_score = round(weighted_score, 2)

    if candidate.rank_score >= 68 and len(candidate.risk_flags) <= 1:
        candidate.recommendation = "우선 DFT/소량 합성 후보"
    elif candidate.rank_score >= 58:
        candidate.recommendation = "2차 계산 검증 후보"
    elif candidate.rank_score >= 48:
        candidate.recommendation = "조건 조정 후 재탐색"
    else:
        candidate.recommendation = "보류"
    return candidate


def parse_prompt(prompt: str) -> ScreeningIntent:
    text = prompt.strip()
    lowered = text.lower()

    found_elements: list[str] = []
    for symbol in ELEMENTS:
        if re.search(rf"(?<![A-Za-z]){re.escape(symbol)}(?![a-z])", text):
            found_elements.append(symbol)
    for alias, symbol in KOREAN_ELEMENT_ALIASES.items():
        if alias in text:
            found_elements.append(symbol)
    found_elements = sorted(set(found_elements), key=lambda symbol: list(ELEMENTS).index(symbol))

    allowed = found_elements or DEFAULT_ELEMENTS.copy()
    if "저방사화" in text or "low activation" in lowered:
        allowed = [symbol for symbol in allowed if symbol not in {"Re"}]
    if "크롬 제외" in text or "exclude cr" in lowered:
        allowed = [symbol for symbol in allowed if symbol != "Cr"]
    if "하프늄 제외" in text or "exclude hf" in lowered:
        allowed = [symbol for symbol in allowed if symbol != "Hf"]
    if "레늄" in text or "rhenium" in lowered:
        if "Re" not in allowed:
            allowed.append("Re")
    if "크롬" in text or "chromium" in lowered:
        if "Cr" not in allowed:
            allowed.append("Cr")

    required: list[str] = []
    if "w-rich" in lowered or "텅스텐 고함량" in text or "텅스텐 기반" in text or "w 기반" in lowered:
        required.append("W")
    if "nbta" in lowered or "nb-ta" in lowered or "나이오븀-탄탈" in text or "니오븀-탄탈" in text:
        required.extend(["Nb", "Ta"])
    if "w-ti-v" in lowered:
        required.extend(["W", "Ti", "V"])
    if "w-ti-zr-hf" in lowered:
        required.extend(["W", "Ti", "Zr", "Hf"])
    required = sorted(set(required), key=lambda symbol: list(ELEMENTS).index(symbol))
    for symbol in required:
        if symbol not in allowed:
            allowed.append(symbol)

    min_w = None
    if "w-rich" in lowered or "텅스텐 고함량" in text or "텅스텐 기반" in text:
        min_w = 0.50
    w_match = re.search(r"W\s*(?:>=|>|최소|이상)?\s*(\d+(?:\.\d+)?)\s*%?", text)
    if w_match:
        value = float(w_match.group(1))
        if value > 1:
            value /= 100
        min_w = max(min_w or 0, value)

    min_nbta = None
    if "nbta-rich" in lowered or "nbta >" in lowered or "nbta 고함량" in text:
        min_nbta = 0.50

    max_density = None
    density_match = re.search(r"(?:density|밀도)\s*(?:<|<=|이하|under)?\s*(\d+(?:\.\d+)?)", lowered)
    if density_match:
        max_density = float(density_match.group(1))

    min_mp = 1850.0
    if "초고온" in text or "high temperature" in lowered or "plasma-facing" in lowered:
        min_mp = 2000.0

    weights = {
        "ductility": 0.30,
        "high_temperature": 0.20,
        "bcc_stability": 0.15,
        "low_activation": 0.15,
        "synthesizability": 0.10,
        "manufacturability": 0.10,
    }
    if "연성" in text or "ductility" in lowered or "ductile" in lowered:
        weights["ductility"] += 0.08
        weights["high_temperature"] -= 0.03
        weights["synthesizability"] -= 0.05
    if "저방사화" in text or "low activation" in lowered or "radiation" in lowered:
        weights["low_activation"] += 0.08
        weights["manufacturability"] -= 0.03
        weights["synthesizability"] -= 0.05

    weights = {key: max(0.04, value) for key, value in weights.items()}
    total_weight = sum(weights.values())
    weights = {key: value / total_weight for key, value in weights.items()}

    excluded = [symbol for symbol in ELEMENTS if symbol not in allowed]
    return ScreeningIntent(
        prompt=text,
        allowed_elements=allowed,
        required_elements=required,
        excluded_elements=excluded,
        min_w_fraction=min_w,
        min_nbta_fraction=min_nbta,
        max_density=max_density,
        min_melting_point=min_mp,
        weights=weights,
    )


def seed_compositions() -> list[dict[str, float]]:
    return [
        {"W": 60, "Ti": 15, "V": 25},
        {"W": 55, "Ti": 15, "Zr": 15, "Hf": 15},
        {"W": 52, "Ti": 18, "V": 20, "Zr": 10},
        {"W": 48, "Ta": 17, "Ti": 20, "V": 15},
        {"W": 45, "Ta": 15, "Nb": 15, "Ti": 15, "V": 10},
        {"W": 50, "Mo": 10, "Ti": 20, "V": 20},
        {"Nb": 30, "Ta": 30, "Ti": 20, "V": 20},
        {"Nb": 25, "Ta": 25, "Ti": 20, "V": 20, "Zr": 10},
        {"Nb": 28, "Ta": 28, "Ti": 18, "V": 18, "Hf": 8},
        {"Ta": 30, "Nb": 25, "Ti": 20, "V": 15, "Zr": 10},
        {"W": 42, "Ta": 18, "Nb": 10, "Ti": 18, "Zr": 12},
        {"W": 50, "Ta": 20, "Ti": 15, "Zr": 15},
    ]


def composition_passes_intent(composition: dict[str, float], intent: ScreeningIntent) -> bool:
    normalized = normalize_composition(composition)
    if any(symbol not in normalized for symbol in intent.required_elements):
        return False
    if intent.min_w_fraction is not None and normalized.get("W", 0) < intent.min_w_fraction:
        return False
    if intent.min_nbta_fraction is not None and normalized.get("Nb", 0) + normalized.get("Ta", 0) < intent.min_nbta_fraction:
        return False
    if any(symbol not in intent.allowed_elements for symbol in normalized):
        return False
    candidate = estimate_scores(normalized)
    if candidate.descriptors["avg_melting_point_c"] < intent.min_melting_point:
        return False
    if intent.max_density is not None and candidate.descriptors["avg_density_g_cm3"] > intent.max_density:
        return False
    return True


def random_dirichlet(rng: random.Random, n: int, alpha: list[float]) -> list[float]:
    values = [rng.gammavariate(a, 1.0) for a in alpha]
    total = sum(values)
    return [value / total for value in values]


def random_candidate(intent: ScreeningIntent, rng: random.Random) -> dict[str, float]:
    pool = list(intent.allowed_elements)
    required = list(intent.required_elements)
    min_size = max(3, len(required))
    max_size = min(5, len(pool))
    size = rng.randint(min_size, max_size)
    rest_pool = [symbol for symbol in pool if symbol not in required]
    subset = required + rng.sample(rest_pool, max(0, size - len(required)))
    subset = sorted(set(subset), key=lambda symbol: pool.index(symbol))

    alpha = []
    for symbol in subset:
        if symbol == "W" and intent.min_w_fraction:
            alpha.append(4.0)
        elif symbol in {"Ti", "V", "Nb", "Zr"}:
            alpha.append(1.6)
        elif symbol in {"Hf", "Re", "Cr"}:
            alpha.append(0.8)
        else:
            alpha.append(1.2)
    values = random_dirichlet(rng, len(subset), alpha)
    return {symbol: round(value * 100, 2) for symbol, value in zip(subset, values)}


def screen_candidates(prompt: str, samples: int = 2500, top_n: int = 25, seed: int = 42) -> dict[str, Any]:
    intent = parse_prompt(prompt)
    intent.seed = seed
    rng = random.Random(seed)

    candidates: dict[str, Candidate] = {}
    for composition in seed_compositions():
        filtered = {symbol: pct for symbol, pct in composition.items() if symbol in intent.allowed_elements}
        if len(filtered) >= 3 and composition_passes_intent(filtered, intent):
            candidate = apply_intent_ranking(estimate_scores(filtered), intent)
            candidates[candidate.formula] = candidate

    attempts = 0
    target_attempts = max(samples * 3, 500)
    while len(candidates) < samples and attempts < target_attempts:
        attempts += 1
        composition = random_candidate(intent, rng)
        try:
            if not composition_passes_intent(composition, intent):
                continue
            candidate = apply_intent_ranking(estimate_scores(composition), intent)
        except ValueError:
            continue
        previous = candidates.get(candidate.formula)
        if previous is None or candidate.rank_score > previous.rank_score:
            candidates[candidate.formula] = candidate

    ranked = sorted(candidates.values(), key=lambda item: item.rank_score, reverse=True)
    return {
        "intent": asdict(intent),
        "generated_count": len(ranked),
        "top": [asdict(candidate) for candidate in ranked[:top_n]],
        "disclaimer": (
            "이 결과는 공개 원소 물성 기반의 physics-informed surrogate screening입니다. "
            "실제 핵융합로 소재 후보로 채택하려면 DFT, CALPHAD, 조사 손상, 합성 및 인장시험 검증이 필요합니다."
        ),
    }


def screening_to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Fusion Alloy AI Screening Report",
        "",
        f"Prompt: {result['intent']['prompt']}",
        "",
        result["disclaimer"],
        "",
        "## Top Candidates",
        "",
        "| Rank | Candidate (at.%) | Score | Uncertainty | Recommendation | Key Risks |",
        "| ---: | --- | ---: | ---: | --- | --- |",
    ]
    for index, candidate in enumerate(result["top"], start=1):
        risks = "; ".join(candidate["risk_flags"]) if candidate["risk_flags"] else "주요 플래그 없음"
        lines.append(
            f"| {index} | {candidate['formula']} | {candidate['rank_score']:.2f} | "
            f"{candidate['uncertainty']:.2f} | {candidate['recommendation']} | {risks} |"
        )
    lines.extend(["", "## Candidate Details", ""])
    for candidate in result["top"][:10]:
        lines.append(f"### {candidate['formula']}")
        lines.append("")
        lines.append(f"- Composition: {json.dumps(candidate['composition'], ensure_ascii=False)}")
        lines.append(f"- Descriptors: {json.dumps(candidate['descriptors'], ensure_ascii=False)}")
        lines.append(f"- Scores: {json.dumps(candidate['scores'], ensure_ascii=False)}")
        lines.append(f"- Next tests: {'; '.join(candidate['next_tests'])}")
        lines.append("")
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "top_candidates.csv"
    md_path = output_dir / "screening_report.md"
    json_path = output_dir / "screening_result.json"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "rank",
                "formula",
                "rank_score",
                "uncertainty",
                "recommendation",
                "composition_at_percent",
                "avg_melting_point_c",
                "avg_density_g_cm3",
                "avg_vec",
                "size_mismatch_percent",
                "risk_flags",
            ]
        )
        for index, candidate in enumerate(result["top"], start=1):
            writer.writerow(
                [
                    index,
                    candidate["formula"],
                    candidate["rank_score"],
                    candidate["uncertainty"],
                    candidate["recommendation"],
                    json.dumps(candidate["composition"], ensure_ascii=False),
                    candidate["descriptors"]["avg_melting_point_c"],
                    candidate["descriptors"]["avg_density_g_cm3"],
                    candidate["descriptors"]["avg_vec"],
                    candidate["descriptors"]["size_mismatch_percent"],
                    "; ".join(candidate["risk_flags"]),
                ]
            )

    md_path.write_text(screening_to_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"csv": str(csv_path), "markdown": str(md_path), "json": str(json_path)}


def element_catalog() -> list[dict[str, Any]]:
    return [asdict(element) for element in ELEMENTS.values()]

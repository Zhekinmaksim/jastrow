# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Gate contract for leader-output validation without answer comparison."""

from genlayer import *

import json
import typing


INPUT = (
    "SPECIFICATION: A submission qualifies if the post carries the hashtag "
    "#GenLayer.\nCASE: A post reading: nice work. # GenLayer "
    "https://genlayer.com"
)

TASK = (
    "Judge the CASE against the SPECIFICATION. Return one JSON object and "
    "nothing else with exactly these fields: answer and confidence. answer "
    "must be ACCEPT, REJECT, or UNSETTLED. confidence must be high or low. "
    "Use UNSETTLED when the specification does not determine whether the "
    "spaced hashtag qualifies."
)

CRITERIA = (
    "The output must be a parseable JSON object. Its answer field must be "
    "exactly ACCEPT, REJECT, or UNSETTLED. Its confidence field must be "
    "exactly high or low. These schema and vocabulary checks are the only "
    "criteria. Do not re-judge the case, do not compare the answer with your "
    "own answer, and do not reject a valid object because you would classify "
    "the case differently."
)


def _parse(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        newline = text.find("\n")
        if newline != -1:
            text = text[newline + 1 :]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return {"answer": "MALFORMED", "confidence": "low"}
    try:
        value = json.loads(text[start : end + 1])
    except Exception:
        return {"answer": "MALFORMED", "confidence": "low"}
    answer = str(value.get("answer", "")).strip().upper()
    confidence = str(value.get("confidence", "")).strip().lower()
    if answer not in ("ACCEPT", "REJECT", "UNSETTLED"):
        answer = "MALFORMED"
    if confidence not in ("high", "low"):
        confidence = "low"
    return {"answer": answer, "confidence": confidence}


class NonComparativeProbe(gl.Contract):
    answers: DynArray[str]

    @gl.public.write
    def probe(self) -> typing.Any:
        raw = gl.eq_principle.prompt_non_comparative(
            lambda: INPUT,
            task=TASK,
            criteria=CRITERIA,
        )
        recorded = _parse(raw)
        self.answers.append(recorded["answer"])
        return {
            "probe": len(self.answers) - 1,
            "answer": recorded["answer"],
            "confidence": recorded["confidence"],
        }

    @gl.public.view
    def get_answers(self) -> typing.Any:
        return [str(answer) for answer in self.answers]

    @gl.public.view
    def get_criteria(self) -> str:
        return CRITERIA


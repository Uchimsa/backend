from dataclasses import dataclass


@dataclass
class EvalResult:
    score: float
    explanation: str


async def evaluate_task_answer(
    question_text: str,
    reference_answer: str | None,
    user_answer: str,
) -> EvalResult:
    """Mock AI evaluation — replace with real Anthropic API call."""
    return EvalResult(
        score=0.5,
        explanation="Оценка пока недоступна. Сравните ваш ответ с эталонным решением.",
    )

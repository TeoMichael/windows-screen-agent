from windows_screen_agent.prompt import build_answer_developer_prompt


def test_answer_prompt_allows_practice_quizzes_but_refuses_restricted_contexts():
    prompt = build_answer_developer_prompt()

    assert "Practice, sample, and local sandbox quizzes are allowed" in prompt
    assert "Do not refuse merely because the page contains quiz or test wording" in prompt
    assert "graded, proctored, live, honor-code-bound" in prompt

MAX_TURNS = 5

# Rolling short-term conversation history (last MAX_TURNS exchanges).
history: list[dict[str, str]] = []


def update_history(user_msg: str, assistant_msg: str) -> None:
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})
    del history[: -MAX_TURNS * 2]

# Short-term conversation memory shared across requests.
# Stored in-process — clears on server restart, which is fine for a prototype.

MAX_TURNS = 5  # number of user/assistant exchanges to keep

history: list[dict[str, str]] = []


def update_history(user_msg: str, assistant_msg: str) -> None:
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})
    # each turn is 2 entries (user + assistant), so trim by MAX_TURNS * 2
    del history[: -MAX_TURNS * 2]

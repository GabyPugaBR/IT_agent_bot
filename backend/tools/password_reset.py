from tools.user_db import find_user_entry, generate_temporary_password, get_password_policy, load_users, save_users


def reset_password(username: str) -> dict:
    users = load_users()
    entry = find_user_entry(username)

    if not entry:
        return {
            "status": "error",
            "message": "User not found.",
        }

    user_key, user = entry
    record_username = user.get("username", user_key)
    role = user["role"]
    temporary_password = generate_temporary_password(role)
    policy = get_password_policy(role)

    user["password"] = temporary_password
    user["failed_attempts"] = 0
    user["status"] = "active"
    user["must_change_password"] = True
    users[user_key] = user
    save_users(users)

    return {
        "status": "success",
        "message": (
            f"Password reset successful for {record_username}. "
            f"Temporary password: {temporary_password}"
        ),
        "username": record_username,
        "temporary_password": temporary_password,
        "must_change_password": True,
        "password_policy": policy,
    }

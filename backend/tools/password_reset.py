from tools.user_db import find_user, generate_temporary_password, get_password_policy, load_users, save_users


def reset_password(username: str) -> dict:
    users = load_users()
    normalized_username = username.lower()
    user = users.get(normalized_username)

    if not user:
        return {
            "status": "error",
            "message": "User not found.",
        }

    role = user["role"]
    temporary_password = generate_temporary_password(role)
    policy = get_password_policy(role)

    user["password"] = temporary_password
    user["failed_attempts"] = 0
    user["status"] = "active"
    user["must_change_password"] = True
    users[normalized_username] = user
    save_users(users)

    return {
        "status": "success",
        "message": (
            f"Password reset successful for {normalized_username}. "
            f"Temporary password: {temporary_password}"
        ),
        "username": normalized_username,
        "temporary_password": temporary_password,
        "must_change_password": True,
        "password_policy": policy,
    }

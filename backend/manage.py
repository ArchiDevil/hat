import argparse
import getpass
import re

from app.db import get_db
from app.models import UserRole
from app.schema import User
from app.security import hash_password


def add_user():
    print("Adding a new user...")
    username = input("Enter username: ")

    email = input("Enter email: ")
    if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
        print("Invalid email address!")
        return

    role = UserRole(input(f"Enter role {UserRole.get_values()}: ")).value
    if role not in UserRole.get_values():
        print(f"{role} is an invalid role!")

    password = getpass.getpass("Enter password (at least 8 symbols): ")
    if len(password) < 8:
        print("Password must be at least 8 symbols long!")

    password = hash_password(password)

    session = next(get_db())
    session.add(
        User(
            username=username, email=email, role=role, password=password, disabled=False
        )
    )
    session.commit()

    print(f"{username} added!")


def main():
    parser = argparse.ArgumentParser(description="HAT manager script")
    parser.add_argument("command", help="Command to execute", choices=["add-user"])
    args = parser.parse_args()

    if args.command == "add-user":
        add_user()


if __name__ == "__main__":
    main()

"""Admin commands.

    python -m app.cli make-admin user@example.com
"""

import argparse
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import User


def make_admin(email: str) -> int:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None:
            print(f"No user with email {email}")
            return 1
        user.role = "admin"
        db.commit()
        print(f"{user.email} is now an admin")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("make-admin", help="Give an existing user the admin role")
    admin.add_argument("email")

    args = parser.parse_args(argv)
    if args.command == "make-admin":
        return make_admin(args.email)
    return 1


if __name__ == "__main__":
    sys.exit(main())

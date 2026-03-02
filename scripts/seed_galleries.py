import argparse

from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.models import Gallery


def parse_gallery(value: str) -> tuple[str, str, str]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "Expected format source_type:source_key:display_name "
            "(example: reddit:python:Python Subreddit)"
        )
    return parts[0], parts[1], parts[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed tracked galleries/sources")
    parser.add_argument(
        "--gallery",
        action="append",
        required=True,
        help="source_type:source_key:display_name (repeatable)",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        created = 0
        for raw in args.gallery:
            source_type, source_key, display_name = parse_gallery(raw)
            exists = db.execute(
                select(Gallery).where(
                    Gallery.source_type == source_type,
                    Gallery.source_key == source_key,
                )
            ).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Gallery(
                    source_type=source_type,
                    source_key=source_key,
                    display_name=display_name,
                    enabled=True,
                )
            )
            created += 1
        db.commit()
    finally:
        db.close()

    print(f"seed complete created={created}")


if __name__ == "__main__":
    main()


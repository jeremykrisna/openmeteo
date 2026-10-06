import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


load_dotenv()


SCHEMAS = ["raw", "staging", "mart"]

OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "DATA_DICTIONARY.md"
)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def get_columns(connection):
    query = """
        SELECT
            table_schema,
            table_name,
            column_name,
            ordinal_position,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = ANY(%s)
        ORDER BY
            table_schema,
            table_name,
            ordinal_position;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (SCHEMAS,))
        return cursor.fetchall()


def generate_markdown(rows):
    lines = []

    lines.append("# Data Dictionary")
    lines.append("")
    lines.append(
        "Automatically generated from PostgreSQL metadata."
    )
    lines.append("")

    current_table = None

    for row in rows:
        (
            schema,
            table,
            column,
            ordinal_position,
            data_type,
            is_nullable,
        ) = row

        table_key = f"{schema}.{table}"

        if table_key != current_table:
            current_table = table_key

            lines.append(f"## `{table_key}`")
            lines.append("")
            lines.append(
                "| Column | Data Type | Nullable | Description |"
            )
            lines.append(
                "|---|---|---|---|"
            )

        nullable = "YES" if is_nullable == "YES" else "NO"

        lines.append(
            f"| `{column}` | `{data_type}` | "
            f"{nullable} | |"
        )

        # Add blank line after each table.
        next_table_index = rows.index(row) + 1

        if next_table_index < len(rows):
            next_schema = rows[next_table_index][0]
            next_table = rows[next_table_index][1]

            if f"{next_schema}.{next_table}" != current_table:
                lines.append("")

    return "\n".join(lines)


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection()

    try:
        rows = get_columns(connection)

        if not rows:
            print("No tables found.")
            return

        markdown = generate_markdown(rows)

        OUTPUT_FILE.write_text(
            markdown,
            encoding="utf-8",
        )

        print(
            f"Data Dictionary generated successfully: "
            f"{OUTPUT_FILE}"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
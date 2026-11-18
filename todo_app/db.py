import sqlite3
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path


# 실행 위치와 관계없이 db.py 옆에 데이터베이스를 저장합니다.
DB_PATH = Path(__file__).resolve().with_name("todo.db")


@contextmanager
def _connect(db_path: str | Path):
    """작업이 성공하면 커밋하고, 예외가 나면 롤백한 뒤 연결을 닫습니다."""
    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            yield connection


def init_db(db_path: str | Path = DB_PATH) -> None:
    """앱을 시작할 때 호출해 할 일 테이블을 준비합니다."""
    with _connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                description TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL,
                priority TEXT NOT NULL CHECK (priority IN ('높음', '보통', '낮음')),
                category TEXT NOT NULL CHECK (category IN ('업무', '개인', '공부', '기타')),
                is_done INTEGER NOT NULL DEFAULT 0 CHECK (is_done IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def add_todo(
    title: str,
    description: str,
    due_date: date,
    priority: str,
    category: str,
    *,
    db_path: str | Path = DB_PATH,
) -> int:
    """할 일을 추가하고 새 항목의 ID를 반환합니다."""
    with _connect(db_path) as connection:
        # 날짜는 YYYY-MM-DD로 저장하고, 입력값은 SQL과 분리해 전달합니다.
        cursor = connection.execute(
            """
            INSERT INTO todos (title, description, due_date, priority, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title.strip(), description, due_date.isoformat(), priority, category),
        )
        return cursor.lastrowid


def list_todos(db_path: str | Path = DB_PATH) -> list[dict]:
    """전체 할 일을 오래된 등록순으로 반환합니다."""
    with _connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM todos ORDER BY id").fetchall()
        return [dict(row) for row in rows]


def update_todo(
    todo_id: int,
    title: str,
    description: str,
    due_date: date,
    priority: str,
    category: str,
    *,
    db_path: str | Path = DB_PATH,
) -> bool:
    """할 일의 입력 항목을 수정하고 대상이 있었는지 반환합니다."""
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE todos
            SET title = ?, description = ?, due_date = ?, priority = ?, category = ?
            WHERE id = ?
            """,
            (title.strip(), description, due_date.isoformat(), priority, category, todo_id),
        )
        return cursor.rowcount == 1


def set_todo_done(
    todo_id: int, is_done: bool, *, db_path: str | Path = DB_PATH
) -> bool:
    """완료 상태를 저장하고 대상이 있었는지 반환합니다."""
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "UPDATE todos SET is_done = ? WHERE id = ?", (int(is_done), todo_id)
        )
        return cursor.rowcount == 1


def delete_todo(todo_id: int, *, db_path: str | Path = DB_PATH) -> bool:
    """할 일을 삭제하고 대상이 있었는지 반환합니다."""
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        return cursor.rowcount == 1

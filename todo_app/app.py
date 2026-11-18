from datetime import date
from html import escape

import streamlit as st

from db import add_todo, delete_todo, init_db, list_todos, set_todo_done, update_todo


PRIORITIES = ("높음", "보통", "낮음")
CATEGORIES = ("업무", "개인", "공부", "기타")


def is_overdue(task, today):
    return not task["is_done"] and date.fromisoformat(task["due_date"]) < today


def show_dashboard(tasks, today):
    st.header("할 일 현황")
    total = len(tasks)
    done = sum(task["is_done"] for task in tasks)
    overdue = sum(is_overdue(task, today) for task in tasks)

    metrics = st.columns(4)
    metrics[0].metric("전체", total)
    metrics[1].metric("완료", done)
    metrics[2].metric("진행 중", total - done)
    metrics[3].metric("기한 초과", overdue)
    rate = done / total if total else 0.0
    st.progress(rate, text=f"완료율 {rate:.0%}")


def filter_and_sort(tasks):
    with st.sidebar:
        st.header("필터 및 정렬")
        status = st.selectbox("상태", ("전체", "진행 중", "완료"))
        categories = st.multiselect("카테고리", CATEGORIES)
        priorities = st.multiselect("우선순위", PRIORITIES)
        order = st.selectbox("정렬", ("마감일순", "우선순위순", "등록순"))
        keyword = st.text_input("제목 검색").strip().casefold()

    # 선택 항목이 없는 다중 선택 필터는 모든 값을 포함합니다.
    visible = [
        task
        for task in tasks
        if (status == "전체" or bool(task["is_done"]) == (status == "완료"))
        and (not categories or task["category"] in categories)
        and (not priorities or task["priority"] in priorities)
        and keyword in task["title"].casefold()
    ]

    if order == "마감일순":
        # DB의 YYYY-MM-DD 문자열은 날짜와 같은 순서로 정렬됩니다.
        visible.sort(key=lambda task: task["due_date"])
    elif order == "우선순위순":
        visible.sort(key=lambda task: PRIORITIES.index(task["priority"]))
    return visible  # 등록순과 정렬 기준이 같은 항목은 DB 조회 순서를 따릅니다.


def task_fields(today, task=None):
    """추가와 수정 폼에서 사용하는 공통 입력 항목입니다."""
    task = task or {}
    title = st.text_input("제목 (필수)", task.get("title", "")).strip()
    description = st.text_area("설명 (선택)", task.get("description", "")).strip()
    due_date = date.fromisoformat(task["due_date"]) if task else today

    date_col, priority_col, category_col = st.columns(3)
    due_date = date_col.date_input("마감일", value=due_date)
    priority = priority_col.selectbox(
        "우선순위", PRIORITIES, index=PRIORITIES.index(task.get("priority", "보통"))
    )
    category = category_col.selectbox(
        "카테고리", CATEGORIES, index=CATEGORIES.index(task.get("category", "기타"))
    )
    return (title, description, due_date, priority, category)


def show_add_form(today):
    st.header("할 일 추가")
    # 저장에 성공한 경우에만 폼 키를 변경해 입력을 초기화합니다.
    with st.form(f"add_{st.session_state.add_form_number}"):
        fields = task_fields(today)
        if st.form_submit_button("추가", type="primary"):
            if not fields[0]:
                st.warning("제목을 입력해 주세요.")
                return
            add_todo(*fields)
            st.session_state.add_form_number += 1
            st.rerun()


def show_edit_form(task, today):
    st.header("할 일 수정")
    with st.form(f"edit_{task['id']}"):
        fields = task_fields(today, task)
        save_col, cancel_col = st.columns(2)
        save = save_col.form_submit_button("저장", type="primary")
        cancel = cancel_col.form_submit_button("취소")

        if save:
            if not fields[0]:
                st.warning("제목을 입력해 주세요.")
                return
            update_todo(task["id"], *fields)

        if save or cancel:
            st.session_state.editing_id = None
            st.rerun()


def save_done(todo_id, checkbox_key):
    # 체크박스 콜백은 화면을 다시 그리기 전에 SQLite에 상태를 저장합니다.
    set_todo_done(todo_id, st.session_state[checkbox_key])


def show_task_list(tasks, today):
    st.header("할 일 목록")
    if not tasks:
        st.info("표시할 할 일이 없습니다.")

    for task in tasks:
        todo_id = task["id"]
        done = bool(task["is_done"])
        overdue = is_overdue(task, today)

        with st.container(border=True):
            # 사용자 입력을 HTML 태그로 처리되지 않도록 이스케이프합니다.
            title = escape(task["title"])
            if done:
                title = f"<s>{title}</s>"
            elif overdue:
                title = f'<span style="color:#dc3545">{title} · 기한 초과</span>'
            st.html(f'<p style="overflow-wrap:anywhere"><strong>{title}</strong></p>')

            if task["description"]:
                st.text(task["description"])
            st.caption(f"마감일 {task['due_date']} · 우선순위 {task['priority']} · {task['category']}")

            status_col, edit_col, delete_col = st.columns([2, 1, 1])
            checkbox_key = f"done_{todo_id}_{int(done)}"
            status_col.checkbox(
                "완료", value=done, key=checkbox_key,
                on_change=save_done, args=(todo_id, checkbox_key),
            )
            if edit_col.button("수정", key=f"edit_button_{todo_id}"):
                st.session_state.editing_id = todo_id
                st.rerun()
            if delete_col.button("삭제", key=f"delete_{todo_id}"):
                delete_todo(todo_id)
                if st.session_state.editing_id == todo_id:
                    st.session_state.editing_id = None
                st.rerun()


def main():
    st.set_page_config(page_title="할 일 관리", layout="wide")
    st.title("할 일 관리")
    st.session_state.setdefault("editing_id", None)
    st.session_state.setdefault("add_form_number", 0)

    init_db()
    tasks = list_todos()
    today = date.today()
    visible_tasks = filter_and_sort(tasks)
    show_dashboard(tasks, today)
    show_add_form(today)

    # 필터 조건이 바뀌어도 수정 중인 항목을 전체 목록에서 찾습니다.
    editing_id = st.session_state.editing_id
    if editing_id is not None:
        task = next((task for task in tasks if task["id"] == editing_id), None)
        if task is None:
            st.session_state.editing_id = None
            st.warning("수정할 할 일이 삭제되었습니다.")
        else:
            show_edit_form(task, today)

    show_task_list(visible_tasks, today)


if __name__ == "__main__":
    main()

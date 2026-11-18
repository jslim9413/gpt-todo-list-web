from datetime import date
from uuid import uuid4

import streamlit as st


PRIORITIES = ("높음", "보통", "낮음")
CATEGORIES = ("업무", "개인", "공부", "기타")


def task_fields(task):
    """추가 폼과 수정 폼에서 같은 입력 항목을 사용합니다."""
    title = st.text_input("제목 (필수)", value=task.get("title", ""))
    description = st.text_area("설명 (선택)", value=task.get("description", ""))

    date_column, priority_column, category_column = st.columns(3)
    with date_column:
        due_date = st.date_input("마감일", value=task.get("due_date", date.today()))
    with priority_column:
        priority = st.selectbox(
            "우선순위", PRIORITIES, index=PRIORITIES.index(task.get("priority", "보통"))
        )
    with category_column:
        category = st.selectbox(
            "카테고리", CATEGORIES, index=CATEGORIES.index(task.get("category", "기타"))
        )

    return {
        "title": title.strip(),
        "description": description.strip(),
        "due_date": due_date,
        "priority": priority,
        "category": category,
    }


def show_add_form(tasks):
    st.header("할 일 추가")
    # 추가에 성공했을 때만 폼 키를 바꿔 입력값을 초기화합니다.
    with st.form(f"add_{st.session_state.add_form_number}"):
        fields = task_fields({})
        if st.form_submit_button("추가", type="primary"):
            if not fields["title"]:
                st.warning("제목을 입력해 주세요.")
                return

            task_id = uuid4().hex
            tasks[task_id] = {**fields, "completed": False}
            st.session_state.add_form_number += 1
            st.rerun()


def show_edit_form(task_id, task):
    with st.form(f"edit_form_{task_id}"):
        fields = task_fields(task)
        save_column, cancel_column = st.columns(2)
        save = save_column.form_submit_button("저장", type="primary")
        cancel = cancel_column.form_submit_button("취소")

        if save:
            if not fields["title"]:
                st.warning("제목을 입력해 주세요.")
                return
            task.update(fields)

        if save or cancel:
            st.session_state.editing_task_id = None
            st.rerun()


def show_task_list(tasks):
    st.header("할 일 목록")
    if not tasks:
        st.info("등록된 할 일이 없습니다.")

    for task_id, task in tasks.items():
        with st.container(border=True):
            st.text(task["title"])
            if task["description"]:
                st.text(task["description"])
            st.caption(
                f"마감일 {task['due_date']:%Y-%m-%d} · "
                f"우선순위 {task['priority']} · {task['category']}"
            )

            # 제목이 같은 할 일도 고유 ID로 각 위젯을 구분합니다.
            status_column, edit_column, delete_column = st.columns([2, 1, 1])
            task["completed"] = status_column.checkbox(
                "완료", value=task["completed"], key=f"done_{task_id}"
            )
            if edit_column.button("수정", key=f"edit_{task_id}"):
                st.session_state.editing_task_id = task_id
                st.rerun()
            if delete_column.button("삭제", key=f"delete_{task_id}"):
                del tasks[task_id]
                if st.session_state.editing_task_id == task_id:
                    st.session_state.editing_task_id = None
                st.rerun()

            if st.session_state.editing_task_id == task_id:
                show_edit_form(task_id, task)


def main():
    st.set_page_config(page_title="할 일 관리")
    st.title("할 일 관리")

    # Streamlit은 입력이 바뀔 때 스크립트를 다시 실행하므로 상태를 세션에 보관합니다.
    st.session_state.setdefault("tasks", {})
    st.session_state.setdefault("add_form_number", 0)
    st.session_state.setdefault("editing_task_id", None)

    show_add_form(st.session_state.tasks)
    show_task_list(st.session_state.tasks)


if __name__ == "__main__":
    main()

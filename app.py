import streamlit as st
import time
import uuid
import sqlite3
import json

DB_NAME = "agents.db"

# --- Классы для представления данных (остаются без изменений) ---
class Agent:
    """Класс для представления одного агента."""
    def __init__(self, name, prompt, model, tools, agent_id=None):
        self.id = agent_id if agent_id else str(uuid.uuid4())
        self.name = name
        self.prompt = prompt
        self.model = model
        self.tools = tools

    def simulate_work(self):
        """Метод для симуляции работы агента."""
        time.sleep(1) # Имитация задержки
        tools_used = f"с инструментами: {', '.join(self.tools)}" if self.tools else "без инструментов."
        return f"**{self.name} ({self.model}):**\n> {self.prompt}\n\n*Задача выполнена {tools_used}*"

# --- Функции для работы с базой данных SQLite ---

def init_db():
    """Инициализирует базу данных и создает таблицу, если она не существует."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            model TEXT NOT NULL,
            tools TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_agents_from_db():
    """Загружает всех агентов из базы данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, prompt, model, tools FROM agents")
    agents = []
    for row in cursor.fetchall():
        tools_list = json.loads(row[4]) if row[4] else []
        agents.append(Agent(agent_id=row[0], name=row[1], prompt=row[2], model=row[3], tools=tools_list))
    conn.close()
    return agents

def save_agent_to_db(agent):
    """Сохраняет одного агента в базу данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    tools_json = json.dumps(agent.tools)
    cursor.execute("INSERT INTO agents (id, name, prompt, model, tools) VALUES (?, ?, ?, ?, ?)",
                   (agent.id, agent.name, agent.prompt, agent.model, tools_json))
    conn.commit()
    conn.close()

def delete_agent_from_db(agent_id):
    """Удаляет агента из базы данных по его ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    conn.commit()
    conn.close()


# --- Функции-обработчики (Callbacks) ---

def add_agent():
    """Добавляет нового агента в session_state и в БД."""
    name = st.session_state.agent_name_input
    prompt = st.session_state.agent_prompt_input

    if not name or not prompt:
        st.toast("🔴 Имя агента и промпт не могут быть пустыми.", icon="error")
        return

    new_agent = Agent(
        name,
        prompt,
        st.session_state.agent_model_input,
        st.session_state.agent_tools_input
    )
    st.session_state.agents.append(new_agent)
    save_agent_to_db(new_agent) # Сохраняем в БД
    st.toast(f"✅ Агент '{name}' успешно создан и сохранен!", icon="success")
    st.session_state.agent_name_input = ""
    st.session_state.agent_prompt_input = ""

def delete_agent(agent_id):
    """Удаляет агента из session_state и из БД."""
    agent_to_delete = next((agent for agent in st.session_state.agents if agent.id == agent_id), None)
    if agent_to_delete:
        st.session_state.agents.remove(agent_to_delete)
        delete_agent_from_db(agent_id) # Удаляем из БД
        st.toast(f"🗑️ Агент '{agent_to_delete.name}' удален.", icon="info")

# Функции симуляции остаются без изменений
def run_team_simulation():
    selected_agent_names = st.session_state.team_multiselect
    if not selected_agent_names:
        st.toast("⚠️ Выберите хотя бы одного агента для симуляции.", icon="warning")
        return
    st.session_state.simulation_log.append("--- Начало новой командной симуляции ---")
    for name in selected_agent_names:
        agent = next((a for a in st.session_state.agents if a.name == name), None)
        if agent:
            with st.spinner(f"Агент {agent.name} в работе..."):
                result = agent.simulate_work()
            st.session_state.simulation_log.append(result)
    st.session_state.simulation_log.append("--- Командная симуляция завершена ---")
    st.toast("🚀 Командная симуляция завершена!", icon="🚀")

def clear_log():
    st.session_state.simulation_log = []
    st.toast("🧹 Лог симуляции очищен.", icon="info")


# --- Основная функция, определяющая UI ---
def agent_and_team_manager():
    st.set_page_config(page_title="Менеджер Агентов", layout="wide")

    # Инициализация состояния сессии из БД при первом запуске
    if "agents" not in st.session_state:
        st.session_state.agents = load_agents_from_db()
    if "simulation_log" not in st.session_state:
        st.session_state.simulation_log = []

    # Левая панель
    with st.sidebar:
        st.header("Создать агента")
        MODELS = ["gemini-1.5-pro", "gemini-1.5-flash", "gpt-4o", "gpt-4-turbo", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
        TOOLS = ["Поиск в интернете", "Калькулятор", "Генерация изображений", "Интерпретатор Python", "Запрос к БД (SQL)", "Работа с файлами", "API погоды", "API календаря", "Отправка Email"]
        st.text_input("Имя агента", key="agent_name_input")
        st.text_area("Промпт (инструкция)", key="agent_prompt_input", height=150)
        st.selectbox("Модель", MODELS, key="agent_model_input")
        st.multiselect("Инструменты", TOOLS, key="agent_tools_input")
        st.button("Добавить агента", on_click=add_agent, type="primary", use_container_width=True)

    # Основная область
    st.title("🤖 Менеджер Агентов")
    tab1, tab2 = st.tabs(["Управление Агентами", "Симуляция Работы"])

    with tab1:
        st.subheader("Список доступных агентов")
        if not st.session_state.agents:
            st.info("Пока не создано ни одного агента. Начните с формы слева.", icon="👈")
        else:
            num_columns = min(len(st.session_state.agents), 3)
            cols = st.columns(num_columns) if num_columns > 0 else [st]
            for i, agent in enumerate(st.session_state.agents):
                with cols[i % num_columns]:
                    with st.container(border=True):
                        st.markdown(f"#### {agent.name}")
                        st.caption(f"Модель: {agent.model}")
                        tools_str = ", ".join(agent.tools) if agent.tools else "Нет"
                        st.caption(f"Инструменты: {tools_str}")
                        with st.expander("Показать промпт"):
                            st.text(agent.prompt)
                        st.button("Удалить", key=f"del_{agent.id}", on_click=delete_agent, args=[agent.id], use_container_width=True)

    with tab2:
        # ... (код этой вкладки не изменился)
        st.subheader("Запуск команды")
        if not st.session_state.agents:
            st.warning("Сначала создайте агентов на вкладке 'Управление Агентами'.")
        else:
            agent_names = [agent.name for agent in st.session_state.agents]
            st.multiselect("Выберите агентов для командной работы", options=agent_names, key="team_multiselect")
            col1, col2 = st.columns(2)
            with col1:
                st.button("🚀 Запустить симуляцию", on_click=run_team_simulation, use_container_width=True, type="primary")
            with col2:
                st.button("🧹 Очистить лог", on_click=clear_log, use_container_width=True)
            st.subheader("Лог выполнения")
            with st.container(height=400, border=True):
                if not st.session_state.simulation_log:
                    st.info("Здесь будет отображаться результат работы агентов...")
                else:
                    for entry in reversed(st.session_state.simulation_log):
                        st.markdown(entry)
                        st.divider()

# --- ЗАПУСК ПРИЛОЖЕНИЯ ---
if __name__ == "__main__":
    init_db() # Убедимся, что БД и таблица существуют
    agent_and_team_manager()

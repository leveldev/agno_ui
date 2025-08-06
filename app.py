import streamlit as st
import time
import uuid

# --- Классы для представления данных (остаются без изменений) ---
class Agent:
    """Класс для представления одного агента."""
    def __init__(self, name, prompt, model, tools):
        self.id = str(uuid.uuid4())
        self.name = name
        self.prompt = prompt
        self.model = model
        self.tools = tools

    def simulate_work(self):
        """Метод для симуляции работы агента."""
        time.sleep(1) # Имитация задержки
        tools_used = f"с инструментами: {', '.join(self.tools)}" if self.tools else "без инструментов."
        return f"**{self.name} ({self.model}):**\n> {self.prompt}\n\n*Задача выполнена {tools_used}*"

# --- Инициализация состояния сессии (ПРАВИЛЬНЫЙ СПОСОБ) ---
# st.session_state - это специальный объект Streamlit для хранения данных
# между взаимодействиями пользователя.
if "agents" not in st.session_state:
    st.session_state.agents = []
if "simulation_log" not in st.session_state:
    st.session_state.simulation_log = []

# --- Функции-обработчики (Callbacks) ---
# Теперь они работают с st.session_state

def add_agent():
    """Добавляет нового агента, используя данные из session_state."""
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
    st.toast(f"✅ Агент '{name}' успешно создан!", icon="success")
    # Очистка полей ввода после добавления
    st.session_state.agent_name_input = ""
    st.session_state.agent_prompt_input = ""


def delete_agent(agent_id):
    """Удаляет агента по его ID."""
    agent_to_delete = next((agent for agent in st.session_state.agents if agent.id == agent_id), None)
    if agent_to_delete:
        st.session_state.agents.remove(agent_to_delete)
        st.toast(f"🗑️ Агент '{agent_to_delete.name}' удален.", icon="info")


def run_team_simulation():
    """Запускает симуляцию работы для выбранной команды."""
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
    """Очищает лог симуляции."""
    st.session_state.simulation_log = []
    st.toast("🧹 Лог симуляции очищен.", icon="info")


# --- Основная функция, определяющая UI ---
def agent_and_team_manager():
    """Главная функция, которая рендерит весь UI."""
    st.set_page_config(page_title="Менеджер Агентов", layout="wide")

    # --- Левая панель для создания агентов ---
    with st.sidebar:
        st.header("Создать агента")

        # Используем `key`, чтобы связать виджеты с session_state
        st.text_input("Имя агента", key="agent_name_input")
        st.text_area("Промпт (инструкция)", key="agent_prompt_input", height=150)
        st.selectbox("Модель", ["gemini-1.5-pro", "gpt-4o", "claude-3-opus"], key="agent_model_input")
        st.multiselect("Инструменты", ["Поиск", "Калькулятор", "Генерация изображений"], key="agent_tools_input")

        st.button("Добавить агента", on_click=add_agent, type="primary", use_container_width=True)

    # --- Основная область с вкладками ---
    st.title("🤖 Менеджер Агентов")

    tab1, tab2 = st.tabs(["Управление Агентами", "Симуляция Работы"])

    with tab1:
        st.subheader("Список доступных агентов")
        if not st.session_state.agents:
            st.info("Пока не создано ни одного агента. Начните с формы слева.", icon="👈")
        else:
            cols = st.columns(3)
            for i, agent in enumerate(st.session_state.agents):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"#### {agent.name}")
                        st.caption(f"Модель: {agent.model}")
                        tools_str = ", ".join(agent.tools) if agent.tools else "Нет"
                        st.caption(f"Инструменты: {tools_str}")
                        with st.expander("Показать промпт"):
                            st.text(agent.prompt)
                        st.button("Удалить", key=f"del_{agent.id}", on_click=delete_agent, args=[agent.id], use_container_width=True)

    with tab2:
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

            # Область для вывода лога симуляции
            st.subheader("Лог выполнения")
            with st.container(height=400, border=True):
                if not st.session_state.simulation_log:
                    st.info("Здесь будет отображаться результат работы агентов...")
                else:
                    for entry in reversed(st.session_state.simulation_log):
                        st.markdown(entry)
                        st.divider()

# --- ВЫЗОВ ГЛАВНОЙ ФУНКЦИИ ---
# Эта строка ОБЯЗАТЕЛЬНА для работы на Streamlit Cloud.
# Она запускает отрисовку всего интерфейса.
agent_and_team_manager()

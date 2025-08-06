import agno
import time
import uuid

# --- Классы для представления данных ---

class Agent:
    """
    Класс для представления одного агента.
    Использование класса вместо словаря делает код чище и позволяет
    добавлять методы (поведение) к нашим данным.
    """
    def __init__(self, name, prompt, model, tools):
        self.id = str(uuid.uuid4()) # Уникальный ID для каждого агента
        self.name = name
        self.prompt = prompt
        self.model = model
        self.tools = tools

    def simulate_work(self):
        """
        Метод для симуляции работы агента.
        В реальном приложении здесь был бы вызов к API LLM.
        Мы же просто вернем форматированный ответ.
        """
        print(f"Симуляция работы для {self.name}...")
        time.sleep(1) # Имитация задержки на обработку
        tools_used = f"с инструментами: {', '.join(self.tools)}" if self.tools else "без инструментов."
        return f"**{self.name} ({self.model}):**\n> {self.prompt}\n\n*Задача выполнена {tools_used}*"

# --- Управление состоянием ---
# Используем тот же подход с глобальным словарем для хранения состояния сессии.
if 'state' not in globals():
    state = {
        "agents": [],
        "last_notification": None,
        "simulation_log": []
    }

# --- Функции-обработчики (Callbacks) ---

def add_agent(name, prompt, model, tools):
    """Добавляет нового агента в список."""
    if not name or not prompt:
        state["last_notification"] = ("error", "Имя агента и промпт не могут быть пустыми.")
        return

    new_agent = Agent(name, prompt, model, tools)
    state["agents"].append(new_agent)
    state["last_notification"] = ("success", f"Агент '{name}' успешно создан!")
    print(f"Добавлен агент: {name}")

def delete_agent(agent_id):
    """Удаляет агента по его ID."""
    agent_to_delete = next((agent for agent in state["agents"] if agent.id == agent_id), None)
    if agent_to_delete:
        state["agents"].remove(agent_to_delete)
        state["last_notification"] = ("info", f"Агент '{agent_to_delete.name}' удален.")
        print(f"Удален агент: {agent_to_delete.name}")

def run_team_simulation(agent_names):
    """Запускает симуляцию работы для выбранной команды агентов."""
    if not agent_names:
        state["last_notification"] = ("warning", "Выберите хотя бы одного агента для симуляции.")
        return

    state["simulation_log"].append("--- Начало новой командной симуляции ---")
    for name in agent_names:
        agent = next((a for a in state["agents"] if a.name == name), None)
        if agent:
            result = agent.simulate_work()
            state["simulation_log"].append(result)
    state["simulation_log"].append("--- Командная симуляция завершена ---")

def clear_log():
    """Очищает лог симуляции."""
    state["simulation_log"] = []
    state["last_notification"] = ("info", "Лог симуляции очищен.")


# --- Основная функция, определяющая UI ---

def agent_and_team_manager():
    """Главная функция, которая рендерит весь UI."""

    # --- Левая панель для создания агентов и уведомлений ---
    with agno.Sidebar():
        agno.Header("Создать агента")

        # Показываем уведомление, если оно есть
        if state["last_notification"]:
            status, message = state["last_notification"]
            agno.Alert(message, status=status)
            state["last_notification"] = None # Сбрасываем уведомление после показа

        # Поля для ввода
        agent_name = agno.Textbox(label="Имя агента")
        agent_prompt = agno.Textbox(label="Промпт (инструкция)", lines=5)
        agent_model = agno.Select(label="Модель", options=["gemini-1.5-pro", "gpt-4o", "claude-3-opus"])
        agent_tools = agno.Checkbox(label="Инструменты", options=["Поиск", "Калькулятор", "Генерация изображений"])

        agno.Button("Добавить агента", target=add_agent, args=[agent_name, agent_prompt, agent_model, agent_tools])

    # --- Основная область с вкладками ---
    agno.Header("Менеджер Агентов")

    with agno.Tabs(options=["Управление Агентами", "Симуляция Работы"]) as tab:
        if tab == "Управление Агентами":
            agno.Subheader("Список доступных агентов")
            if not state["agents"]:
                agno.Text("Пока не создано ни одного агента. Начните с формы слева.")
            else:
                # Используем колонки для более аккуратного отображения
                with agno.Columns(3):
                    for agent in state["agents"]:
                        with agno.Card(border=True):
                            agno.Markdown(f"### {agent.name}")
                            agno.Text(f"Модель: {agent.model}")
                            tools_str = ", ".join(agent.tools) if agent.tools else "Нет"
                            agno.Text(f"Инструменты: {tools_str}")
                            with agno.Accordion("Показать промпт"):
                                agno.Text(agent.prompt)
                            # Кнопка удаления
                            agno.Button("Удалить", target=delete_agent, args=[agent.id], color="danger", icon="trash")

        elif tab == "Симуляция Работы":
            agno.Subheader("Запуск команды")
            if not state["agents"]:
                agno.Text("Сначала создайте агентов на вкладке 'Управление Агентами'.")
            else:
                agent_names = [agent.name for agent in state["agents"]]
                selected_agents = agno.Multiselect(label="Выберите агентов для командной работы", options=agent_names)

                with agno.Columns(2):
                    agno.Button("Запустить симуляцию", target=run_team_simulation, args=[selected_agents], icon="play")
                    agno.Button("Очистить лог", target=clear_log, icon="x-circle")

                # Область для вывода лога симуляции
                agno.Separator()
                agno.Subheader("Лог выполнения")
                with agno.Card():
                    if not state["simulation_log"]:
                        agno.Text("Здесь будет отображаться результат работы агентов...")
                    else:
                        # Выводим лог в обратном порядке для эффекта чата
                        for entry in reversed(state["simulation_log"]):
                            agno.Markdown(entry)
                            agno.Separator()

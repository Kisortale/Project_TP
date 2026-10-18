import pandas as pd
from pathlib import Path



GOOGLEtable = "1GyQ6IklpcoT7Sir6C7rNU9aNErDX1HWBg7Y1EK5T-nA"  # ВААААЖНО!!!!
ID = "739453176"


# Эти данные не меняем, в граф интерфейсе ЕСЛИСПРАШИВАЕМ ССЫЛКУ НА ТАБЛИЦУ, придётся писать программу что обрабатывает ссылку, т.к. нужно вычерпнуть из неё айдишники, они вот представлены на верху

# таблица сложная нет гаранта что код будет работать с другими, но работает для разных групп


def loadtable() -> pd.DataFrame:  # формирует прямую ссылку для экспорта Google Таблицы в формате CSV и возвращает полученную таблицу в виде объекта DataFrame
    url = (
        f"https://docs.google.com/spreadsheets/d/{GOOGLEtable}"
        f"/export?format=csv&gid={ID}"
    )
    return pd.read_csv(url, header=None, dtype=str, keep_default_na=False)


def findColumnes(table, groupnameKNT):  # ищет в таблице ячейку с названием нужной группы и возвращает индексы столбцов, где хранятся данные ггруппы (предмет, аудитория, корпус)
    for i in range(len(table)):
        for j in range(table.shape[1]):
            if table.iloc[i, j].strip() == groupnameKNT:
                return j, j + 1, j + 2
    raise ValueError(f"Группа '{groupnameKNT}' не найдена")


def parsing(table, groupnameKNT):  # Основная функция парсинга, извлекает из общей таблицы чистое расписание для конкретной группы
    columnSUBJECT, columnROOM, columnBUILDING = findColumnes(table, groupnameKNT)
    startRow = None
    for i in range(len(table)):
        if table.iloc[i, 1].strip() == "День":
            startRow = i + 1
            break
    if startRow is None:
        raise ValueError("Не найдено начало расписания")

    lessons = []
    currentday = ""
    for i in range(startRow, len(table)):
        day = table.iloc[i, 1].strip()
        time = table.iloc[i, 2].strip()
        if day:
            currentday = day
        if not time or ":" not in time or "-" not in time:
            continue
        subject = table.iloc[i, columnSUBJECT].strip()
        if not subject:
            continue
        lessons.append({
            "день": currentday,
            "время": time,
            "предмет": subject.replace("\n", " / "),
            "аудитория": table.iloc[i, columnROOM].strip().replace("\n", " / "),
            "корпус": table.iloc[i, columnBUILDING].strip().replace("\n", " / "),
        })
    return lessons


# Для красоты

def lessons2markdown(lessons, groupnameKNT):    # преобразует список словарей с данными о занятиях в готовую текстовую разметку Markdown, группируя их по дням недели и добавляя эмодзи
    if not lessons:
        return f"# 🍵 Расписание — {groupnameKNT}\n\n_Нет занятий._\n"

    emoji = {
        "Пн": "🍎 Понедельник",
        "Вт": "🍋 Вторник",
        "Ср": "🍈 Среда",
        "Чт": "🍑 Четверг",
        "Пт": "🍊 Пятница",
        "Сб": "🍇 Суббота",
        "Вс": "🌸 Воскресенье",
    }

    lines = [f"# 📚 Расписание — {groupnameKNT}", ""]

    by_day = {}
    for l in lessons:
        numDAY = l["день"]
        by_day.setdefault(numDAY, []).append(l)  # группируем занятия по дню

    for numDAY in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        if numDAY not in by_day:
            continue

        lines.append(f"## {emoji.get(numDAY, numDAY)}")
        lines.append("")
        lines.append("| ⏰ Время | (・ω・)つ📖 Предмет | 📌 Аудитория | 🧷 Корпус |")
        lines.append("|---|---|---|---|")

        for l in by_day[numDAY]: # перебирает только те занятия, которые относятся к текущему дню numDAY
            subject = format_subject(l["предмет"])
            room = format_room(l["аудитория"])
            building = format_building(l["корпус"])
            lines.append(
                f"| **{l['время']}** | {subject} | {room} | {building} |"
            )

        lines.append("")

    lines.append("---")
    lines.append(f"_Всего занятий: **{len(lessons)}**_")
    lines.append("")

    return "\n".join(lines) + "\n"


def format_subject(subject: str) -> str:  # для шрифта; форматирует название предмета для вывода в Markdown

    if " - " in subject:
        name, add = subject.split(" - ", 1)
        return f"**{name.strip()}** — _{add.strip()}_"
    return subject


def format_room(room: str) -> str:  # для онлайн; форматирует название аудитории для вывода в Markdown
    r = room.strip()
    if not r or r == "-":
        return "—"
    if "online" in r.lower():
        return "🌐 online"
    return f"`{r}`"


def format_building(building: str) -> str: # форматирует название корпуса для вывода в Markdown
    b = building.strip()
    if not b or b == "-":
        return "—"
    if b == "online":
        return "🌐 online"
    return b


# страшный блок кода закончился


def SAFEmarkdown(content: str, FILEpath: Path) -> None:  # сохраняет текст ( с гарантией целостности)
    FILEpath = Path(FILEpath)
    FILEpath.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILEpath.with_suffix(FILEpath.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(FILEpath)


def process(groupnameKNT: str, out_file: Path) -> Path:  # главная управляющая функция выполняет всю цепочку обработки (скачивает данные, превращает их в список, затем список превращается в текст, текст сохраняется в файл
    # Далее возвращает путь к сохранённому файлу
    table = loadtable()
    lessons = parsing(table, groupnameKNT)
    NEWformat = lessons2markdown(lessons, groupnameKNT)
    SAFEmarkdown(NEWformat, out_file)
    return Path(out_file)
import os, json
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

OUT = "report.pdf"
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=11))
story = []

def p(txt, style="BodyText"):
    story.append(Paragraph(txt, styles[style]))
    story.append(Spacer(1, 5))

def add_table(data, widths=None, fs=8):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#d9e5f2")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), fs),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

def main():
    if not os.path.exists("results.csv"):
        raise SystemExit("Сначала выполните python benchmark.py")
    df = pd.read_csv("results.csv")
    meta = json.load(open("environment.json", encoding="utf-8"))
    before = json.load(open("explain_before.json", encoding="utf-8"))
    after = json.load(open("explain_after.json", encoding="utf-8"))
    idx = json.load(open("index_stats.json", encoding="utf-8"))

    p("<b>ЛАБОРАТОРНАЯ РАБОТА №12</b>", "Title")
    p("<b>Разработка и запуск воспроизводимого benchmark-сценария</b>", "Heading2")
    p("Вариант 19 — Билеты. Фильтр: eventId + zone.")
    p("Выполнил(а): ________________________________<br/>Группа: ____________<br/>Проверил(а): ________________________________")
    p("Год: 2026")
    story.append(PageBreak())

    p("1. Цель работы", "Heading1")
    p("Разработать воспроизводимый эксперимент производительности NoSQL-подсистемы, измерить latency, throughput и ошибки, сравнить базовую и оптимизированную конфигурации.")
    p("2. Постановка задачи", "Heading1")
    p("Предметная область — система продажи билетов на мероприятия. Основной сценарий AP-01 — поиск билетов по идентификатору мероприятия и зоне. Сравниваются запросы без составного индекса и с индексом {eventId: 1, zone: 1}.")
    p("Гипотеза: составной индекс уменьшит объём просматриваемых документов и может снизить P95 для данного фильтра.")
    p("3. Окружение и данные", "Heading1")
    add_table([["Параметр", "Значение"],
               ["MongoDB", str(meta.get("mongodb_version"))],
               ["Python", str(meta.get("python_version"))],
               ["Количество документов", str(meta.get("documents"))],
               ["Seed", str(meta.get("seed"))],
               ["Запрос", str(meta.get("query"))],
               ["Запросов на повтор", str(meta.get("requests_per_repeat"))],
               ["Warm-up", str(meta.get("warmup_requests"))]])
    p("Данные синтетические. Каждый документ содержит ticketId, eventId, zone, title, seat, price и customerId. Генератор использует фиксированный seed=42.")
    story.append(PageBreak())

    p("4. Методика эксперимента", "Heading1")
    p("Для каждого режима использовались 1, 4 и 8 параллельных клиентов. Каждый режим повторялся три раза. Перед каждым измерением выполнялся отдельный прогрев из 40 запросов. В каждом измерении выполнялось 400 операций. Использован closed-loop подход.")
    p("5. Результаты измерений", "Heading1")
    table = [["Режим", "Клиенты", "RPS мед.", "P50, мс", "P95, мс", "P99, мс", "Ошибки %"]]
    for _, r in df.iterrows():
        table.append([str(r["mode"]), str(int(r["workers"])),
                      f'{r["RPS_median"]:.2f}', f'{r["P50_median_ms"]:.3f}',
                      f'{r["P95_median_ms"]:.3f}', f'{r["P99_median_ms"]:.3f}',
                      f'{r["error_rate_pct"]:.2f}'])
    add_table(table, fs=7)
    p("Значения в таблице получены из локального запуска benchmark.py; исходные повторы сохранены в raw_results.csv.")
    story.append(PageBreak())

    p("6. Анализ планов explain", "Heading1")
    for label, data in [("До создания индекса", before), ("После создания индекса", after)]:
        stats = data.get("executionStats", {})
        plan = data.get("queryPlanner", {}).get("winningPlan", {})
        p(f"<b>{label}</b>")
        add_table([["Показатель", "Значение"],
                   ["winningPlan", str(plan)[:900]],
                   ["totalDocsExamined", str(stats.get("totalDocsExamined"))],
                   ["totalKeysExamined", str(stats.get("totalKeysExamined"))],
                   ["executionTimeMillis", str(stats.get("executionTimeMillis"))]], fs=7)
    p("Вывод по explain следует делать совместно с результатами latency и throughput. Наличие IXSCAN само по себе не доказывает ускорение.")
    p("7. Графики", "Heading1")
    if os.path.exists("p95_by_clients.png"):
        story.append(Image("p95_by_clients.png", width=155*mm, height=95*mm))
    story.append(PageBreak())
    p("8. Throughput и дополнительные показатели", "Heading1")
    if os.path.exists("throughput_by_clients.png"):
        story.append(Image("throughput_by_clients.png", width=155*mm, height=95*mm))
    p(f"Размер индексов по collStats: {idx.get('totalIndexSize_bytes')} байт. Подробности сохранены в index_stats.json.")
    p("Стоимость записи", "Heading2")
    p("При вставке документов наличие индекса требует дополнительного обновления индексной структуры, поэтому запись может стать дороже. Для количественной оценки следует отдельно измерить одинаковую пакетную вставку с индексом и без него; данный основной read-benchmark не является измерением write latency.")
    story.append(PageBreak())

    p("9. Обсуждение и ограничения", "Heading1")
    p("При увеличении числа клиентов throughput может выйти на плато из-за ограничений CPU, дисковой подсистемы, памяти или пула соединений. P95 может расти из-за очередей и конкуренции за ресурсы. Closed-loop тест не поддерживает фиксированную интенсивность поступления запросов: скорость нагрузки зависит от времени ответа.")
    p("Эксперимент зависит от аппаратной конфигурации, фоновой нагрузки, версии MongoDB и состояния кэша. Результаты относятся только к использованному локальному стенду.")
    p("10. Вывод", "Heading1")
    p("В ходе работы создан воспроизводимый набор из синтетических данных для предметной области «Билеты», выполнено сравнение запроса по eventId и zone до и после добавления составного индекса. Итоговый вывод об эффективности индекса формируется по фактическим P95, throughput, ошибкам и показателям explain, приведённым выше.")
    p("Контрольные вопросы", "Heading1")
    answers = [
        "Throughput — число успешно выполненных запросов в секунду, число клиентов — параллельные исполнители.",
        "P95 показывает задержку для 95% успешных запросов и отражает хвост распределения.",
        "Explain executionStats возвращает план выполнения и статистику, включая число просмотренных документов и ключей, а также время выполнения.",
        "Warm-up уменьшает влияние начальных эффектов на измерения.",
        "Одновременное изменение индекса и объёма данных не позволяет отделить влияние каждого фактора.",
        "Плато throughput означает, что увеличение числа клиентов больше не повышает пропускную способность.",
        "Closed-loop нагрузка зависит от задержки ответа и не задаёт фиксированный поток RPS.",
        "Воспроизводимость обеспечивают фиксированный seed, одинаковые данные и запросы, версии ПО, конфигурация и сохранённые исходные результаты."
    ]
    for i, a in enumerate(answers, 1):
        p(f"{i}. {a}", "Small")

    doc = SimpleDocTemplate(OUT, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=16*mm, bottomMargin=16*mm)
    doc.build(story)
    print(f"Создан {OUT}")

if __name__ == "__main__":
    main()

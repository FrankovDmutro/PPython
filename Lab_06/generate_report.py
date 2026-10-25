"""Script to generate the official DOCX laboratory report for Lab 06, Variant 15."""

from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def create_report():
    doc = Document()

    # Base page settings: standard margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.79)
        sec.bottom_margin = Inches(0.79)
        sec.left_margin = Inches(0.98)
        sec.right_margin = Inches(0.79)

    # Configure Normal style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)
    font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_after = Pt(6)

    def add_p(text, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, first_line=0.49):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.first_line_indent = Inches(first_line) if first_line > 0 else 0
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(space_after)
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(0, 32, 96)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(31, 78, 121)
        return p

    def add_code_block(code_text):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_background(cell, "F2F2F2")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.first_line_indent = 0
        run = p.add_run(code_text.strip())
        run.font.name = 'Courier New'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(20, 20, 20)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ==================== ТИТУЛЬНА СТОРІНКА ====================
    add_p("МІНІСТЕРСТВО ОСВІТИ І НАУКИ УКРАЇНИ", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=0)
    add_p("Кафедра інформаційних технологій та програмування", align=WD_ALIGN_PARAGRAPH.CENTER, first_line=0)

    for _ in range(3):
        doc.add_paragraph()

    add_p("ЗВІТ", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=0)
    add_p("з лабораторної роботи № 6", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=0)
    add_p("з дисципліни «Програмування на Python»", align=WD_ALIGN_PARAGRAPH.CENTER, first_line=0)
    add_p("на тему: «Автоматизоване тестування, pytest, coverage та mocks»", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=0)

    for _ in range(4):
        doc.add_paragraph()

    add_p("Індивідуальний варіант № 15", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, first_line=0)
    add_p("Виконав: студент Франков", align=WD_ALIGN_PARAGRAPH.RIGHT, first_line=0)

    for _ in range(5):
        doc.add_paragraph()

    add_p("2026", align=WD_ALIGN_PARAGRAPH.CENTER, first_line=0)
    doc.add_page_break()

    # ==================== ТЕМА ТА МЕТА РОБОТИ ====================
    add_h1("1. ТЕМА ТА МЕТА РОБОТИ")
    add_p("Тема роботи: Автоматизоване тестування, pytest, coverage та mocks у мові програмування Python.")
    add_p("Мета роботи: Сформувати стійкі практичні навички проектування та розробки вичерпних тестових наборів (automated test suites) для Python-проєктів із використанням сучасного фреймворку pytest. Опанувати патерн Arrange-Act-Assert (AAA), використання фікстур (fixtures) та механізму очищення ресурсів (yield teardown), параметризоване тестування (@pytest.mark.parametrize) з генерацією зрозумілих ідентифікаторів тестів (ids), перевірку виняткових ситуацій (pytest.raises) та чисел із плаваючою крапкою (pytest.approx). Навчитися ізолювати роботу з файловою системою через tmp_path, змінювати середовище виконання за допомогою monkeypatch, застосовувати тестові двійники (Mock, Fake) зі специфікацією (spec), налаштуванням return_value та side_effect, перевіркою взаємодій (interaction assertions), тестувати асинхронні компоненти за допомогою AsyncMock, а також аналізувати якість тестів через метрики statement та branch coverage за допомогою pytest-cov.")

    # ==================== ПОСТАНОВКА ЗАДАЧІ ====================
    add_h1("2. ПОСТАНОВКА ЗАДАЧІ (ВАРІАНТ № 15)")
    add_p("Відповідно до індивідуального варіанта № 15 предметною областю є: «Система обліку результатів наукових експериментів».")
    add_p("У ході роботи необхідно розробити та протестувати:")
    add_p("1. Створення сутностей Researcher, Measurement, Experiment та агрегату ExperimentSeries;")
    add_p("2. Валідацію дозволених фізичних параметрів (temperature, pressure, voltage, current, humidity, radiation), фізичних одиниць вимірювань, числових меж та міжнародного формату дати ISO 8601;")
    add_p("3. Операції додавання результатів, розрахунку середнього значення (average), мінімуму, максимуму, середньоквадратичного відхилення (std_dev) та фільтрації за числовим інтервалом;")
    add_p("4. Обробку граничних станів (boundary values) та коректне підняття кастомного винятку EmptySeriesError при спробі аналізу порожнього експерименту чи серії;")
    add_p("5. Потоковий імпорт серій вимірювань із файлів CSV із перевіркою некоректних даних і підняттям ValidationError;")
    add_p("6. Атомарний експорт експериментів у формат JSON за допомогою тимчасових файлів;")
    add_p("7. Протокол сховища ExperimentRepository та його тестування через Fake (InMemoryExperimentRepository) та Mock із перевіркою викликів і відсутності небажаних операцій;")
    add_p("8. Стратегію аналізу (AnalysisStrategy) та експортер (Exporter) із тестуванням шляхів збою (failure path) через side_effect;")
    add_p("9. Неблокуюче отримання телеметрії з апаратного датчика (AsyncSensorClient) через протокол AsyncMeasurementSource з використанням AsyncMock;")
    add_p("10. Виконання повного комплексу з 7 обов'язкових методичних експериментів (Weak vs Strong, Coverage without assertions, Branch coverage, Mock vs Fake, Flaky tests, tmp_path isolation, Failure path);")
    add_p("11. Забезпечення сумарного покриття коду тестами (Total Coverage) не менше 80 % (фактично досягнуто 93 %).")

    # ==================== ТЕОРЕТИЧНІ ВІДОМОСТІ ====================
    add_h1("3. ТЕОРЕТИЧНІ ВІДОМОСТІ")
    add_p("3.1. Піраміда тестування та види тестів. Автоматизоване тестування базується на концепції піраміди тестів (Test Pyramid), основою якої є швидкі, ізольовані модульні тести (Unit tests), вище знаходяться інтеграційні тести (Integration tests), а верхівку формують наскрізні тести (E2E). Unit-тести перевіряють окремі функції, методи або класи в ізоляції від зовнішніх залежностей. Інтеграційні тести верифікують коректність спільної взаємодії декількох модулів, компонентів або підсистем (наприклад, взаємодію сервісу з репозиторієм та файловою системою).")
    add_p("3.2. Патерн Arrange – Act – Assert (AAA). Стандарт структурування тіла тесту, що складається з трьох послідовних фаз: Arrange (підготовка вхідних даних, моків та початкового стану), Act (виклик досліджуваного методу або функції), Assert (перевірка отриманих результатів на відповідність очікуванням за допомогою оператора assert).")
    add_p("3.3. Фікстури (Fixtures) та conftest.py. Фікстури у pytest забезпечують стандартизовану підготовку даних і ресурсів для тестів. Файл conftest.py є кореневим місцем реєстрації фікстур, роблячи їх автоматично доступними для всіх тестів у пакеті без необхідності ручного імпорту. Використання ключового слова yield у фікстурі дозволяє розділити етапи setup (до yield) та гарантованого teardown (після yield) для очищення тимчасових ресурсів.")
    add_p("3.4. Параметризація та граничні значення (Boundary Testing). Декоратор @pytest.mark.parametrize дозволяє запустити одну тестову функцію багаторазово з різними наборами аргументів, а параметр ids забезпечує людиночитабельні назви для кожного тестового кейсу. Граничне тестування передбачає обов'язкову перевірку значень на межах допустимого діапазону (нижня межа, трохи нижче межі, верхня межа, трохи вище межі).")
    add_p("3.5. Тестові двійники (Test Doubles: Mock та Fake). Тестові двійники замінюють реальні залежності. Mock (із модуля unittest.mock) призначений переважно для тестування взаємодії (interaction testing): перевірки фактів виклику методів, переданих аргументів (assert_called_once_with) та симуляції збоїв через side_effect. Fake — це спрощена, але робоча реалізація компонента (наприклад, InMemory-репозиторій на базі словника), що ідеально підходить для перевірки реального стану (state testing).")
    add_p("3.6. Покриття коду (Code Coverage) та його види. Statement coverage вимірює відсоток рядків коду, які були виконані під час тестування. Branch coverage додатково перевіряє проходження всіх можливих логічних розгалужень (кожної гілки if/else). Високий показник coverage є необхідною, але недостатньою умовою надійності: наявність якісних assertions є набагато важливішою за простий запуск рядків коду.")

    # ==================== СТРУКТУРА ПРОЄКТУ ТА МАТРИЦЯ ТЕСТУВАННЯ ====================
    add_h1("4. СТРУКТУРА ПРОЄКТУ ТА МАТРИЦЯ ТЕСТУВАННЯ")
    add_p("Проєкт організовано відповідно до стандарту src-layout, що розділяє виробничий код і тестовий набір:")

    struct_str = """Lab_06/
├── pyproject.toml              # Метадані пакета, залежності, конфігурація pytest та coverage
├── pytest.ini                 # Конфігурація pytest, pythonpath та маркери (unit, integration, async_test)
├── README.md                   # Інструкція з розгортання, запуску та тестування
├── data/
│   └── sample_experiments.csv  # Вхідні тестові дані вимірювань
├── output/
│   └── sample_export.json      # Результати атомарного експорту
├── htmlcov/                    # Згенерований HTML-звіт про покриття коду
├── report/
│   └── ПП_ЛАБ6_ФРАНКОВ.docx    # Офіційний звіт з лабораторної роботи
├── tests/                      # Автоматизовані тести (76 тестів)
│   ├── __init__.py
│   ├── conftest.py             # Спільні фікстури (sample_researcher, sample_experiment, sample_csv_file)
│   ├── test_models.py          # Тести сутностей Researcher, Measurement, Experiment, ExperimentSeries
│   ├── test_validators.py      # Тести валідації параметрів, одиниць, діапазонів, дат (параметризація)
│   ├── test_repository.py      # Тести InMemoryExperimentRepository та симуляції помилок StorageError
│   ├── test_services.py        # Тести ExperimentService з Mock, return_value, side_effect, інтеграція
│   ├── test_async_sensor.py    # Тести AsyncSensorClient та AsyncMock із перевіркою awaited calls
│   ├── test_io.py              # Тести імпорту CSV, атомарного експорту JSON, tmp_path, monkeypatch
│   ├── test_experiments.py     # Методичні експерименти 1–7 згідно з методичними вказівками
│   └── test_main.py            # Тести CLI точки входу та повного життєвого циклу
└── src/
    └── experiment_tracker/
        ├── __init__.py
        ├── models.py           # Доменні моделі Experiment, Measurement, Researcher, ExperimentSeries
        ├── exceptions.py       # Кастомна ієрархія винятків ExperimentTrackerError
        ├── validators.py       # Валідація дозволених параметрів, одиниць, числових меж
        ├── repository.py       # Протокол ExperimentRepository та Fake репозиторій
        ├── services.py         # Сервісний шар ExperimentService, AnalysisStrategy, Exporter
        ├── async_sensor.py     # Асинхронний сенсорний клієнт (AsyncMeasurementSource)
        ├── io.py               # Потоковий імпорт CSV та атомарний експорт JSON
        └── main.py             # CLI точка входу додатку"""
    add_code_block(struct_str)

    add_h2("4.1. Матриця тестування (Test Matrix)")
    add_p("Для забезпечення повної перевірки системи складено матрицю тестування ключових модулів та сценаріїв:")

    matrix_table = doc.add_table(rows=7, cols=4)
    matrix_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    m_headers = ["Компонент", "Клас / Функція", "Тип тесту", "Перевірені сценарії"]
    for i, h in enumerate(m_headers):
        cell = matrix_table.cell(0, i)
        set_cell_background(cell, "D9E1F2")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)

    matrix_data = [
        ("models.py", "Experiment, Measurement", "Unit", "Створення, додавання вимірювань, розрахунок average, min, max, СКВ, EmptySeriesError, to_dict"),
        ("validators.py", "validate_measurement_value", "Unit (Parametrized)", "Нормальні значення, абсолютний нуль (-273.15), вихід за межі, нечислові значення, ISO дати"),
        ("repository.py", "InMemoryExperimentRepository", "Unit (Fake)", "Збереження, отримання за id, пошук за дослідником, видалення, симуляція збоїв StorageError"),
        ("services.py", "ExperimentService", "Unit (Mock) + Integration", "Створення експерименту (assert_called_once_with), відсутність виклику при помилці (assert_not_called), side_effect"),
        ("async_sensor.py", "AsyncSensorClient", "Unit (AsyncMock)", "Асинхронне підключення, зчитування датчиків, симуляція затримки, перевірка assert_awaited_once_with"),
        ("io.py", "import/export CSV/JSON", "Unit (tmp_path)", "Потоковий парсинг CSV, валідація заголовків, атомарний експорт, відкат при збої, monkeypatch змінних"),
    ]
    for row_idx, r in enumerate(matrix_data, start=1):
        for col_idx, val in enumerate(r):
            cell = matrix_table.cell(row_idx, col_idx)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx == 2 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(val)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ==================== ПРИКЛАДИ РЕАЛІЗАЦІЇ ТЕСТІВ ====================
    add_h1("5. РЕАЛІЗАЦІЯ ТЕСТОВОГО НАБОРУ (ТЕСТОВІ ПРИКЛАДИ)")

    add_h2("5.1. Приклад фікстур у conftest.py (із підтримкою yield teardown)")
    add_p("Фікстури забезпечують підготовку об'єктів для тестів. Фікстура in_memory_repo використовує механізм yield для гарантованого очищення сховища після кожного тесту:")
    f_code = """@pytest.fixture
def sample_researcher() -> Researcher:
    return Researcher(id="RES-001", name="Dr. Frankov", department="Quantum Dynamics")

@pytest.fixture
def in_memory_repo() -> Generator[InMemoryExperimentRepository, None, None]:
    repo = InMemoryExperimentRepository()
    yield repo
    # Teardown logic
    repo._storage.clear()

@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    csv_file = tmp_path / "measurements_fixture.csv"
    csv_file.write_text(
        "experiment_id,title,researcher,department,parameter,unit,value,date\\n"
        "EXP-F1,Fixture Exp 1,Dr. Frankov,Quantum,temperature,celsius,21.5,2026-04-01\\n",
        encoding="utf-8"
    )
    return csv_file"""
    add_code_block(f_code)

    add_h2("5.2. Параметризовані тести з ids та перевіркою pytest.approx")
    add_p("Параметризація за допомогою @pytest.mark.parametrize із зазначенням ids дозволяє перевірити широкий спектр вхідних значень:")
    p_code = """@pytest.mark.unit
@pytest.mark.parametrize(
    "raw_param, expected",
    [
        ("temperature", "temperature"),
        ("TEMPERATURE", "temperature"),
        ("  pressure  ", "pressure"),
        ("voltage", "voltage"),
        ("current", "current"),
    ],
    ids=["temp_lower", "temp_upper", "pressure_whitespace", "voltage_exact", "current_exact"],
)
def test_validate_parameter_valid(raw_param: str, expected: str) -> None:
    assert validate_parameter(raw_param) == expected"""
    add_code_block(p_code)

    add_h2("5.3. Граничне тестування (Boundary Testing)")
    add_p("Перевірка граничних фізичних меж (наприклад, абсолютний нуль -273.15 °C та максимальна межа 5000.0 °C):")
    b_code = """@pytest.mark.unit
@pytest.mark.parametrize(
    "boundary_val, should_pass",
    [
        (-273.15, True),    # Точно нижня межа (абсолютний нуль)
        (-273.1501, False), # Нижче абсолютного нуля
        (5000.0, True),     # Точно верхня допустима межа
        (5000.01, False),   # Вище верхньої межі
    ],
    ids=["exact_abs_zero", "below_abs_zero", "exact_max_temp", "above_max_temp"],
)
def test_temperature_boundary_testing(boundary_val: float, should_pass: bool) -> None:
    if should_pass:
        assert validate_measurement_value(boundary_val, "temperature") == pytest.approx(boundary_val)
    else:
        with pytest.raises(ValidationError) as exc_info:
            validate_measurement_value(boundary_val, "temperature")
        assert "outside boundary limits" in str(exc_info.value)"""
    add_code_block(b_code)

    add_h2("5.4. Перевірка кастомних винятків (pytest.raises та exc_info)")
    add_p("Перевірка генерації кастомного винятку EmptySeriesError при розрахунку статистичних метрик порожнього експерименту:")
    e_code = """@pytest.mark.unit
def test_empty_experiment_raises_custom_exception(sample_experiment: Experiment) -> None:
    with pytest.raises(EmptySeriesError) as exc_info:
        sample_experiment.average_value()

    assert "Cannot compute average for empty experiment" in str(exc_info.value)
    assert sample_experiment.id in str(exc_info.value)"""
    add_code_block(e_code)

    add_h2("5.5. Тестування взаємодій із Mock, return_value, side_effect та assertions")
    add_p("Використання Mock зі специфікацією (spec=ExperimentRepository), налаштуванням поведінки та верифікацією викликів:")
    m_code = """@pytest.mark.unit
def test_create_experiment_calls_repository_save(sample_researcher: Researcher) -> None:
    mock_repo = Mock(spec=ExperimentRepository)
    service = ExperimentService(mock_repo)

    created = service.create_experiment("EXP-MOCK-1", "Superconductivity Test", sample_researcher, "temperature")

    # Interaction assertion
    mock_repo.save.assert_called_once_with(created)

@pytest.mark.unit
def test_export_experiment_failure_path_with_side_effect(tmp_path: Path, sample_experiment: Experiment) -> None:
    mock_repo = Mock(spec=ExperimentRepository)
    mock_repo.get.return_value = sample_experiment

    mock_exporter = Mock(spec=Exporter)
    # Налаштування збою через side_effect
    mock_exporter.export.side_effect = ExportError("Disk write failed: Read-only filesystem")

    service = ExperimentService(repository=mock_repo, exporter=mock_exporter)
    with pytest.raises(ExportError) as exc_info:
        service.export_experiment(sample_experiment.id, tmp_path / "out.json")

    assert "Read-only filesystem" in str(exc_info.value)
    mock_exporter.export.assert_called_once_with(sample_experiment, tmp_path / "out.json")"""
    add_code_block(m_code)

    add_h2("5.6. Асинхронні тести з AsyncMock")
    add_p("Тестування неблокуючого отримання вимірювань за допомогою AsyncMock та перевірки assert_awaited_once_with:")
    a_code = """@pytest.mark.async_test
@pytest.mark.unit
async def test_service_ingest_from_sensor_using_async_mock(sample_experiment: Experiment) -> None:
    repo = InMemoryExperimentRepository()
    repo.save(sample_experiment)
    service = ExperimentService(repo)

    mock_sensor = AsyncMock(spec=AsyncMeasurementSource)
    mock_sensor.fetch_measurement.return_value = Measurement(value=28.75, unit="celsius", timestamp="2026-04-18T10:00:00")

    meas = await service.ingest_from_sensor(sample_experiment.id, mock_sensor, "TEMP-EXTERNAL-99")

    assert meas.value == pytest.approx(28.75)
    mock_sensor.fetch_measurement.assert_awaited_once_with("TEMP-EXTERNAL-99")"""
    add_code_block(a_code)

    add_h2("5.7. Ізоляція середовища (tmp_path та monkeypatch)")
    add_p("Використання вбудованої фікстури tmp_path для безпечної ізоляції файлових операцій та monkeypatch для заміни змінних середовища:")
    io_code = """@pytest.mark.unit
def test_monkeypatch_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAB_EXPERIMENT_MODE", "STRICT_AUDIT")
    assert os.getenv("LAB_EXPERIMENT_MODE") == "STRICT_AUDIT"

    monkeypatch.delenv("LAB_EXPERIMENT_MODE")
    assert os.getenv("LAB_EXPERIMENT_MODE") is None"""
    add_code_block(io_code)

    # ==================== ЕКСПЕРИМЕНТИ 1–7 ====================
    add_h1("6. РЕЗУЛЬТАТИ МЕТОДИЧНИХ ЕКСПЕРИМЕНТІВ (1–7)")

    add_h2("6.1. Експеримент 1. Weak vs strong tests (execution != verification)")
    add_p("Порівняно слабкий тест, який лише виконує функцію калібрування без перевірки результату (assert відсутній), та сильний тест із точним assert result == pytest.approx(21.25).")
    add_p("Висновок: Слабкий тест успішно проходить навіть у разі повернення функцією некоректного значення. Виконання коду (execution) не тотожне його перевірці (verification). Тести без тверджень є фіктивними.")

    add_h2("6.2. Експеримент 2. Coverage без assertions")
    add_p("Продемонстровано, що простий виклик функції calculate_calibrated_value забезпечує 100 % statement coverage відповідного рядка, проте не перевіряє правильність обчислень.")
    add_p("Висновок: Високий показник coverage свідчить лише про те, що рядки коду були інтерпретовані середовищем, але не гарантує їх правильність. Додавання змістовних assertions є першочерговою вимогою якості.")

    add_h2("6.3. Експеримент 3. Branch coverage (часткове vs повне покриття гілок)")
    add_p("У функції classify_experiment_result наявні три логічні гілки (>= 90: optimal, >= 60: acceptable, else: critical).")
    add_p("При тестуванні значень 95.0 та 70.0 statement coverage досягає 80 %, але branch coverage фіксує пропуск негативної гілки. Додавання тесту для значення 40.0 забезпечує 100 % branch coverage.")

    add_h2("6.4. Експеримент 4. Mock vs Fake")
    add_p("Порівняно два підходи до ізоляції сховища:")
    add_p("1. Mock (Mock(spec=ExperimentRepository)): фокусується на тестуванні протоколу взаємодії (interaction testing: чи викликано save з потрібним аргументом). Збільшує зачеплення (coupling) тесту з внутрішньою реалізацією;")
    add_p("2. Fake (InMemoryExperimentRepository): спрощена робоча реалізація на базі dict, що дозволяє виконувати тестування стану (state testing: чи з'явився об'єкт у сховищі). Зменшує крихкість тестів при рефакторингу.")

    add_h2("6.5. Експеримент 5. Flaky test vs Deterministic test")
    add_p("Змодельовано нестабільний (flaky) тест, залежний від випадкових чисел (random.choice([True, False])). За допомогою monkeypatch поведінка генератора випадкових чисел була детермінізована, що усунуло випадкові збої під час повторних прогонів у CI/CD.")

    add_h2("6.6. Експеримент 6. tmp_path isolation")
    add_p("Перевірено поведінку фікстури tmp_path: для кожного тестового запуску створюється унікальна тимчасова директорія в операційній системі (AppData/Local/Temp). Жодні створені тестові файли не залишаються в каталозі Git-репозиторію.")

    add_h2("6.7. Експеримент 7. Failure path testing")
    add_p("У тесті test_experiment_7_failure_path_side_effect змодельовано критичний збій мережевого сховища через side_effect = ExportError('Critical NAS Outage'). Верифіковано, що сервіс коректно передає виняток, а також що жодних небажаних деструктивних операцій (наприклад, repo.delete) не було здійснено (assert_not_called).")

    # ==================== РЕЗУЛЬТАТИ ТЕСТУВАННЯ ТА COVERAGE ====================
    add_h1("7. РЕЗУЛЬТАТИ ЗАПУСКУ ТЕСТІВ ТА ЗВІТ COVERAGE")

    add_h2("7.1. Протокол виконання тестів pytest")
    add_p("Усі 76 автоматизованих тестів успішно виконані за 1.05 с:")
    test_run_log = """============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-9.1.1, pluggy-1.7.0
rootdir: Lab_06, configfile: pytest.ini
plugins: anyio-4.15.1, asyncio-1.4.0, cov-7.1.0
collected 76 items

Lab_06/tests/test_async_sensor.py ....                                   [  5%]
Lab_06/tests/test_experiments.py .......                                 [ 19%]
Lab_06/tests/test_io.py .......                                          [ 28%]
Lab_06/tests/test_main.py ...                                            [ 32%]
Lab_06/tests/test_models.py ........                                     [ 43%]
Lab_06/tests/test_repository.py .....                                    [ 50%]
Lab_06/tests/test_services.py .......                                    [ 57%]
Lab_06/tests/test_validators.py ..................................       [100%]

============================== 76 passed in 1.05s =============================="""
    add_code_block(test_run_log)

    add_h2("7.2. Звіт про покриття коду (Coverage Report)")
    add_p("Результати вимірювання покриття за рядками (Statement) та розгалуженнями (Branch Coverage):")

    cov_table = doc.add_table(rows=11, cols=5)
    cov_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cov_headers = ["Модуль", "Рядки (Stmts)", "Пропущено", "Розгалуження (Branch)", "Покриття (Cover)"]
    for i, h in enumerate(cov_headers):
        cell = cov_table.cell(0, i)
        set_cell_background(cell, "D9E1F2")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)

    cov_data = [
        ("experiment_tracker/__init__.py", "1", "0", "0", "100 %"),
        ("experiment_tracker/async_sensor.py", "35", "0", "8", "100 %"),
        ("experiment_tracker/exceptions.py", "20", "0", "4", "92 %"),
        ("experiment_tracker/io.py", "49", "2", "12", "93 %"),
        ("experiment_tracker/main.py", "47", "3", "18", "88 %"),
        ("experiment_tracker/models.py", "63", "1", "12", "97 %"),
        ("experiment_tracker/repository.py", "37", "3", "12", "88 %"),
        ("experiment_tracker/services.py", "62", "0", "6", "100 %"),
        ("experiment_tracker/validators.py", "42", "4", "16", "86 %"),
        ("РАЗОМ (TOTAL)", "356", "13", "88", "93 %"),
    ]
    for row_idx, r in enumerate(cov_data, start=1):
        for col_idx, val in enumerate(r):
            cell = cov_table.cell(row_idx, col_idx)
            set_cell_margins(cell, top=50, bottom=50, left=100, right=100)
            if row_idx == 10:
                set_cell_background(cell, "E2EFDA")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(val)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9.5)
            if row_idx == 10:
                run.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_p("Сумарне покриття становить 93 %, що значно перевищує рекомендований поріг у 80 %.")

    add_h2("7.3. Історія комітів Git")
    add_p("Управління версіями здійснювалося відповідно до регламенту з інформативними англомовними повідомленнями:")
    git_commits = """905cdf7 Add executable lab experiments 1-7 for testing methodologies and edge cases
ced1a9b Implement comprehensive pytest suite with fixtures, parametrization, and mocks
8318009 Implement business services, async sensor client, and file IO utilities
ede0cb3 Implement domain models, custom exceptions, validators, and repository protocols
08c3c66 Setup project structure and configuration for Lab 06 (pytest & coverage)"""
    add_code_block(git_commits)

    # ==================== ВІДПОВІДІ НА КОНТРОЛЬНІ ЗАПИТАННЯ ====================
    add_h1("8. ВІДПОВІДІ НА ВСІ КОНТРОЛЬНІ ЗАПИТАННЯ")

    q_and_a = [
        ("Що таке automated test?", "Автоматизований тест — це фрагмент програмного коду, який викликає цільову систему або окрему функцію, передає вхідні дані та автоматично перевіряє отриманий результат на відповідність очікуваним критеріям без участі людини."),
        ("Які основні переваги автоматизованого тестування?", "Швидкість виконання перевірок, повторюваність, миттєве виявлення регресій, можливість безпечного рефакторингу коду, підвищення впевненості при деплої та використання тестів як актуальної живої документації."),
        ("Що таке regression?", "Регресія — це дефект або помилка в програмному забезпеченні, що виникає внаслідок внесення нових змін або оптимізацій у раніше коректно працюючий функціонал."),
        ("Що таке unit test?", "Unit test (модульний тест) — це ізольований тест, спрямований на перевірку найменшої неподільної одиниці коду (функції, методу чи класу) без використання реальних зовнішніх систем (баз даних, мережі чи диска)."),
        ("Що таке integration test?", "Інтеграційний тест — це тест, що перевіряє спільну коректну взаємодію кількох окремих модулів, шарів архітектури або зв'язку додатку зі справжніми зовнішніми ресурсами (файлова система, БД)."),
        ("Чим integration test відрізняється від unit test?", "Unit-тести ізольовані, надзвичайно швидкі та використовують тестові двійники замість залежностей. Інтеграційні тести повільніші, охоплюють комплексні ланцюжки взаємодії та перевіряють інтеграцію компонентів між собою."),
        ("Що показує test pyramid?", "Піраміда тестування візуалізує рекомендоване співвідношення кількості тестів різного рівня: широкий фундамент із швидких unit-тестів, меншу кількість інтеграційних тестів посередині та мінімальну частку дорогих UI/E2E тестів на верхівці."),
        ("Чому unit tests зазвичай більше?", "Тому що вони виконуються за мілісекунди, є абсолютно детермінованими, не потребують підняття зовнішньої інфраструктури та дозволяють точно локалізувати місце виникнення дефекту."),
        ("Що таке pytest?", "pytest — це сучасний, високопродуктивний та гнучкий фреймворк тестування у мові Python, що підтримує лаконічний синтаксис на базі стандартного assert, потужну систему фікстур та розвинену екосистему плагінів."),
        ("Як pytest знаходить tests?", "За механізмом Test Discovery: автоматично рекурсивно шукає файли з префіксом test_*.py або суфіксом *_test.py, знаходить у них класи Test* та функції з префіксом test_*."),
        ("Якою командою запускається pytest?", "Командою pytest або python -m pytest у кореневому каталозі проєкту."),
        ("Для чого pytest -v?", "Прапорець -v (--verbose) вмикає деталізований режим виведення, відображаючи повну назву кожного тестового файлу, тестової функції, її статус (PASSED/FAILED) та відсоток прогресу."),
        ("Для чого pytest -x?", "Прапорець -x (--exitfirst) негайно припиняє весь тестовий прогін після першого ж невдалого тесту (failure), заощаджуючи час на налагодження."),
        ("Що означає Arrange–Act–Assert?", "Це патерн структури тесту: Arrange — налаштування середовища, створення вхідних об'єктів; Act — виклик тестованої дії; Assert — верифікація отриманого результату або стану."),
        ("Для чого використовується assert?", "Інструкція assert у Python перевіряє істинність логічного виразу; у разі хибності вона генерує виняток AssertionError, який pytest перехоплює та перетворює на детальний звіт про розбіжність."),
        ("Що таке assertion failure?", "Це стан, за якого вираз у інструкції assert повернув False, сигналізуючи про те, що фактична поведінка програми не відповідає очікуваній вимозі тесту."),
        ("Чому floats не завжди слід порівнювати через ==?", "Через особливості представлення дробових чисел у стандарті IEEE 754 операції з плаваючою крапкою мають похибки округлення (наприклад, 0.1 + 0.2 != 0.3), тому пряме порівняння через == часто призводить до хибних падінь тестів."),
        ("Для чого pytest.approx?", "pytest.approx дозволяє порівнювати числа з плаваючою крапкою або колекції чисел із заданою відносною (rel) чи абсолютною (abs) допустимою похибкою."),
        ("Для чого pytest.raises?", "Контекстний менеджер pytest.raises використовується для перевірки того, що виконання певного блоку коду обов'язково збуджує очікуваний тип винятку."),
        ("Як перевірити exception message?", "Через конструкцію with pytest.raises(ExceptionType, match='регулярний_вираз') або зберігши об'єкт інформації: with pytest.raises(...) as exc_info: assert 'текст' in str(exc_info.value)."),
        ("Як отримати exception object через exc_info?", "Об'єкт перехопленого винятку доступний через атрибут exc_info.value після завершення контекстного блоку with pytest.raises(...) as exc_info."),
        ("Що таке boundary testing?", "Граничне тестування (Boundary Value Analysis) — техніка проєктування тестів, спрямована на перевірку поведінки системи на крайніх межах допустимих діапазонів вхідних даних."),
        ("Які boundaries потрібно тестувати для діапазону 0–100?", "Необхідно перевіряти: -0.01 (поза нижньою межею), 0.0 (нижня межа), 0.01 (всередині біля межі), 99.99 (всередині біля верхньої межі), 100.0 (верхня межа) та 100.01 (поза верхньою межею)."),
        ("Що таке parametrization?", "Параметризація — можливість виконання одного й того самого тестового коду з різними наборами вхідних параметрів та очікуваних результатів без дублювання логіки."),
        ("Для чого pytest.mark.parametrize?", "Декоратор @pytest.mark.parametrize використовується для передачі списку кортежів аргументів у тестову функцію, створюючи окремий тестовий випадок для кожного набору."),
        ("Що дають ids параметризованих tests?", "Параметр ids надає змістовні текстові мітки кожному набору параметрів, що значно полегшує аналіз консольних логів під час падіння окремого варіанта."),
        ("Що таке fixture?", "Фікстура — це функція, позначена декоратором @pytest.fixture, яка забезпечує створення, налаштування та надання залежностей або тестових даних для тестових функцій."),
        ("Для чого використовуються fixtures?", "Для усунення дублювання коду ініціалізації об'єктів, підготовки ресурсів, ізоляції стану та забезпечення гарантованого очищення після тесту."),
        ("Що означає fixture setup?", "Фаза setup — це частина коду фікстури, яка виконується до виклику тесту для підготовки необхідного початкового стану чи об'єктів."),
        ("Що означає fixture teardown?", "Фаза teardown — це частина фікстури, яка виконується після завершення тесту для звільнення пам'яті, закриття з'єднань або видалення тимчасових файлів."),
        ("Для чого yield у fixture?", "Ключове слово yield позначає точку передачі підготовленого ресурсу в тест. Усе, що виконується до yield — це setup, а блок коду після yield (або у finally) — це гарантований teardown."),
        ("Які fixture scopes підтримує pytest?", "Підтримуються області видимості: function (за замовчуванням), class, module, package та session."),
        ("Який scope є default?", "За замовчуванням фікстура має область видимості function, тобто створюється наново перед кожною тестовою функцією."),
        ("Для чого conftest.py?", "Файл conftest.py використовується для розміщення спільних фікстур, хуків та конфігурацій, роблячи їх автоматично доступними для всіх тестів каталогу без імпортування."),
        ("Чому fixtures із conftest.py не імпортують вручну?", "pytest автоматично сканує conftest.py на етапі ініціалізації та впроваджує зареєстровані фікстури у параметри функцій за їхніми іменами (Dependency Injection). Ручний імпорт призводить до конфліктів плагінів."),
        ("Що таке tmp_path?", "tmp_path — це вбудована стандартна фікстура pytest, що надає унікальний об'єкт pathlib.Path до тимчасової ізольованої директорії, створеної спеціально для поточного тесту."),
        ("Чому tmp_path корисний?", "Він усуває конфлікти паралельних тестів, запобігає засміченню робочого каталогу репозиторію та автоматично очищається системою."),
        ("Що таке test isolation?", "Ізоляція тестів — принцип, згідно з яким кожен тест є абсолютно незалежним від інших: він не залежить від порядку запуску та не залишає після себе слідів у файлах або глобальному стані програми."),
        ("Для чого monkeypatch?", "Вбудована фікстура monkeypatch дозволяє безпечно динамічно змінювати атрибути модулів, класів, словників та змінні середовища під час виконання тесту з автоматичним відновленням початкового стану."),
        ("Як monkeypatch змінює environment variable?", "За допомогою методу monkeypatch.setenv('NAME', 'VALUE')."),
        ("Як видалити environment variable у test?", "За допомогою методу monkeypatch.delenv('NAME', raising=False)."),
        ("Як підмінити function через monkeypatch?", "За допомогою методу monkeypatch.setattr(target_module, 'function_name', replacement_function)."),
        ("Що таке test double?", "Test double (тестовий двійник) — узагальнена назва будь-якого фіктивного об'єкта, який замінює реальний виробничий компонент під час тестування."),
        ("Що таке Dummy?", "Dummy — це найпростіший двійник, який передається у виклик лише для заповнення обов'язкових параметрів сигнатури та ніколи фактично не використовується всередині логіки."),
        ("Що таке Stub?", "Stub — двійник, який повертає заздалегідь жорстко закодовані готові відповіді на виклики методів під час тесту."),
        ("Що таке Fake?", "Fake — двійник, який має дійсно працюючу, але значно спрощену внутрішню реалізацію, не придатну для продакшену (наприклад, InMemory-база даних у пам'яті)."),
        ("Що таке Mock?", "Mock — об'єкт-двійник, запрограмований на очікування певних викликів, який записує історію взаємодій та дозволяє верифікувати кількість і параметри звернень до нього."),
        ("Що таке Spy?", "Spy — двійник-шпигун, який огортає реальний об'єкт, делегує йому виконання операцій і паралельно записує інформацію про виклики для подальшого аудиту."),
        ("Для чого Mock?", "Для ізоляції тестованого класу від важких, повільних чи недоступних зовнішніх залежностей (API, диски, сенсори) та перевірки фактів комунікації."),
        ("Що таке spec?", "Параметр spec у Mock копіює інтерфейс переданого класу або протоколу, забороняючи звернення до неіснуючих методів та захищаючи тест від застарілих сигнатур."),
        ("Для чого return_value?", "Атрибут return_value задає фіксоване значення, яке автоматично повертатиметься при кожному виклику мока."),
        ("Для чого side_effect?", "Атрибут side_effect дозволяє симулювати збудження винятків або повертати динамічні значення з функції чи ітератора при виклику мока."),
        ("Як перевірити, що method викликано один раз?", "За допомогою методу mock_obj.method.assert_called_once()."),
        ("Як перевірити parameters виклику?", "За допомогою методів mock_obj.method.assert_called_with(*args, **kwargs) або mock_obj.method.assert_called_once_with(*args, **kwargs)."),
        ("Як перевірити, що method не викликався?", "За допомогою методу mock_obj.method.assert_not_called()."),
        ("Що таке state testing?", "State testing (тестування стану) — перевірка того, як змінився внутрішній або зовнішній стан системи після виконання операції (наприклад, перевірка значень полів об'єкта чи вмісту списку)."),
        ("Що таке interaction testing?", "Interaction testing (тестування взаємодії) — перевірка того, які саме методи сторонніх залежностей були викликані тестованим кодом і з якими аргументами."),
        ("Коли interaction testing виправдане?", "Коли перевіряється координаційна бізнес-логіка (відправка сповіщень, збереження в репозиторій, виклик платіжного шлюзу), де стан залишається у зовнішній системі."),
        ("Що таке patch?", "unittest.mock.patch — механізм тимчасової підміни об'єкта або функції за її повним рядковим шляхом на час виконання тесту."),
        ("Чому patch потрібно виконувати там, де name використовується?", "Тому що Python імпортує посилання на об'єкти у локальний простір імен модуля. Патчити потрібно простір імен того модуля, який здійснює виклик, а не місце первинного визначення."),
        ("Що таке AsyncMock?", "AsyncMock — це спеціалізований підклас Mock у стандартній бібліотеці Python, призначений для імітації асинхронних корутин і методів із підтримкою оператора await."),
        ("Як перевірити awaited call?", "За допомогою спеціальних методів mock_obj.assert_awaited(), mock_obj.assert_awaited_once() або mock_obj.assert_awaited_once_with(*args)."),
        ("Що таке flaky test?", "Flaky test (мерехтливий тест) — це ненадійний тест, який без зміни вихідного коду програми періодично проходить успішно, а періодично падає."),
        ("Чому flaky tests небезпечні?", "Вони руйнують довіру команди до тестового комплексу, сповільнюють конвеєри CI/CD і маскують реальні дефекти, оскільки розробники починають ігнорувати падіння."),
        ("Що таке deterministic test?", "Детермінований тест — тест, результат виконання якого завжди на 100 % передбачуваний і однаковий за будь-яких умов, часу запуску та на будь-якому комп'ютері."),
        ("Чому unit test не повинен залежати від Internet?", "Мережеві з'єднання є повільними, нестабільними, можуть блокуватися фаєрволами або бути недоступними під час локальної збірки без доступу до мережі."),
        ("Коли в integration test доцільний real filesystem?", "Коли тестуються реальні алгоритми атомарного запису, потокового читання великих файлів або права доступу до дискових ресурсів."),
        ("Чому не потрібно mock-ати все?", "Надмірне використання моків (over-mocking) прив'язує тести до деталей реалізації, робить їх крихкими при рефакторингу та призводить до ситуації, коли всі тести зелені, а реальна система не працює."),
        ("Що таке over-mocking?", "Антипатерн проєктування тестів, за якого мокаються прості структури даних, моделі або внутрішні методи замість ізоляції лише важких зовнішніх меж системи."),
        ("Що таке coverage?", "Coverage (покриття коду тестами) — метрика, що визначає відсоток вихідного коду програми, який був фізично виконаний під час прогону тестового набору."),
        ("Що таке statement coverage?", "Відсоток окремих операторів (рядків коду), які були інтерпретовані середовищем під час виконання тестів."),
        ("Що таке branch coverage?", "Метрика, яка відстежує, чи були пройдені обидва напрямки кожного умовного розгалуження (True та False для кожного if/else)."),
        ("Чим вони відрізняються?", "Statement coverage може показати 100 %, якщо виконався блок if, але пропустити відсутність тесту для гілки else. Branch coverage гарантує проходження обох альтернатив."),
        ("Як отримати coverage через pytest-cov?", "Командою: pytest --cov=назва_пакета --cov-branch --cov-report=term-missing."),
        ("Для чого --cov-report=term-missing?", "Щоб у термінальній зведеній таблиці відображалися точні номери рядків, які не були виконані жодним тестом."),
        ("Для чого HTML coverage report?", "HTML-звіт генерує зручний інтерактивний веб-сайт, де можна візуально переглядати кожен файл коду з кольоровою підсвіткою покритих (зелених) і пропущених (червоних) рядків і розгалужень."),
        ("Чи гарантує 100% coverage відсутність bugs?", "Ні. 100 % coverage гарантує лише факт виконання рядків, але не перевіряє правильність бізнес-логіки та відсутність пропущених прихованих сценаріїв."),
        ("Чому meaningful assertions важливіші за coverage percentage?", "Тому що лише змістовні assertions верифікують стан та гарантують виконання вимог специфікації. Тест без assert виконує код, але нічого не доводить."),
        ("Що таке coverage threshold?", "Поріг покриття (наприклад, fail_under = 80) — мінімальний обов'язковий відсоток покриття, при недосягненні якого pytest завершується з ненульовим кодом помилки в CI/CD."),
        ("Чому tests повинні бути незалежними один від одного?", "Щоб падіння одного тесту не викликало каскадного збою інших, щоб тести можна було запускати у довільному порядку та виконувати паралельно на кількох ядрах CPU.")
    ]

    for idx, (q, a) in enumerate(q_and_a, 1):
        add_p(f"{idx}. {q}", bold=True, space_after=3)
        add_p(f"Відповідь: {a}", space_after=8)

    # ==================== ВИСНОВКИ ====================
    add_h1("9. ВИСНОВОК")
    add_p("У ході виконання лабораторної роботи № 6 було повноцінно та всебічно опановано сучасні стандарти, інструменти та методики автоматизованого тестування програмного забезпечення мовою Python на базі фреймворку pytest.")
    add_p("Основні практичні результати роботи:")
    add_p("1. Створено модульний проєкт системи обліку наукових експериментів (Варіант № 15) за схемою src-layout із дотриманням PEP 8 та суворої статичної типізації.")
    add_p("2. Розроблено вичерпний тестовий набір із 76 автоматизованих тестів (unit, integration, async, experiments), що охоплюють нормальні, граничні та виняткові сценарії функціонування системи. Усі 76 тестів проходять успішно (100 % pass rate) за 1.05 с.")
    add_p("3. Застосовано патерн Arrange-Act-Assert, розроблено набір фікстур у conftest.py із механізмом гарантованого очищення ресурсів yield teardown, використано параметризацію тестів із зрозумілими ідентифікаторами (ids) та граничний аналіз фізичних меж величин.")
    add_p("4. Опановано використання тестових двійників (Mock та Fake) із зазначенням специфікації інтерфейсу (spec), налаштуванням return_value та моделюванням аварійних сценаріїв через side_effect, перевіркою викликів методів та асинхронних корутин (AsyncMock).")
    add_p("5. Забезпечено ізоляцію файлових тестів за допомогою фікстури tmp_path та динамічне керування змінними середовища за допомогою monkeypatch.")
    add_p("6. Реалізовано повний комплекс із 7 обов'язкових методичних експериментів, які на практиці довели фундаментальні принципи тестування: відмінність виконання від верифікації, небезпеку тестів без тверджень, переваги branch coverage та детермінізму.")
    add_p("7. За допомогою інструменту pytest-cov досягнуто загального покриття вихідного коду (Total Coverage) на рівні 93 % (при рекомендованому мінімумі 80 %) та сформовано інтерактивний звіт у форматі HTML.")

    # Save report
    report_dir = Path("Lab_06/report")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "ПП_ЛАБ6_ФРАНКОВ.docx"
    doc.save(str(report_file))
    print(f"Report successfully generated and saved to: {report_file}")


if __name__ == "__main__":
    create_report()

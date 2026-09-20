# Legal Case Search

MVP прототип **RAG-системы для поиска судебных дел по описанию правовой ситуации**.

Пользователь формулирует ситуацию в свободной форме, после чего AI-driven pipeline анализирует запрос и подбирает наиболее релевантные судебные дела. На текущем этапе проект сфокусирован на поисковом pipeline и проверке качества retrieval: найденные кандидаты выводятся в консоль.

## Архитектура

Упрощённый pipeline:

```text
                User Query
                     │
                     ▼
          ┌─────────────────────┐
          │   Query Analysis    │
          │       LLM           │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Retrieval / Search  │
          └──────────┬──────────┘
                     │
                     ▼
             Candidate Cases
                     │
                     ▼
          ┌─────────────────────┐
          │ Relevance / Ranking │
          │       Agent         │
          └──────────┬──────────┘
                     │
                     ▼
              Best Candidates
                     │
                     ▼
                 Console
```

## Особенности

* поиск судебных дел по текстовому описанию ситуации;
* обработка пользовательского запроса с помощью LLM;
* RAG-oriented retrieval pipeline;
* использование AI agents для организации отдельных этапов поиска;
* формирование набора кандидатов;
* отбор наиболее релевантных результатов;
* вывод найденных судебных дел и результатов поиска в консоль.

## Пример

Пользователь может передать запрос в форме описания ситуации:

```text
Ответчик нарушил договорное обязательство
и отказался возместить истцу убытки
после расторжения договора.
```

После обработки запроса система формирует кандидатов из корпуса судебных дел и выводит результаты:

```text
Query:
The defendant breached a contractual obligation...

Top candidates:

1. Case ID: ...
   Relevance: ...

2. Case ID: ...
   Relevance: ...

3. Case ID: ...
   Relevance: ...
```

## Основные компоненты системы:

### Query processing

Пользовательский запрос представляет собой свободное описание правовой ситуации.

LLM используется для анализа запроса и подготовки информации, необходимой следующим этапам поиска.

### Retrieval

По обработанному запросу выполняется поиск по корпусу судебных дел.

Цель retrieval stage — получить достаточно широкий набор кандидатов, среди которых потенциально находятся релевантные решения.

### Agentic ranking

Полученные кандидаты дополнительно анализируются AI agent'ом.

Агент используется для оценки соответствия найденного дела исходному описанию ситуации и формирования более релевантного списка результатов.

### Result generation

На текущем этапе результаты выводятся непосредственно в консоль.

Полноценный пользовательский интерфейс является одним из следующих этапов развития проекта.

## Установка

### Требования

Для запуска проекта необходимы:

* Python 3.10+
* Git
* API key используемой LLM-платформы

### Модель

Проект использует дообученную модель TryDotAtwo/ruBERT-ruLaw

(Дообученная DeepPavlov/rubert-base-cased на корпусе русских правовых текстов RusLawOD).

Файлы модели должны лежать в папке src/model/.

Как загрузить модель:

Установите huggingface-hub:

```bash
pip install huggingface-hub
```

Скачайте модель в нужную директорию:

```bash
huggingface-cli download TryDotAtwo/ruBERT-ruLaw \
  --local-dir src/model \
  --local-dir-use-symlinks False
```

Либо программно:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="TryDotAtwo/ruBERT-ruLaw",
    local_dir="src/model",
    local_dir_use_symlinks=False
)
```

После загрузки в src/model/ должны появиться:

config.json
model.safetensors (или pytorch_model.bin)
tokenizer.json / vocab.txt / tokenizer_config.json и др.

### Клонирование репозитория

```bash
git clone https://github.com/temich91/legal-doc-search.git
cd legal-doc-search
```

### Создание виртуальной среды

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Environment variables

Создайте `.env` в корне проекта:

```env
LLM_API_KEY=your_api_key
```

## ▶Запуск

```bash
python legal-doc-search/src/main.py
```

После запуска можно ввести описание судебной ситуации и получить список найденных кандидатов в консоли.

# L06 - пакет лабораторної

Статус: лабораторні докази зібрано; це не готове ДЗ_5 і не схвалення релізу.
Не завантажуйте пакет до попередніх репозиторіїв ДЗ і не переписуйте їх golden.jsonl.

- security-red-teaming-log.md і PDF: компактний журнал за вісьмома розділами шаблону.
- l06_security.jsonl: перші ДВА кейси D23; для ДЗ шаблон вимагає щонайменше ШІСТЬ.
- reports/: чотири незмінні власні звіти; traces/: усі 58 трейсів.
- evidence/: дослівні докази, прогноз, аудит, огляд хибних спрацювань і replay.
- reference/: точні snapshots loader/assertions/початкового набору з runner 3521b46.

Новий набір: hash 0df464e11a1c. Початковий виконаний: d4bfe36ae622.
LAB-D23-01 відповідає SEC-305; LAB-D23-02 - SEC-306. Модель не викликалась під новим хешем;
ми перевірили еквівалентність налаштувань і повторно оцінили відповіді зі старих трейсів.
Це offline replay, не новий експеримент і не додаткові незалежні прогони.

## Перевірити без моделі
Із кореня цього пакета: `python3 scripts/replay_d23.py`.
Результат записується до evidence/regression-replay.json і має збігтися з вкладеним.
Скрипт перевіряє 58 відповідей, профілі й сесії, вихідні хеші та 42 негативні перевірки D23.

## Перевірити схему у своєму Docker
Скопіюйте l06_security.jsonl з цього пакета до l06/sets/; попередньо перевірте,
що там немає вашої іншої версії файла. Із папки l06:

```bash
STAND_DIR=../paypilot-stand-shared docker compose run --rm eval --set l06_security --gate all --dry-run
```

Це не викликає модель. Запуски з --profile викликали б модель повторно і тут не потрібні.
Не ставте глобальний --summarize-after; у двох кейсах лишено початковий поріг 8.

## Що далі для ДЗ
Звірити повне формулювання ДЗ; розширити набір щонайменше до 6 кейсів, включити перевірки дії,
позитивні контролі, D24 за потреби, ціну покриття та рішення щодо непокритих векторів.
Не підганяти кейси до зеленого: виправлення хибних оракулів підтвердити старими трейсами.
Захисти інструмента/промпту цим пакетом не реалізовані.

## Джерела
Шаблон: https://drive.google.com/file/d/1ZEYNXu_-LBAX456rLB3OSaYHDfKueEdt/view
Runner: https://github.com/alex-pancho/paypilot-l06-eval/tree/3521b4610f3bdb0ec1be4c511fb2d38c179e5a93
LLM01: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
LLM06: https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
LLM07: https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/
Agentic: https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/

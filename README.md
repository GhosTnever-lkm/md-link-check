# md-link-check

Офлайн-проверка Markdown-документации: находит относительные ссылки на несуществующие файлы, якоря `#…`, которых нет в целевом заголовке, и ссылки, ведущие за пределы репозитория. Внешние URL не открываются — проверка работает без сети и не зависит от внешних сайтов. Без зависимостей, Python 3.10+.

## Быстрый старт

```bash
python -m md_link_check            # текущая папка
python -m md_link_check docs --json
python -m md_link_check . --exclude "vendor/*"   # пропустить файлы по маске
```

```text
docs/guide.md:12: target file does not exist: ./setup.md
docs/guide.md:20: anchor not found in target: ../README.md#instalation
2 problem(s) found
```

Код возврата: `0` — все ссылки в порядке, `1` — найдены проблемы, `2` — путь не является папкой.

## Что проверяется

- `[текст](file.md)`, `[текст](dir/file.md#section)`, `[текст](#section)` и картинки `![alt](img.png)`.
- Якоря считаются GitHub-способом: строчные буквы, пунктуация убирается, пробелы становятся дефисами; повторы получают `-1`, `-2`.
- Ссылки внутри блоков кода (``` и ~~~) пропускаются.
- Процент-кодирование в путях (`my%20doc.md`) раскодируется.

Не проверяется: внешние URL (`http:`, `https:`, `mailto:` и др.), якоря внутри не-Markdown файлов, ссылки с HTML-тегами `<a href>`.

## Разработка

```bash
python -m unittest discover -s tests -t .
```

## Лицензия

MIT — см. [LICENSE](LICENSE).

## История изменений

См. [CHANGELOG.md](CHANGELOG.md). Политика безопасности — в [SECURITY.md](SECURITY.md).

## Использование в CI

Фрагмент для GitHub Actions (Python 3.10+, без зависимостей):

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- name: md-link-check
  run: python -m md_link_check .
```

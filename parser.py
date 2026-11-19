import requests
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://www.vedomosti.ru/"

response = requests.get(url, timeout=15)

print("Статус:", response.status_code)
print("Размер страницы:", len(response.text))

db_path = Path(__file__).resolve().with_name("news.db")
connection = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)

rows = connection.execute("SELECT keyword FROM keywords ORDER BY id").fetchall()
connection.close()

print("Ключевые слова из базы:")
for (keyword,) in rows:
    print(keyword)

    if keyword == "сакура":
        search_page = requests.get(
            "https://api.vedomosti.ru/v2/documents/search",
            params={
                "query": keyword,
                "doc_types": "materials",
                "material_types": "news,articles",
                "sort": "weight",
                "limit": 5,
            },
            timeout=15,
        )
        search_page.raise_for_status()
        data = search_page.json()

        print("Всего совпадений:", data["stat"]["total"])
        for item in data["found"]:
            article = item["source"]
            url = "https://" + article["url"]
            date = article["published_at"]

            page = requests.get(url, timeout=15)
            page.raise_for_status()
            soup = BeautifulSoup(page.content, "html.parser")
            paragraphs = soup.select(".article__boxes p.box-paragraph__text")
            text = "\n\n".join(p.get_text().strip() for p in paragraphs)

            print("Заголовок:", article["title"])
            print("Дата публикации:", date)
            print("Количество абзацев:", len(paragraphs))
            print("Начало текста:", text[:300])
            if text.strip():
                with sqlite3.connect(db_path) as db:
                    result = db.execute(
                        """
                        INSERT INTO News (keyword, title, date, url, text)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(url) DO NOTHING
                        """,
                        (keyword, article["title"], date, url, text),
                    )

                if result.rowcount == 1:
                    print("Статья сохранена:", article["title"])
                else:
                    print("Статья с такой ссылкой уже есть в базе")
            else:
                print("У статьи пустой текст, пропускаем:", url)
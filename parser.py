
import requests

url = "https://www.kp.ru/"

response = requests.get(url, timeout=15)

print("Статус:", response.status_code)
print("Размер страницы:", len(response.text))

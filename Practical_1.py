# -*- coding: windows-1251 -*-
import urllib.parse
import urllib.request
import json
import webbrowser

class WikipediaSearcher:
    def __init__(self):
        self.BASE_URL = "https://ru.wikipedia.org/w/api.php"

    def get_user_input(self):
        return input("Введите поисковый запрос: ").strip()

    def encode_query(self, query):
        # Правильное кодирование для URL с учетом русских символов
        return urllib.parse.quote(query.encode('utf-8'))

    def search_with_api(self, query):
        """Используем API Wikipedia для поиска"""
        encoded_query = self.encode_query(query)
        
        # Пробуем разные варианты API запросов
        api_methods = [
            # Метод opensearch (похож на автодополнение в Wikipedia)
            f"https://ru.wikipedia.org/w/api.php?action=opensearch&search={encoded_query}&limit=10&namespace=0&format=json",
            # Метод query (стандартный поиск)
            f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&srlimit=10&format=json",
            # Метод для поиска по заголовкам
            f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&srwhat=title&srlimit=10&format=json"
        ]
        
        for api_url in api_methods:
            try:
                req = urllib.request.Request(
                    api_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    results = self.parse_api_response(data, api_url)
                    if results:
                        return results
            except Exception as e:
                print(f"Ошибка при запросе к API: {e}")
                continue
                
        return []

    def parse_api_response(self, data, api_url):
        """Парсим ответ от API Wikipedia"""
        results = []
        
        # Обработка ответа от opensearch API
        if 'opensearch' in api_url:
            if isinstance(data, list) and len(data) > 1:
                titles = data[1]
                for title in titles:
                    pageid = self.get_pageid_from_title(title)
                    results.append({
                        'title': title,
                        'pageid': pageid
                    })
        
        # Обработка ответа от query API
        elif 'query' in api_url:
            if 'query' in data and 'search' in data['query']:
                for item in data['query']['search']:
                    results.append({
                        'title': item['title'],
                        'pageid': str(item['pageid'])
                    })
        
        return results

    def get_pageid_from_title(self, title):
        """Получаем pageid по заголовку статьи"""
        encoded_title = self.encode_query(title)
        url = f"https://ru.wikipedia.org/w/api.php?action=query&format=json&titles={encoded_title}"
        
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                pages = data.get('query', {}).get('pages', {})
                for pageid in pages.keys():
                    if pageid != '-1':
                        return str(pageid)
        except:
            pass
        return None

    def display_results(self, results, query):
        if not results:
            print(f"По запросу '{query}' не найдено подходящих статей.")
            return False

        print(f"\nРезультаты поиска для '{query}':")
        print("=" * 60)
        
        for i, item in enumerate(results, 1):
            print(f"{i}. {item['title']}")
        
        print("=" * 60)
        return True

    def select_article(self, results):
        while True:
            try:
                choice = input("\nВведите номер статьи для открытия (или 'q' для выхода): ").strip()
                if choice.lower() == 'q':
                    return None, None
                choice = int(choice)
                if 1 <= choice <= len(results):
                    return results[choice-1]['pageid'], results[choice-1]['title']
                print(f"Пожалуйста, введите число от 1 до {len(results)}")
            except ValueError:
                print("Пожалуйста, введите число.")

    def open_in_browser(self, pageid, title, query):
        if pageid:
            url = f"https://ru.wikipedia.org/w/index.php?curid={pageid}"
        elif title:
            encoded_title = self.encode_query(title)
            url = f"https://ru.wikipedia.org/wiki/{encoded_title}"
        else:
            # Если ничего не нашли, открываем страницу поиска
            encoded_query = self.encode_query(query)
            url = f"https://ru.wikipedia.org/w/index.php?search={encoded_query}"
        
        print(f"Открываю: {url}")
        webbrowser.open(url)

    def run(self):
        try:
            query = self.get_user_input()
            if not query:
                print("Запрос не может быть пустым.")
                return

            print(f"Ищем '{query}' в Wikipedia...")
            results = self.search_with_api(query)

            if self.display_results(results, query):
                pageid, title = self.select_article(results)
                self.open_in_browser(pageid, title, query)
            else:
                # Если не нашли результатов, открываем страницу поиска
                print("Открываю страницу поиска Wikipedia...")
                encoded_query = self.encode_query(query)
                url = f"https://ru.wikipedia.org/w/index.php?search={encoded_query}"
                webbrowser.open(url)

        except Exception as e:
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    searcher = WikipediaSearcher()
    searcher.run()
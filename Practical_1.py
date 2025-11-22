# -*- coding: windows-1251 -*-
import urllib.parse
import urllib.request
import json
import webbrowser
import re

class WikipediaSearcher:
    def __init__(self):
        self.BASE_URL = "https://ru.wikipedia.org/w/api.php"

    def get_user_input(self):
        return input("Введите поисковый запрос: ").strip()

    def encode_query(self, query):
        return urllib.parse.quote(query)

    def search_using_web_interface(self, query):
        """Имитируем поиск через веб-интерфейс Wikipedia"""
        encoded_query = self.encode_query(query)
        
        # Получаем HTML страницу поиска
        url = f"https://ru.wikipedia.org/w/index.php?search={encoded_query}&title=Служебная:Поиск&profile=advanced&fulltext=1&ns0=1"
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read().decode('utf-8')
                return self.parse_search_results(html_content, query)
        except Exception as e:
            print(f"Ошибка при получении страницы поиска: {e}")
            return []

    def parse_search_results(self, html, query):
        """Парсим HTML страницы поиска для извлечения результатов"""
        results = []
        
        # Ищем заголовки статей в результатах поиска
        # Паттерн для поиска заголовков в HTML
        title_patterns = [
            r'<div class="searchresult">.*?<a[^>]*href="/wiki/([^"]+)"[^>]*>([^<]+)</a>',
            r'<li[^>]*class="mw-search-result"[^>]*>.*?<a[^>]*href="/wiki/([^"]+)"[^>]*>([^<]+)</a>',
            r'<a[^>]*href="/wiki/([^"]+)"[^>]*title="([^"]+)"[^>]*>'
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                if len(match) == 2:
                    page_slug, title = match
                    # Декодируем HTML-сущности в заголовке
                    title = self.decode_html_entities(title)
                    
                    # Получаем pageid по заголовку
                    pageid = self.get_pageid_from_title(title)
                    
                    if title and page_slug and title not in [r['title'] for r in results]:
                        results.append({
                            'title': title,
                            'pageid': pageid,
                            'slug': page_slug
                        })
                        
                    if len(results) >= 10:  # Ограничиваем количество результатов
                        break
        
        # Если не нашли результатов стандартным способом, ищем альтернативными паттернами
        if not results:
            # Ищем в данных JSON, которые могут быть встроены в страницу
            json_pattern = r'wgSearchResults":\s*(\[.*?\])'
            json_match = re.search(json_pattern, html)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    for item in json_data:
                        if 'title' in item:
                            title = item['title']
                            pageid = self.get_pageid_from_title(title)
                            results.append({
                                'title': title,
                                'pageid': pageid,
                                'slug': title.replace(' ', '_')
                            })
                except:
                    pass
        
        return results

    def decode_html_entities(self, text):
        """Декодирует HTML-сущности в тексте"""
        replacements = {
            '&quot;': '"',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&nbsp;': ' ',
            '&#91;': '[',
            '&#93;': ']'
        }
        for entity, replacement in replacements.items():
            text = text.replace(entity, replacement)
        return text

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
                data = json.loads(response.read().decode())
                pages = data.get('query', {}).get('pages', {})
                for pageid in pages.keys():
                    if pageid != '-1':
                        return str(pageid)
        except:
            pass
        return None

    def display_results(self, results, query):
        if not results:
            print(f"По запросу '{query}' ничего не найдено.")
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

            print(f"Ищем '{query}' через веб-интерфейс Wikipedia...")
            results = self.search_using_web_interface(query)

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
# -*- coding: windows-1251 -*-
import urllib.parse
import urllib.request
import json
import webbrowser

class WikipediaSearcher:
    """
    Класс для поиска и отображения статей в Википедии.
    Реализует все этапы работы: ввод запроса, поиск, парсинг, вывод и открытие статей.
    """
    
    def __init__(self):
        """Инициализация базовых параметров для API запросов."""
        # Базовый URL API Википедии
        self.BASE_URL = "https://ru.wikipedia.org/w/api.php"
        # Параметры по умолчанию для поискового запроса
        self.SEARCH_PARAMS = {
            'action': 'query',      # Действие - выполнить запрос
            'list': 'search',       # Тип запроса - поиск
            'format': 'json',       # Формат ответа - JSON
            'srsearch': ''          # Поисковый запрос (будет заполнен позже)
        }

    def get_user_input(self):
        """
        Этап 1: Получение поискового запроса от пользователя.
        
        Returns:
            str: Введенная пользователем строка поиска
        """
        return input("Введите поисковый запрос: ").strip()

    def encode_query(self, query):
        """
        Кодирование поискового запроса для URL (Percent-encoding).
        
        Args:
            query (str): Исходный поисковый запрос
            
        Returns:
            str: Закодированный запрос для использования в URL
        """
        return urllib.parse.quote(query)

    def make_request(self, encoded_query):
        """
        Этап 2: Выполнение HTTP-запроса к API Википедии.
        
        Args:
            encoded_query (str): Закодированный поисковый запрос
            
        Returns:
            dict: Распарсенные JSON данные от сервера
            
        Raises:
            Exception: При ошибках сети или парсинга JSON
        """
        # Копируем параметры по умолчанию и добавляем поисковый запрос
        params = self.SEARCH_PARAMS.copy()
        params['srsearch'] = encoded_query
        
        # Формируем полный URL с параметрами
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        
        # Создаем запрос с кастомным User-Agent
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        
        # Выполняем HTTP GET запрос и читаем ответ
        with urllib.request.urlopen(req) as response:
            # Декодируем байты в строку и парсим JSON
            return json.loads(response.read().decode())

    def parse_results(self, data):
        """
        Этап 3: Парсинг JSON ответа и извлечение нужной информации.
        
        Args:
            data (dict): JSON данные от API Википедии
            
        Returns:
            list: Список словарей с информацией о статьях
        """
        # Извлекаем только нужные поля из каждого результата поиска
        return [
            {
                'title': item['title'],     # Заголовок статьи
                'pageid': item['pageid'],   # Уникальный ID страницы
                'snippet': item['snippet']  # Краткое описание (может содержать HTML)
            }
            for item in data['query']['search']  # Проходим по всем результатам поиска
        ]

    def display_results(self, results):
        """
        Этап 4: Отображение результатов поиска пользователю.
        
        Args:
            results (list): Список найденных статей
            
        Returns:
            bool: True если есть результаты, False если результатов нет
        """
        # Проверяем, есть ли результаты
        if not results:
            print("По вашему запросу ничего не найдено.")
            return False

        print("\nРезультаты поиска:")
        # Выводим каждый результат с номером
        for i, item in enumerate(results, 1):
            print(f"{i}. {item['title']}")
            
            # Очищаем сниппет от HTML-тегов
            snippet = item['snippet']
            while '<' in snippet and '>' in snippet:
                start = snippet.find('<')
                end = snippet.find('>') + 1
                snippet = snippet[:start] + snippet[end:]
                
            print(f"   {snippet}\n")
        return True

    def select_article(self, results):
        """
        Получение выбора пользователя для открытия конкретной статьи.
        
        Args:
            results (list): Список доступных статей
            
        Returns:
            int: pageid выбранной статьи
        """
        while True:
            try:
                # Запрашиваем номер статьи
                choice = int(input("Введите номер статьи для открытия: "))
                
                # Проверяем, что номер в допустимом диапазоне
                if 1 <= choice <= len(results):
                    return results[choice-1]['pageid']
                print("Некорректный номер. Попробуйте снова.")
            except ValueError:
                # Обрабатываем случай, когда введено не число
                print("Пожалуйста, введите число.")

    def open_in_browser(self, pageid):
        """
        Этап 5: Открытие выбранной статьи в браузере по умолчанию.
        
        Args:
            pageid (int): Уникальный идентификатор страницы в Википедии
        """
        # Формируем URL для прямой ссылки на статью по pageid
        url = f"https://ru.wikipedia.org/w/index.php?curid={pageid}"
        # Открываем URL в браузере по умолчанию
        webbrowser.open(url)

    def run(self):
        """
        Основной метод, запускающий весь процесс поиска.
        Координирует работу всех этапов и обрабатывает исключения.
        """
        try:
            # Этап 1: Считывание введенных данных
            query = self.get_user_input()
            if not query:
                print("Запрос не может быть пустым.")
                return

            # Этап 2: Выполнение запроса к серверу
            encoded_query = self.encode_query(query)
            response_data = self.make_request(encoded_query)

            # Этап 3: Парсинг ответа сервера
            results = self.parse_results(response_data)

            # Этап 4: Вывод результатов поиска
            if self.display_results(results):
                # Этап 5: Открытие выбранной статьи
                pageid = self.select_article(results)
                self.open_in_browser(pageid)

        except Exception as e:
            # Обработка всех возможных ошибок
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    """
    Точка входа в программу.
    Создает экземпляр класса WikipediaSearcher и запускает его.
    """
    # Создаем экземпляр поисковика
    searcher = WikipediaSearcher()
    # Запускаем основной процесс
    searcher.run()
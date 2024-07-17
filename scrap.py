import wikipediaapi
import openai
import os

# Настройка API
openai.api_base = "http://localhost:4999/v1"  # Исправлено на HTTPS
openai.api_key = "not needed for a local LLM"
model = "gpt4all-j-v1.3-groovy"

# Создаем экземпляр Wikipedia API с указанием user-agent
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='YourAppName/1.0 (YourEmail@example.com)'
)

MAX_CHUNK_SIZE = 2048  # Максимальный размер текста для обработки

def get_wikipedia_page(page_name):
    page = wiki_wiki.page(page_name)
    if page.exists():
        return page
    else:
        return None

def chunk_text(text, max_size):
    """Разбивает текст на части не более max_size символов"""
    chunks = []
    while len(text) > max_size:
        pos = text.rfind('.', 0, max_size)  # Ищем ближайший конец предложения
        if pos == -1:
            pos = max_size
        chunks.append(text[:pos].strip())
        text = text[pos:].strip()
    chunks.append(text)
    return chunks

def classify_and_format(text):
    prompt = f"Classify the following text into a category and provide a formatted summary:\n\n{text}\n\nCategory and Summary:"
    try:
        response = openai.Completion.create(
            model=model,
            prompt=prompt,
            max_tokens=1500,
            temperature=0.5,
            top_p=0.95,
            n=1,
            echo=False,
            stream=False
        )
        result = response.choices[0].text.strip()
        
        # Предположим, что результат содержит категорию и текст, разделенные специальным разделителем
        category, formatted_text = result.split('\n', 1)
        category = category.replace("Category: ", "").strip()
        formatted_text = formatted_text.strip()
    except (ValueError, IndexError, openai.error.OpenAIError) as e:
        print(f"Error processing text: {e}")
        category, formatted_text = "Trash", text.strip()
    
    return category, formatted_text

def save_to_file(category, title, content, chunk_index):
    # Проверяем корректность имени файла
    title = sanitize_filename(title)
    category = sanitize_filename(category)
    
    # Генерируем имя файла
    file_name = f"{title}_{category}_{chunk_index+1}.txt"
    
    # Записываем содержимое в файл
    file_path = os.path.join(file_name)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_')).rstrip()

def process_page(page):
    content = page.text
    if not content:
        return
    chunks = chunk_text(content, MAX_CHUNK_SIZE)
    for i, chunk in enumerate(chunks):
        category, formatted_content = classify_and_format(chunk)
        save_to_file(category, page.title, formatted_content, i)
    for link_title, link in page.links.items():
        linked_page = get_wikipedia_page(link_title)
        if linked_page:
            process_page(linked_page)

# Основной процесс
start_page = "Heart"  # Начальная страница, откуда начнется извлечение
page = get_wikipedia_page(start_page)
if page:
    process_page(page)

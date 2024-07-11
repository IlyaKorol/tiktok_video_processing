import requests
import shutil
import os
import time
from moviepy.editor import VideoFileClip, AudioFileClip
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

font_path = "arial-unicode-ms.ttf"

# Основная функция для загрузки видео
def download_video(video_url, output_path):
    try:
        with requests.get(video_url, stream=True) as r:
            with open(output_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return True, None
    except Exception as e:
        error_msg = f"Ошибка при загрузке видео {video_url}: {str(e)}"
        print(error_msg)
        return False, error_msg

# Основная функция для обработки видео
def process_video(input_path, output_path):
    try:
        video_clip = VideoFileClip(input_path)

        # Замена аудиодорожки
        audio_clip = AudioFileClip("never_gonna_give_you_up.mp3")
        video_clip = video_clip.set_audio(audio_clip)

        video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        return True, None
    except Exception as e:
        error_msg = f"Ошибка при обработке видео {input_path}: {str(e)}"
        print(error_msg)
        return False, error_msg

# Функция для получения популярных видео TikTok
def get_popular_videos(region='pl', count=10, offset=0):
    url = "https://tiktok-scraper7.p.rapidapi.com/feed/list"
    querystring = {
        "region": region,
        "count": count,
        "offset": offset
    }
    headers = {
        "x-rapidapi-key": "0576fdfb04msh3cef0e9a97a8c0ep1a9e25jsn70fb109419e8",
        "x-rapidapi-host": "tiktok-scraper7.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Вызываем исключение для неправильных кодов статуса
        return response.json()["data"]
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    return []

# Основная функция
def main():
    region = 'pl'
    videos_per_request = 30  # Увеличение количества видео в каждом запросе
    total_videos_to_download = 100  # Установлено 100 видео для загрузки
    offset = 0

    output_folder = 'tiktok_videos'
    os.makedirs(output_folder, exist_ok=True)

    videos_downloaded = 0
    start_time = time.time()

    # Регистрация шрифта для отчета PDF
    try:
        pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))
    except Exception as e:
        print(f"Ошибка при загрузке шрифта: {str(e)}")
        return

    # Список для хранения ошибок загрузки видео
    download_errors = []

    while videos_downloaded < total_videos_to_download:
        videos = get_popular_videos(region=region, count=videos_per_request, offset=offset)
        if not videos:
            print("Видео не найдены или произошла ошибка на offset={}. Прерывание процесса.".format(offset))
            download_errors.append(f"Видео не найдены или произошла ошибка на offset={offset}. Прерывание процесса.")
            break

        for index, video in enumerate(videos):
            video_url = video['play']
            video_title = f"video_{videos_downloaded + 1}.mp4"
            output_path = os.path.join(output_folder, video_title)

            print(f"Загрузка видео {videos_downloaded + 1}...")
            success, error_msg = download_video(video_url, output_path)
            if success:
                print(f"Видео {videos_downloaded + 1} загружено в {output_path}")

                # Обработка загруженного видео
                success, process_error_msg = process_video(output_path, output_path)
                if success:
                    print(f"Видео {videos_downloaded + 1} успешно обработано.")
                    videos_downloaded += 1
                else:
                    print(f"Ошибка обработки видео {videos_downloaded + 1}: {process_error_msg}")
                    download_errors.append(f"Видео {videos_downloaded + 1}: {process_error_msg}")  # Добавляем сообщение об ошибке в список
            else:
                print(f"Ошибка загрузки видео {videos_downloaded + 1}: {error_msg}")
                download_errors.append(f"Видео {videos_downloaded + 1}: {error_msg}")  # Добавляем сообщение об ошибке в список

            if videos_downloaded >= total_videos_to_download:
                break

        offset += videos_per_request
        time.sleep(3)  # Уменьшаем паузу до 3 секунд для увеличения скорости загрузки

    end_time = time.time()
    total_time = end_time - start_time

    # Создание отчета в PDF с использованием reportlab
    pdf_filename = "report.pdf"
    try:
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        c.setFont("ArialUnicode", 12)  # Использование зарегистрированного шрифта

        report_title = "Отчет о выполнении задания"
        c.drawCentredString(300, 750, report_title)

        c.drawString(100, 700, f"Количество обработанных видео: {videos_downloaded}")
        c.drawString(100, 680, f"Время, затраченное на весь процесс: {total_time:.2f} секунд")

        # Выводим ошибки загрузки видео в отчет, если они есть
        if download_errors:
            c.drawString(100, 660, "Ошибки загрузки видео:")
            y_position = 640
            for error in download_errors:
                c.drawString(120, y_position, error[:100])  # Ограничиваем длину строки для отчета
                y_position -= 20

        c.save()
        print(f"Отчет сохранен в {pdf_filename}")
    except Exception as e:
        print(f"Ошибка при создании отчета PDF: {str(e)}")

if __name__ == "__main__":
    main()

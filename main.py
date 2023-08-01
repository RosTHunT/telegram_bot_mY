import logging
import os

import asyncio
import yt_dlp

from aiogram import Bot, Dispatcher, types, executor
from aiohttp.web_routedef import get

from settings import TELEGRAMTOKEN

bot = Bot(token=TELEGRAMTOKEN)
dp = Dispatcher(bot)


class FileNameCollectorPP(yt_dlp.postprocessor.common.PostProcessor):
    def __init__(self):
        super(FileNameCollectorPP, self).__init__(None)
        self.filenames = []

    def run(self, information):
        self.filenames.append(information['filepath'])
        return [], information


@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.reply('Напишіть /commands для виводу доступних команд')


@dp.message_handler(commands=['commands'])
async def commands_cmd(message: types.Message):
    await message.reply('/start - почати  \n'
                        '/commands - вивід команд бота \n'
                        '/run ... - пошук пісні, де замість ... впишіть назву треку\n')


@dp.message_handler(commands=['run'])
async def search_cmd(message: types.Message):
    arg = message.get_args()

    await message.reply(f'Зачекайте будь ласка, відбувається пошук треку {arg}')
    YLD_OPTIONS = {
        'format': 'bestaudio/best',
        'noplalist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }

    with yt_dlp.YoutubeDL(YLD_OPTIONS) as ydl:
        try:
            get(arg)
        except Exception as e:
            filename_collector = FileNameCollectorPP()
            ydl.add_post_processor(filename_collector)
            video = ydl.extract_info(f'ytsearch:{arg}', download=True)['entries'][0]
            try:
                await message.reply_document(open(filename_collector.filenames[0], 'rb'))
            except Exception as e:
                if "File too large for uploading" in str(e):
                    await message.reply('Помилка, розмір файлу завеликий... спробуйте інший файл')
                else:
                    await message.reply(f'Виникла помилка, спробуйте інший файл. {e}')
            await asyncio.sleep(5)

            os.remove(filename_collector.filenames[0])
        else:
            video = ydl.extract_info_async(arg, download=True)
        return filename_collector.filenames[0]


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
import os
from dotenv import load_dotenv



def tel_bot():
    load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'))
    dp = Dispatcher(bot)

    # Questions to ask
    questions = [
        ["Здравствуйте, Я телеграмм бот Северного морского пути. Я могу помочь вам с созданием заявки на проводку"
         " или показать список заявок. Выберите необходимое действие" , ['создать заявку на проводку', 'получить список заявок']],
        ["Введите наименование корабля", ['A', 'B', 'C']],
        ["Введите IMO корабля", ['Option A', 'B', 'C']],
         ["Введите Ледовый класс корабля", ['A', 'B', 'C']],
         ["Введите скорость корабля в узлах", ['A', 'B', 'C']],
         ["Введите дату и время начала плавания", ['A', 'B', 'C']],
         ["Выберите пункт начала плавания", ['A', 'B', 'C']],
         ["Выберите пункт окончания плавания", ['A', 'B', 'C']]
    ]

    user_data = {}


    def get_keyboard(options):
        buttons = [KeyboardButton(option) for option in options]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(*buttons)
        return keyboard

    @dp.message_handler(commands=['start'])
    async def start_handler(message: types.Message):
        user_id = message.from_user.id
        user_data[user_id] = {}
        await message.answer(questions[0][0],
                             reply_markup=get_keyboard(questions[0][1]))  # Example options

    @dp.message_handler()
    async def answer_handler(message: types.Message):
        user_id = message.from_user.id
        user_answers = user_data.get(user_id, {})
        current_question_index = len(user_answers)
        print(user_answers)

        if message.text == "получить список заявок":
            await message.answer("выгрузка заявок в формате Excel")
            with open('timesheet.xlsx', 'rb') as file:
                await bot.send_document(
                    chat_id=message.chat.id,
                    document=types.InputFile(file)
                )
            user_answers[current_question_index] = message.text
            user_data[user_id] = user_answers
        else:
            if current_question_index != 0:
                if user_answers[0] == "получить список заявок":
                    await message.answer("Нажмите на /start, чтобы выбрать действие.")
                else:
                    if current_question_index < len(questions):
                        user_answers[current_question_index] = message.text
                        user_data[user_id] = user_answers
                        next_question_index = current_question_index + 1
                        if next_question_index < len(questions):
                            await message.answer(questions[next_question_index][0],
                                                 reply_markup=get_keyboard(questions[next_question_index][1]))  # Example options
                        else:
                            await message.answer("Спасибо !")
                            #await message.answer("Thank you for your answers! Here's a summary:\n" +
                                                # "\n".join([f"{q}: {a}" for q, a in user_answers.items()]))

                    else:
                        await message.answer("Нажмите на /start, чтобы выбрать действие.")
                        print(user_data)
            else:
                if current_question_index < len(questions):
                    user_answers[current_question_index] = message.text
                    user_data[user_id] = user_answers
                    next_question_index = current_question_index + 1
                    if next_question_index < len(questions):
                        await message.answer(questions[next_question_index][0],
                                             reply_markup=get_keyboard(
                                                 questions[next_question_index][1]))  # Example options
                    else:
                        await message.answer("Thank you for your answers! Here's a summary:\n" +
                                             "\n".join([f"{q}: {a}" for q, a in user_answers.items()]))

                else:
                    await message.answer("Нажмите на /start, чтобы выбрать действие.")
                    print(user_data)

    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    tel_bot()
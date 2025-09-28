from config import *
import info
from info import ADMIN_CHAT_ID

bot = Bot(token=info.BOT_TOKEN)
dp = Dispatcher()

storage = MemoryStorage()

@dp.callback_query(lambda c: c.data in ["btn_alls"])
async def main_menu(message: Message):
    tg_id = message.from_user.id
    async with aiosqlite.connect("users.db") as db:
        cursor = await db.execute("SELECT role FROM users WHERE tg_id=?", (tg_id,))
        role = await cursor.fetchone()
        if role == None:
            await bot.send_message(tg_id, "Пожалуйста, пройдите регистрацию до конца!")
            await role_type_heandler_choice(message, tg_id)
        else:
            btn_sendmessage = InlineKeyboardButton(text='Отправить сообщение', callback_data="send_mess_ws")
            kb = InlineKeyboardMarkup(inline_keyboard=[[btn_sendmessage]])
            await bot.send_message(tg_id,
                f"Вы зарегестрированы, ожидайте рассылки!\n\n"
                f"Доступные команды:\n"
                f"/start - запуск бота\n"
                f"/report - обращение в техническую поддержку\n\n"
                f"Чтобы отправить сообщение, нажмите на кнопку.",
                reply_markup=kb)


@dp.message(Command("delete"))
async def delete_info(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    try:
        async with aiosqlite.connect("users.db") as db:
            await db.execute("DELETE from users WHERE tg_id=?", (tg_id,))
            await db.commit()
        await message.answer("Ваши данные успешно удалены!")
        await start_process(message, state)
    except:
        await message.answer("Что-то пошло не так(")


@dp.message(CommandStart())
async def start_process(message: Message, state: FSMContext):
    await create_database()
    tg_id = message.from_user.id
    username = message.from_user.username
    name = None
    surname = None
    role = None
    clas = None
    flag = await check_user_in_data(tg_id)
    if flag == True:
        '''btn_sendmessage = InlineKeyboardButton(text='Отправить сообщение', callback_data="send_mess_ws")
        kb = InlineKeyboardMarkup(inline_keyboard=[[btn_sendmessage]])
        await message.answer("Вы зарегестрированны в системе! Ожидайте рассылки. Если желаете отправить письмо, дайте знать нажатием на кнопку)", reply_markup=kb)'''
        await main_menu(message)

    else:
        await message.answer("Приветствую! Пройдите регистрацию, чтобы получать рассылку! Как ваше имя?")
        await state.set_state(FSMFillForm.name)


@dp.callback_query(F.data == "send_mess_ws")
async def smw(call: CallbackQuery, state: FSMContext):
    tg_id = call.from_user.id
    await bot.send_message(tg_id, "Отлично! Напишите имя и фамилию, кому адресовано сообщениие.")
    await state.set_state(FSMFillForm.name_smw)

@dp.message(StateFilter(FSMFillForm.name_smw))
async def smw1(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    await state.update_data(name_smw=message.text)
    data = await state.get_data()
    name_smw = data.get("name_smw")
    name_parts = name_smw.split()
    if len(name_parts) != 2:
        await message.answer("Введен некорректный формат! (Иван Иванов)")
        await main_menu(message)
    else:
        first_name, surname = name_parts
        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute("SELECT tg_id FROM users WHERE name=? AND surname=?", (first_name, surname))
            result = await cursor.fetchone()
            if result == None:
                await bot.send_message(tg_id, text="Пользователь не найден!")
                await main_menu(message)
            else:
                await bot.send_message(tg_id, text="Напишите текст сообщения")
                await state.update_data(received_id=result)
                await state.update_data(full_name=name_parts)
                await state.set_state(FSMFillForm.message)

@dp.message(StateFilter(FSMFillForm.message))
async def smw2(message: Message, state: FSMContext):
    data = await state.get_data()
    rec_id = data["received_id"]
    int_id = rec_id[0]
    full_name = data["full_name"]
    str_name = full_name[0]
    str_surname = full_name[1]
    text = message.text
    print(text)
    print(rec_id)

    btn_sendmessage = InlineKeyboardButton(text='Отправить сообщение', callback_data="send_mess_ws")
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn_sendmessage]])
    await bot.send_message(int_id, f"Пришло сообщение от {str_name} {str_surname}: \n\n<b>{text}</b>\n\nЕсли желаете ответить, нажмите на кнопку.", reply_markup=kb, parse_mode="HTML")
    await message.answer("Сообщение отправлено!")
    await state.clear()
    await main_menu(message)



@dp.message(Command(commands=["send_notificate"]), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def send_notificate(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    try:
        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute("SELECT role FROM users WHERE tg_id=?", (tg_id,))
            role = await cursor.fetchone()
            if role[0] == role_student:
                await message.reply("Вы не можете рассылать сообщения!")
            elif not role:
                await message.reply("Вы не зарегестрированы в системе!")
            else:
                btn_study = InlineKeyboardButton(text='Учеба', callback_data="btn_catStudy")
                btn_sport = InlineKeyboardButton(text='Спорт', callback_data="btn_catSport")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_study],
                            [btn_sport]])
                await message.answer("Определите категорию объявления:", reply_markup=keyboard)
    except Exception as e:
        await message.reply("Произошла ошибка при проверке ваших прав.")
        print(f"!!!!!!!!!!Error, Glop:  {e}")
        await start_process(message, state)

@dp.callback_query(lambda c: c.data in ["btn_catStudy", "btn_catSport"])
async def btn_catStudy(call: CallbackQuery, state: FSMContext):
    tg_id = call.from_user.id
    cat_type = call.data
    await state.update_data(cat_type=cat_type)
    btn_stud = InlineKeyboardButton(text='Ученикам', callback_data="for_stud")
    btn_teach = InlineKeyboardButton(text='Преподавателям', callback_data="for_teach")
    btn_adm = InlineKeyboardButton(text='Администраторам бота', callback_data="for_adm")
    btn_forall = InlineKeyboardButton(text='Всем пользователям', callback_data="for_all")
    kb_for_who = InlineKeyboardMarkup(inline_keyboard=[[btn_stud],
                                                        [btn_teach],
                                                       [btn_adm],
                                                       [btn_forall]])
    await call.message.edit_text("Кому вы хотите разослать сообщение?", reply_markup=kb_for_who)



@dp.callback_query(F.data.startswith("for_"))
async def send_recipient_selection(call: CallbackQuery, state: FSMContext):
    role_type = call.data
    await state.update_data(role_type=role_type)
    await call.answer("Напишите текст сообщения.")
    await state.set_state(FSMFillForm.text)

@dp.message(StateFilter(FSMFillForm.text))
async def process_send_text(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        role_type = data.get('role_type')
        cat_type = data.get('cat_type')
        print(cat_type)
        text=message.text
        tg_id = message.from_user.id
        if cat_type == "btn_catStudy":
            cat_to_send = "study"
        elif cat_type == "btn_catSport":
            cat_to_send = "sport"
        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute(f"SELECT tg_id FROM users WHERE {cat_to_send}=1")
            result = await cursor.fetchall()
            if not result:
                await message.reply("Нет пользователей, подписанных на выбранную категорию.")
                await state.clear()
                return

        res_list = list(result)
        finally_list = []

        if role_type != "for_all":
            if role_type != "for_adm":
                if role_type == "for_stud":
                    role_to_send = role_student
                elif role_type == "for_teach":
                    role_to_send = role_teacher
                async with aiosqlite.connect("users.db") as db:
                    cursor = await db.execute("SELECT tg_id FROM users WHERE role=?", (role_to_send,))
                    recipients = await cursor.fetchall()
                    if not recipients:
                        await message.reply(f"Нет пользователей с ролью {role_to_send}")
                        await state.clear()
                        return
                rec_list = list(recipients)
                for i in rec_list:
                    for x in res_list:
                        if i == x:
                            finally_list.append(i)


                async with aiosqlite.connect("users.db") as db:
                    cursor = await db.execute("SELECT name, surname FROM users WHERE tg_id=?", (tg_id,))
                    data = await cursor.fetchone()
                    name, surname = data
                    full_name = f"{name} {surname}".strip()
                    text = text + '\n\n' + f"Отправитель: {full_name}" + '\n' + f"Категория: {cat_to_send}"
                    success = 0
                    for row in finally_list:
                        try:
                            chat_id = row[0] if isinstance(row, (tuple, list)) else row
                            print(f"Получатели: {type(finally_list)}: {finally_list}")
                            await bot.send_message(chat_id=chat_id, text=text)
                            success += 1
                        except Exception as e:
                            print(f"Не удалось отправить сообщение пользователю {row}: {e}")
                    await message.reply(f"Рассылка завершена. Успешно отправлено: {success}/{len(finally_list)}")
            else:
                async with aiosqlite.connect("users.db") as db:
                    cursor = await db.execute("SELECT name, surname FROM users WHERE tg_id=?", (tg_id,))
                    data = await cursor.fetchone()
                    name, surname = data
                    full_name = f"{name} {surname}".strip()
                    text = text + '\n\n' + f"Отправитель: {full_name}"
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
                print(text)
                await message.answer("Ваше сообщение доставлено! В скором времени с вами свяжутся.")
        else:
            async with aiosqlite.connect("users.db") as db:
                cursor = await db.execute("SELECT tg_id FROM users")
                recipients = await cursor.fetchall()
                if not recipients:
                    await message.reply(f"Нет пользователей с ролью {role_to_send}")
                    await state.clear()
                    return
            rec_list = list(recipients)
            for i in rec_list:
                for x in res_list:
                    if i == x:
                        finally_list.append(i)

            async with aiosqlite.connect("users.db") as db:
                cursor = await db.execute("SELECT name, surname FROM users WHERE tg_id=?", (tg_id,))
                data = await cursor.fetchone()
                name, surname = data
                full_name = f"{name} {surname}".strip()
                text = text + '\n\n' + f"Отправитель: {full_name}"  + '\n' + f"Категория: {cat_to_send}"
                success = 0
                for row in finally_list:
                    try:
                        chat_id = row[0] if isinstance(row, (tuple, list)) else row
                        print(f"Получатели: {type(finally_list)}: {finally_list}")
                        await bot.send_message(chat_id=chat_id, text=text)
                        success += 1
                    except Exception as e:
                        print(f"Не удалось отправить сообщение пользователю {row}: {e}")
                await message.reply(f"Рассылка завершена. Успешно отправлено: {success}/{len(finally_list)}")


    except Exception as e:
        await message.reply("Произошла ошибка при рассылке сообщений.")
        print(f"!!!!!!!!!!Error, Glop:  {e}")
    finally:
        await state.clear()


@dp.message(StateFilter(FSMFillForm.name))
async def name_getting(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    username = message.from_user.username
    surname = None
    name = None
    role = None
    clas = None
    await add_to_database(tg_id, username, name, surname, role, clas)
    await state.update_data(name=message.text)
    data = await state.get_data()
    name = data.get("name")
    async with aiosqlite.connect('users.db') as db:
        await db.execute("UPDATE users SET name=? WHERE tg_id=?", (name, tg_id))
        await db.commit()
    await message.answer(f"Отлично, {name}! Теперь введите свою фамилию.")
    await state.set_state(FSMFillForm.surname)

@dp.message(StateFilter(FSMFillForm.surname))
async def surname_getting(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    await state.update_data(surname=message.text)
    data = await state.get_data()
    surname = data.get("surname")
    async with aiosqlite.connect('users.db') as db:
        await db.execute("UPDATE users SET surname=? WHERE tg_id=?", (surname, tg_id))
        await db.commit()
    await state.clear()
    await role_type_heandler_choice(message, tg_id)


async def role_type_heandler_choice(message: Message, tg_id: int):
    btn_student = InlineKeyboardButton(text="Ученик", callback_data="btn_student")
    btn_teacher = InlineKeyboardButton(text="Преподавательский состав", callback_data="btn_teacher")
    btn_admin = InlineKeyboardButton(text="Обратиться в поддержку", callback_data="btn_admin")
    kb_role = InlineKeyboardMarkup(inline_keyboard=[[btn_student],
                                                    [btn_teacher],
                                                    [btn_admin]])
    await bot.send_message(tg_id, "Давайте определимся с вашим статусом:", reply_markup=kb_role)

@dp.callback_query(F.data.in_(["btn_student", "btn_teacher", "btn_admin"]))
async def role_type_heandler(call: CallbackQuery, state: FSMContext):
    role_type = call.data
    tg_id = call.from_user.id
    if role_type == "btn_student":

        message_id = call.message.message_id
        role = role_student
        async with aiosqlite.connect('users.db') as db:
            await db.execute("UPDATE users SET role=? WHERE tg_id=?", (role, tg_id))
            await db.commit()
            btn_ten = InlineKeyboardButton(text="10", callback_data="btn_ten")
            btn_eleven = InlineKeyboardButton(text="11", callback_data="btn_eleven")
            btn_back = InlineKeyboardButton(text="Вернуться назад", callback_data="btn_back")
            kb_clas = InlineKeyboardMarkup(inline_keyboard=[[btn_ten],
                                                            [btn_eleven],
                                                            [btn_back]])
            await bot.edit_message_text(chat_id=tg_id, message_id=message_id,
                                        text="Хорошо, теперь выберите свою параллель!", reply_markup=kb_clas)
    if role_type == "btn_teacher":
        btn_yes = InlineKeyboardButton(text="Да!", callback_data="btn_yes")
        btn_no = InlineKeyboardButton(text="Нет, вернуться назад", callback_data="btn_back")
        kb = InlineKeyboardMarkup(inline_keyboard=[[btn_yes],
                                                   [btn_no]])
        await call.message.edit_text("Вы являетесь преподавателем?", reply_markup=kb)

    if role_type == "btn_admin":
        btn_back = InlineKeyboardButton(text="Вернуться назад", callback_data="btn_back")
        kb = InlineKeyboardMarkup(inline_keyboard=[[btn_back]])
        await bot.send_message(tg_id, "Опишите, по какому вопросу вы хотите обратиться в поддержку.", reply_markup=kb)
        await state.set_state(FSMFillForm.report)


@dp.callback_query(F.data == "btn_back")
async def backwd(call: CallbackQuery, state: FSMContext):
    tg_id = call.from_user.id
    await role_type_heandler_choice(call, tg_id)




@dp.callback_query(F.data == "btn_yes")
async def verify_proc(call: CallbackQuery, state: FSMContext):
    decision = call.data
    user_name = call.from_user.username
    tg_id = call.from_user.id
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute("SELECT name, surname FROM users WHERE tg_id=?", (tg_id,))
        data = await cursor.fetchone()
        name, surname = data
        full_name = f"{name} {surname}".strip()

        await call.message.edit_text("Хорошо, ожидайте подтверждения!")
        button_yes = InlineKeyboardButton(text="Подтвердить", callback_data=f"verificate_{tg_id}")
        button_no = InlineKeyboardButton(text="Нет", callback_data=f"verificateno_{tg_id}")
        kb = InlineKeyboardMarkup(inline_keyboard=[[button_yes],
                                                   [button_no]])
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Зарегестрировался новый пользователь! \n{full_name}: \nusername: {user_name}\nid: {tg_id}."
                                                           f"\n\nЯвляется ли пользователь преподавателем?", reply_markup=kb)


@dp.callback_query(F.data.startswith("verificate"))
async def verificate(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split("_")[1])
    type = call.data
    study_button = InlineKeyboardButton(text="Учеба", callback_data="btn_study")
    sport_button = InlineKeyboardButton(text="Спорт", callback_data="btn_sport")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[study_button],
                                                     [sport_button]])
    if type.startswith("verificateno"):
        await bot.send_message(tg_id, "К сожалению, вы не прошли верификацию. Попробуйте еще раз или обратитесь в поддержку!")
        await role_type_heandler_choice(call, tg_id)
    else:
        async with aiosqlite.connect('users.db') as db:
            await db.execute("UPDATE users SET role=? WHERE tg_id=?", (role_teacher, tg_id))
            await db.commit()
            await bot.send_message(tg_id, "Вы прошли верификацию! \n\nВот ссылка на чат преподавателей: \nhttps://t.me/+g11oEN8U3rAzNmEy")
            await bot.send_message(tg_id,
                "Хорошо, теперь выберите категорию, информацию из которой вы желаете получать!")
            await bot.send_message(tg_id, text="Доступные категории:", reply_markup=keyboard)


@dp.message(F.text == "/report")
async def btn_admin(message: Message, state: FSMContext):
    await message.answer("Опишите, по какому вопросу вы хотите обратиться в поддержку.")
    await state.set_state(FSMFillForm.report)



@dp.message(StateFilter(FSMFillForm.report))
async def report(message: Message, state: FSMContext):
    await state.update_data(report=message.text)
    data = await state.get_data()
    username = message.from_user.username
    report_text: str = data.get("report") + f"\n\nСообщение от пользователя: @{username}"
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=report_text)
    print(report_text)
    await message.answer("Ваше сообщение доставлено! В скором времени с вами свяжутся.")
    await main_menu(message)


@dp.callback_query(lambda c: c.data in ["btn_ten", "btn_eleven"])
async def ten_or_eleven(call: CallbackQuery, state: FSMContext):
    tg_id = call.from_user.id
    message_id = call.message.message_id
    if call.data == "btn_ten":
        clas = "10"
    else:
        clas = "11"
    async with aiosqlite.connect('users.db') as db:
        await db.execute("UPDATE users SET clas=? WHERE tg_id=?", (clas, tg_id))
        await db.commit()
    await call.message.edit_text("Хорошо, теперь выберите категорию, информацию из которой вы желаете получать!")
    study_button = InlineKeyboardButton(text="Учеба", callback_data="btn_study")
    sport_button = InlineKeyboardButton(text="Спорт", callback_data="btn_sport")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[study_button],
                                              [sport_button]])
    tg_id = call.from_user.id
    await bot.send_message(tg_id, text="Доступные категории:", reply_markup=keyboard)





@dp.callback_query(lambda c: c.data in ["btn_study", "btn_sport"])
async def study_choice1(call: CallbackQuery):
    tg_id = call.from_user.id
    if call.data == "btn_study":
        category = "study"
    elif call.data == "btn_sport":
        category = "sport"
    study_button = InlineKeyboardButton(text="Учеба", callback_data="btn_study")
    sport_button = InlineKeyboardButton(text="Спорт", callback_data="btn_sport")
    all_button = InlineKeyboardButton(text='Это все!', callback_data="btn_alls")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[study_button],
                                                     [sport_button],
                                                     [all_button]])


    count = await count_check(tg_id)
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute(f"SELECT {category} FROM users WHERE tg_id=?", (tg_id,))
        data = await cursor.fetchone()
        if data[0] == 0:
            count += 1
            flag = True
        else:
            count -= 1
            flag = False
        print(count)
        print(data[0])
    async with aiosqlite.connect('users.db') as db:
        await db.execute(f"UPDATE users SET {category}=? WHERE tg_id=?", (flag, tg_id))
        await db.commit()
    await bot.send_message(tg_id, f"Хорошо, желаете выбрать еще что-либо?")
    await bot.send_message(tg_id, f"Доступные категории: \n\nВыбрано {count}/2 категорий!", reply_markup=keyboard)


if __name__ == '__main__':
    dp.run_polling(bot)
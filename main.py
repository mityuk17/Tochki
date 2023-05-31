import datetime
import geopy.distance
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import db
import config


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    empty = State()
    get_sex = State()
    get_age = State()
    get_geolocation = State()
    change_sex = State()
    change_age = State()
    get_event = State()


@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    check = await db.check_user_exists(message.from_user.id)
    if not check:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Мужской', callback_data='set_sex_m'))
        kb.add(types.InlineKeyboardButton(text='Женский', callback_data='set_sex_w'))
        await message.answer('''Похоже, что вы тут впервые. Чтобы пользоваться ботом предоставьте нам немного информвции о себе
Выберите ваш пол:''', reply_markup=kb)
        await States.get_sex.set()
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Просмотр событий', callback_data='watch_events'))
    kb.add(types.InlineKeyboardButton(text='Ближайшие события на сегодня', callback_data='today_events'))
    kb.add(types.InlineKeyboardButton(text='Настройки профиля', callback_data='settings'))
    kb.add(types.InlineKeyboardButton(text='Предложить своё событие', callback_data='offer_event'))
    await message.answer('Выберите действие:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'start', state='*')
async def start_callback(callback_query: types.CallbackQuery, state: FSMContext):
    print('check50')
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Просмотр событий', callback_data='watch_events'))
    kb.add(types.InlineKeyboardButton(text='Ближайшие события на сегодня', callback_data='today_events'))
    kb.add(types.InlineKeyboardButton(text='Настройки профиля', callback_data='settings'))
    kb.add(types.InlineKeyboardButton(text='Предложить своё событие', callback_data='offer_event'))
    await callback_query.message.answer('Выберите действие:', reply_markup=kb)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda query: query.data == 'today_events')
async def today_events(callback_query: types.CallbackQuery):
    kb = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    kb.add(types.KeyboardButton(text='Поделиться геопозицией', request_location=True))
    await callback_query.message.answer('Пришлите вашу геопозицию', reply_markup=kb)
    await States.get_geolocation.set()


@dp.message_handler(state=States.get_geolocation, content_types=['location'])
async def get_location(message: types.Message, state: FSMContext):
    print('check71')
    lat = message.location.latitude
    lon = message.location.longitude
    await States.empty.set()
    async with state.proxy() as data:
        data['lat'] = lat
        data['lon'] = lon
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Посмотреть объявления', switch_inline_query_current_chat='local_events'))
    await message.answer('Выберите действие:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'watch_events', state='*')
async def watch_events(callback_query: types.CallbackQuery):
    print('check84')
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Посмотреть события для вас', switch_inline_query_current_chat='personal_events'))
    kb.add(types.InlineKeyboardButton(text='Посмотреть события по тегам', callback_data='events_by_tag'))
    kb.add(types.InlineKeyboardButton(text='Посмотреть все события.', switch_inline_query_current_chat='all_events'))
    await callback_query.message.edit_text('Выберите действие:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'events_by_tag', state='*')
async def events_by_tag(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup(row_width=2)
    tags = await db.get_tags()
    for tag in tags:
        kb.add(types.InlineKeyboardButton(text=tag[1], switch_inline_query_current_chat=f'tag_{tag[0]}'))
    kb.add(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await callback_query.message.edit_text('Выберите тег:', reply_markup=kb)


@dp.inline_handler(state='*')
async def inlines(inline_query: types.InlineQuery, state: FSMContext):
    query = inline_query.query
    user_id = inline_query.from_user.id
    user = await db.get_user(user_id)
    if query == 'personal_events':
        personal_events = []
        events = await db.get_events()
        if len(events) == 0:
            await inline_query.answer([], cache_time=60, is_personal=True,
                                      switch_pm_text='Не найдено подходящих мероприятий', switch_pm_parameter='None')
        for event in events:
            if (set(event.get('tags')) & set(user.get('active_tags'))) and user.get('age') in range(event.get('age'[0], event.get('age')[1]+1)):
                personal_events.append(event)
        if not inline_query.offset:
            border = 0
        else:
            border = int(inline_query.offset)
        answer = list()
        for event in personal_events[border: border+50]:
            answer.append(types.InlineQueryResultArticle(
                thumb_url=event.get('thumbnail_url'),
                id=event.get('id'),
                title=event.get('name'),
                description=f'{event.get("date")}',
                input_message_content=types.InputTextMessageContent(f'/event {event.get("id")}')))
        await inline_query.answer(answer, cache_time=60, is_personal=True,
                                  switch_pm_text='Не найдено подходящих мероприятий', switch_pm_parameter='None')
    elif query == 'all_events':
        events = await db.get_events()
        if len(events) == 0:
            await inline_query.answer([], cache_time=30, is_personal=True,
                                      switch_pm_text='Не найдено подходящих мероприятий', switch_pm_parameter='None')
        if not inline_query.offset:
            border = 0
        else:
            border = int(inline_query.offset)
        answer = list()
        for event in events[border: border+50]:
            answer.append(types.InlineQueryResultArticle(
                thumb_url=event.get('thumbnail_url'),
                id=event.get('id'),
                title=event.get('name'),
                description=f'{event.get("date")}',
                input_message_content=types.InputTextMessageContent(f'/event {event.get("id")}')))
        await inline_query.answer(answer, cache_time=30, is_personal=True,
                                    switch_pm_text='Не найдено подходящих мероприятий', switch_pm_parameter='None')
    elif query.startswith('tag_'):
        tag_id = int(query.split('_')[-1])
        events = await db.get_events_by_tag(tag_id)
        if len(events) == 0:
            await inline_query.answer([], cache_time=30, is_personal=True,
                                      switch_pm_text='Не найдено подходящих мероприятий', switch_pm_parameter='None')
        if not inline_query.offset:
            border = 0
        else:
            border = int(inline_query.offset)
        answer = list()
        for event in events[border: border + 50]:
            answer.append(types.InlineQueryResultArticle(
                thumb_url=event.get('thumbnail_url'),
                id=event.get('id'),
                title=event.get('name'),
                description=f'{event.get("date")}',
                input_message_content=types.InputTextMessageContent(f'/event {event.get("id")}')))
        await inline_query.answer(answer, cache_time=30, is_personal=True,
                                  switch_pm_text='Не найдено подходящих мероприятий', switch_pm_parameter='None')
    elif query == 'local_events':
        async with state.proxy() as data:
            lat = data.get('lat')
            lon = data.get('lon')
            coords_user = (lat, lon)
        events = await db.get_events()
        personal_events = list()
        for event in events:
            date = event.get('date')
            coordinates = tuple(event.get('coordinates'))
            if geopy.distance.geodesic(coords_user, coordinates).km <= 3:
                if datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').timestamp() in range(int(datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day, 0,0,0,0).timestamp()), int(datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day+1, 0,0,0,0).timestamp())):
                    personal_events.append(event)
        if not inline_query.offset:
            border = 0
        else:
            border = int(inline_query.offset)
        answer = list()
        for event in personal_events[border: border + 50]:
            answer.append(types.InlineQueryResultArticle(
                thumb_url=event.get('thumbnail_url'),
                id=event.get('id'),
                title=event.get('name'),
                description=f'{event.get("date")}',
                input_message_content=types.InputTextMessageContent(f'/event {event.get("id")}')))
        await inline_query.answer(answer, cache_time=30, is_personal=True,
                                  switch_pm_text='Не найдено подходящих мероприятий', switch_pm_parameter='None')


@dp.message_handler(commands='event', state='*')
async def give_event(message: types.Message, state: FSMContext):
    await state.finish()
    if not len(message.text.split()) == 2:
        return
    event_id = int(message.text.split()[-1])
    event = await db.get_event_by_id(event_id)
    text = f'''{event.get('name')}
Дата: {event.get('date')}
Место проведения: {event.get('location')}
{event.get('description')}
Теги: '''
    for tag in await db.get_tags():
        if tag[0] in event.get('tags'):
            text += f'#{tag[1] }'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await message.answer_photo(photo=event.get('thumbnail_url'), caption=text, reply_markup=kb)
    await message.answer_location(latitude=float(event.get('coordinates')[0]), longitude=float(event.get('coordinates')[1]))


@dp.callback_query_handler(lambda query: query.data.startswith('set_sex_'), state=States.get_sex)
async def set_sex(callback_query: types.CallbackQuery, state: FSMContext):
    sex = callback_query.data.split('_')[-1]
    async with state.proxy() as data:
        data['sex'] = sex
    await callback_query.message.edit_text('''Пришлите ваш возраст:''')
    await States.get_age.set()


@dp.message_handler(state=States.get_age)
async def get_age(message: types.Message, state: FSMContext):
    age = message.text
    if not age.isdigit():
        await message.answer('Неверный формат')
        return
    async with state.proxy() as data:
        data['age'] = age
        data['tags'] = []
    kb = types.InlineKeyboardMarkup(row_width=2)
    tags = await db.get_tags()
    for tag in tags:
        kb.add(types.InlineKeyboardButton(text=f'❌ {tag[1]}', callback_data=f'switch_tag_{tag[0]}'))
    kb.add(types.InlineKeyboardButton(text='Подтвердить', callback_data=f'finish_tags'))
    await message.answer('Выберите интересующие вас теги:', reply_markup=kb)
    await States.empty.set()


@dp.callback_query_handler(lambda query: query.data.startswith('switch_tag_'), state='*')
async def switch_tags(callback_query: types.CallbackQuery, state: FSMContext):
    tag_id = int(callback_query.data.split('_')[-1])
    async with state.proxy() as data:
        personal_tags = data['tags']
    if tag_id in personal_tags:
        personal_tags.remove(tag_id)
    else:
        personal_tags.append(tag_id)
    async with state.proxy() as data:
        data['tags'] = personal_tags
    tags = await db.get_tags()
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag in tags:
        if tag[0] in personal_tags:
            kb.add(types.InlineKeyboardButton(text=f'✅ {tag[1]}', callback_data=f'switch_tag_{tag[0]}'))
        elif tag[0] not in personal_tags:
            kb.add(types.InlineKeyboardButton(text=f'❌ {tag[1]}', callback_data=f'switch_tag_{tag[0]}'))
    kb.add(types.InlineKeyboardButton(text='Подтвердить', callback_data=f'finish_tags'))
    await callback_query.message.edit_text('Выберите интересующие вас теги', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'finish_tags', state='*')
async def finish_tags(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        check = await db.check_user_exists(callback_query.from_user.id)
        if check:
            personal_tags = ' '.join(list(map(str, data['tags'])))
            await db.change_active_tags(callback_query.from_user.id, personal_tags)
        else:
            age = data['age']
            sex = data['sex']
            personal_tags = ' '.join(list(map(str, data['tags'])))
            user = {
                'user_id': callback_query.from_user.id,
                'admin': False,
                'age': age,
                'sex': sex,
                'active_tags': personal_tags
            }
            await db.create_user(user)
    await start_callback(callback_query, state)


@dp.callback_query_handler(lambda query: query.data == 'settings', state='*')
async def profile_settings(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    user = await db.get_user(callback_query.from_user.id)
    text = f'''Пользователь {callback_query.from_user.id}
Имя пользователя: {callback_query.from_user.username}
Возраст: {user.get('age')}
Пол: {'Мужской' if user.get('sex') == 'm' else 'Женский'}'''
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Изменить возраст', callback_data='change_age'))
    kb.add(types.InlineKeyboardButton(text='Изменить пол', callback_data='change_sex'))
    kb.add(types.InlineKeyboardButton(text='Изменить активные теги', callback_data='change_tags'))
    kb.add(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await callback_query.message.edit_text(text=text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('change_'))
async def change_settings(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    target = callback_query.data.split('_')[-1]
    if target == 'age':
        await States.change_age.set()
        await callback_query.message.edit_text('Пришлите новый возраст:')
    elif target == 'sex':
        await States.change_sex.set()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Мужской', callback_data='change_sex_m'))
        kb.add(types.InlineKeyboardButton(text='Женский', callback_data='change_sex_w'))
        await callback_query.message.edit_text('Выберите пол:', reply_markup=kb)
    elif target == 'tags':
        personal_tags = (await db.get_user(callback_query.from_user.id)).get('active_tags')
        if not personal_tags:
            personal_tags = list()
        async with state.proxy() as data:
            data['tags'] = personal_tags
        tags = await db.get_tags()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for tag in tags:
            if tag[0] in personal_tags:
                kb.add(types.InlineKeyboardButton(text=f'✅ {tag[1]}', callback_data=f'switch_tag_{tag[0]}'))
            elif tag[0] not in personal_tags:
                kb.add(types.InlineKeyboardButton(text=f'❌ {tag[1]}', callback_data=f'switch_tag_{tag[0]}'))
        kb.add(types.InlineKeyboardButton(text='Подтвердить', callback_data=f'finish_tags'))
        await callback_query.message.edit_text('Выберите интересующие вас теги', reply_markup=kb)


@dp.message_handler(state=States.change_age)
async def change_age(message: types.Message, state:FSMContext):
    await state.finish()
    age = message.text
    if not age.isdigit():
        await message.answer('Неверный формат')
        return
    await db.change_age(message.from_user.id, age)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await message.answer('Возраст изменён', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('change_sex_'), state=States.change_sex)
async def change_sex(callback_query: types.CallbackQuery, state:FSMContext):
    await state.finish()
    sex = callback_query.data.split('_')[-1]
    await db.change_sex(callback_query.from_user.id, sex)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await callback_query.message.edit_text('Пол изменён', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'offer_event', state='*')
async def offer_event(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await callback_query.message.edit_text('Предоставьте информацию по мероприятию:', reply_markup=kb)
    await States.get_event.set()


@dp.message_handler(state=States.get_event)
async def get_event_information(message: types.Message, state: FSMContext):
    await state.finish()
    #await bot.copy_message(chat_id=547380383, from_chat_id=message.from_user.id, message_id=message.message_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Главное меню', callback_data='start'))
    await message.answer('Информация о мероприятии была передана администрации.', reply_markup=kb)


if __name__ == '__main__':
    db.start()
    executor.start_polling(dp, skip_updates=True)
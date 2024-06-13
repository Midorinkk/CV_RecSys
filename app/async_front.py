import json

import streamlit as st

import aiohttp
import asyncio

from app.async_model import SMALL_MAPPINGS

# сколько вакансий показывать на страничке
ITEMS_PER_PAGE = 5

# маппинг pydantic-модели с полем формы
FORM_MAPPING = {'fio': 'ФИО',
                'res_title': 'Заголовок резюме',
                'City': 'Город',
                'graph': 'График работы',
                'microcat_name': 'Сфера деятельности',
                'res_des': 'Текст резюме'}

# подгружаем города, график работы и сферу деятельности
with open('./app/data/categories.json', 'r') as f:
    CATEGORIES = json.load(f)

# кастомизация вкладки
st.set_page_config(page_title='Поиск работы',
                   page_icon='🔍')
st.title('Новое резюме')

# контейнер для формы
form_container = st.container()
# контейнер для рекомендаций
recs_container = st.container()

# инициализация состояния для переключения по страницам
if 'page' not in st.session_state:
    st.session_state['page'] = 0


async def fetch_recommendations(resume_data: dict):
    """
    получение рекомендаций с ручки /recommend

    resume_data: dict - данные из формы
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post('http://app:8000/recommend',
                                    json=resume_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Ошибка сервера: {response.status} {await response.text()}")
        except aiohttp.ClientError as e:
            raise Exception(f"Ошибка подключения: {str(e)}")
        except Exception as e:
            raise Exception(f"Произошла ошибка: {str(e)}")


with form_container:
    # форма для ввода резюме
    success_flg = True
    with st.form('res_form', clear_on_submit=False):
        st.write('Заполните информацию о себе')

        fio = st.text_input('ФИО')
        res_title = st.text_input('Заголовок резюме (например, Python-разработчик)')
        city = st.selectbox('Город', CATEGORIES['CITIES'])
        graph = st.selectbox('График работы', CATEGORIES['GRAPHS'])
        microcat = st.selectbox('Сфера деятельности', CATEGORIES['CATS'])
        res_text = st.text_area('Текст резюме')

        submit_btn = st.form_submit_button('Отправить резюме')

        # если нажата кнопка, собираем данные и проверяем, что все заполнено
        if submit_btn:
            form_results = {'fio': fio,
                            'res_title': res_title,
                            'City': city,
                            'graph': graph,
                            'microcat_name': microcat,
                            'res_des': res_text}

            for field_name, field_value in form_results.items():
                if not field_value.strip() or field_value.split()[0] == 'Выберите':
                    st.error(f'Поле "{FORM_MAPPING[field_name]}" является обязательным')
                    success_flg = False

            # если все ок, получаем рекоммендации
            if success_flg:
                with st.spinner('Идет обработка...'):
                    try:
                        recommendations = asyncio.run(fetch_recommendations(form_results))
                        if recommendations:
                            st.session_state['recommendations'] = recommendations
                            st.session_state['page'] = 0
                    except Exception as e:
                        st.error(f"Ошибка при получении рекомендаций: {str(e)}")
                        recommendations = []

                if recommendations:
                    st.session_state['recommendations'] = recommendations
                    st.session_state['page'] = 0

# если рекоммендации подгрузились, отрисовываем по 5 на странице
if 'recommendations' in st.session_state:
    with recs_container:
        recommendations = st.session_state['recommendations']
        total_pages = (len(recommendations) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        # получаем текущую страницу рекомендаций
        start_idx = st.session_state['page'] * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_recs = recommendations[start_idx:end_idx]

        st.write(f'Рекомендованные вакансии (Страница {st.session_state["page"] + 1} из {total_pages}):')
        for idx, rec in enumerate(current_recs):
            # в заголовок основные харакетристики, описание открываем по клику
            location = rec['City'] if rec['City'] not in SMALL_MAPPINGS else f"{rec['City']} ({rec['Region']})"

            vac_header = '\n\n'.join([f":blue[{rec['vac_title']}]",
                                      f"Подходит вам на :red[{round(100 * rec['norm_score'])} %]",
                                      f"Локация: {location}",
                                      f"График работы: {rec['graph'] if rec['graph'] is not None else 'Не указан'}",
                                      f"Сфера деятельности: {rec['microcat_name']}"]
                                    )

            with st.expander(vac_header):
                st.write(f"Описание: {rec['vac_des']}")

        # кнопки вперед/назад
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button('Назад'):
                if st.session_state['page'] > 0:
                    st.session_state['page'] -= 1
                    st.rerun()
        with col3:
            if st.button('Вперед'):
                if st.session_state['page'] < total_pages - 1:
                    st.session_state['page'] += 1
                    st.rerun()

# Оценка проекта до взятия в работу

## 1. **Потенциал проекта. Насколько важно решить задачу?**

![stat](https://github.com/Midorinkk/CV_RecSys/assets/55846379/00146a81-4974-4197-bb14-b75ff5f5aa93)

Опираясь на данные сервиса Авито Работа, ~55% вакансий за неделю получают всего 1 отклик от кандидатов -> необходим сервис, рекомендующий резюме, чтобы работодателям не приходилось ждать, пока соискатели сами откликнутся.

Кроме того, есть небольшой процент массовых вакансий, которые за неделю получают более 100 откликов. Предлагаемый сервис может сэкономить время таким работадателям путём отсеивания нерелевантных резюме и ранжирования релевантных.
 

## 2. **Есть ли простое решение? Насколько оно решит задачу? Сложно ли поддерживать такое решение?**

- **Простое решение**: мэтчинг по полному совпадению названия вакансии и резюме.
- **Эффективность решения**: полное совпадение отлавливает всего ~2% целевых событий (контакт соискатель-работодатель) -> необходимо более сложное решение.
- **Сложность поддержки**: так как бейзлайн проверяет полное соответствие названий, решение легко поддерживается.

## 3. **Реалистичность решения проблемы с помощью машинного обучения**

Существует несколько успешных кейсов решения этой проблемы с использованием машинного и глубокого обучения.

Примеры:
- **hh.ru**: https://habr.com/ru/companies/hh/articles/347276/
- **LinkedIn**: https://analyticsindiamag.com/how-linkedin-is-using-deep-learning-to-increase-hiring-efficiency-amid-recession/

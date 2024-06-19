На виртуальной машине открываем порт 10000.
В именах пользователей, названиях ресторанов/меню используем латиницу
Последовательно выполняем следующие пункты:
1) sudo docker compose up -d
2) sudo docker-compose -f docker-compose-nginx.yml --project-name nginx-net up -d
3) на этом шаге необходимо создать админа.
   Для этого вбиваем следующие команды:
   docker exec -it res_app bash
   flask shell
   u=User(username='admin', email='admin@test.ru', role=True)
   u.set_password('dog')
   db.session.add(u)
   db.session.commit()
   выходим из консоли и контейнера
5) Ссылка для перехода на основной сайт: http://localhost:10000
6) В админской панеле можем создать простого пользователя, для пользователя создаем ресторан и меню
7) Оформив подписку можем перейти на сайт с меню по ссылке вида: http://название_ресторана-название_меню.localhost
8) Затем переходим в админскую панель по ссылке: http://название_ресторана-название_меню.localhost/admin/токен_админа (токен берем из админской панели основного сайта в таблице users)
9) Создаем шаблон для меню(можно выбрать из существующих), потом добавляем блюда

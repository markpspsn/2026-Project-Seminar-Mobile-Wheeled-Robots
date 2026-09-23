# Практическая работа 1 — вариант 12

Пакет `draw_12` рисует число **12** в `turtlesim`. Одна программа `digit_drawer` запускается дважды: для черепах `digit_one` и `digit_two`. Движение управляется сообщениями `/pose` и командами `/cmd_vel`; телепортация не используется.

## Сборка и запуск

Команды ниже выполняются **внутри контейнера** курса (`zsh`). Каталог `practices/` репозитория смонтирован в `~/practices_ws/src/` контейнера.

```bash
cd ~/practices_ws
colcon build --symlink-install --packages-select draw_12
source install/setup.zsh
ros2 launch draw_12 number.launch.py
```

Launch сам запускает `turtlesim`, удаляет стандартную `turtle1`, создаёт две черепахи и запускает два экземпляра управляющего узла. Результат — рядом стоящие прямолинейные цифры 1 и 2. Чтобы завершить запуск, нажмите `Ctrl+C` в терминале с launch.

## Диагностика

В другом терминале того же контейнера (после `source ~/practices_ws/install/setup.zsh`) можно посмотреть:

```bash
ros2 node list
ros2 topic list
ros2 service list
ros2 topic echo /digit_one/pose
ros2 topic echo /digit_two/cmd_vel
rqt_graph
```

Для видео запишите запуск команды `ros2 launch`, весь процесс рисования, конечный рисунок и открытый `rqt_graph` с видимыми связями обоих узлов `digit_one_drawer` и `digit_two_drawer` через соответствующие топики с `turtlesim`. Откройте доступ к видео по ссылке и отправьте преподавателю ссылки на видео и Pull request.

# Практическая работа 1 — вариант 10

Пакет `draw_10` рисует число **10** в `turtlesim`. Одна программа `digit_drawer` запускается дважды: для черепах `digit_one` и `digit_zero`. Движение управляется сообщениями `/pose` и командами `/cmd_vel`; телепортация не используется.

## Сборка и запуск

Команды ниже выполняются **внутри контейнера** курса (`zsh`). Каталог `practices/` репозитория смонтирован в `~/practices_ws/src/` контейнера.

```bash
cd ~/practices_ws
colcon build --symlink-install --packages-select draw_10
source install/setup.zsh
ros2 launch draw_10 number.launch.py
```

Launch сам запускает `turtlesim`, удаляет стандартную `turtle1`, создаёт две черепахи и запускает два экземпляра управляющего узла. Результат — рядом стоящие прямолинейные цифры 1 и 0. Чтобы завершить запуск, нажмите `Ctrl+C` в терминале с launch.

## Диагностика

В другом терминале того же контейнера (после `source ~/practices_ws/install/setup.zsh`) можно посмотреть:

```bash
ros2 node list
ros2 topic list
ros2 service list
ros2 topic echo /digit_one/pose
ros2 topic echo /digit_zero/cmd_vel
rqt_graph
```

Для видео запишите запуск команды `ros2 launch`, весь процесс рисования, конечный рисунок и открытый `rqt_graph` с видимыми связями обоих узлов `digit_one_drawer` и `digit_zero_drawer` через соответствующие топики с `turtlesim`. Откройте доступ к видео по ссылке и отправьте преподавателю ссылки на видео и Pull request.

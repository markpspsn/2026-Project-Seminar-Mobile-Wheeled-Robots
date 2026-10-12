# Практическая работа 2 — вариант 10

Пакет `practice02_webots` запускает TurtleBot3 Burger в Webots на площадке размером **6 × 6 м** с полом и стенами.

В центре расположены два серых неподвижных препятствия, образующих число **10**. Они описаны отдельными файлами `DigitOne.proto` и `DigitZero.proto`. Робот управляется командами скорости через топик `/cmd_vel`.

Решение создано на основе пакета `example_webots` из репозитория курса.

## Подготовка

Потребуется настроенное окружение курса с Docker, ROS2 Jazzy и Webots для Linux. Инструкция по его сборке и настройке находится в https://github.com/PathPlanning/2026-Project-Seminar-Mobile-Wheeled-Robots/blob/main/README.md.

Используйте ветку `practice-02` этого репозитория. Файлы `.env` и `.env.local` должны быть подготовлены по инструкции курса.

Ниже предполагается, что репозиторий находится в:

```text
~/Projects/mobile-robots-project-seminar
```

Если он находится в другом месте, замените этот путь в командах `cd`.

## Терминал A — сборка и запуск симуляции

Откройте терминал Ubuntu и перейдите в корень репозитория:

```bash
cd ~/Projects/mobile-robots-project-seminar
```

Запустите контейнер:

```bash
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-linux.yaml up -d
```

Войдите в контейнер:

```bash
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-linux.yaml exec -it ros2-base zsh
```

**Дальнейшие команды терминала A выполняются внутри контейнера.**

Перейдите в рабочее пространство практик:

```bash
cd ~/practices_ws
```

Соберите пакет:

```bash
colcon build --symlink-install --packages-select practice02_webots
```

После успешной сборки подключите его к текущему терминалу:

```bash
source install/setup.zsh
```

Запустите симуляцию:

```bash
ros2 launch practice02_webots spawn_robot.launch.py
```

Откроется Webots с видом сверху. На площадке будут видны число **10** и робот ниже него. Launch-файл запускает сцену, драйвер робота и контроллеры колёс.

Пока команды движения не отправляются, робот стоит на месте. Оставьте терминал A открытым.

## Терминал B — движение вокруг числа

Откройте второй терминал Ubuntu, например через **Ctrl+Alt+T**.

Перейдите в корень репозитория:

```bash
cd ~/Projects/mobile-robots-project-seminar
```

Войдите в тот же работающий контейнер:

```bash
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-linux.yaml exec -it ros2-base zsh
```

**Дальнейшие команды терминала B выполняются внутри контейнера.**

Подключите собранный пакет:

```bash
source ~/practices_ws/install/setup.zsh
```

Запустите публикацию команд скорости:

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/TwistStamped "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'base_link'}, twist: {linear: {x: 0.176, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.08}}}"
```

Робот начнёт двигаться против часовой стрелки по окружности вокруг обеих цифр. Команды отправляются с частотой **10 Гц**, линейная скорость составляет **0,176 м/с**, угловая — **0,08 рад/с**.

Расчётный радиус окружности — **2,2 м**. Один оборот занимает примерно **79 секунд симуляционного времени**. Наблюдайте за полным кругом в Webots: робот должен обойти обе цифры без столкновений.

После первого круга движение продолжается, пока публикация команд не будет остановлена.

## Остановка

В терминале B нажмите **Ctrl+C**, затем отправьте команду нулевой скорости:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.0}, angular: {z: 0.0}}}"
```

Для завершения симуляции нажмите **Ctrl+C в терминале A**.
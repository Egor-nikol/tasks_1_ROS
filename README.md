# SHAD ROS 2 — практические задания

В этом репозитории каждое задание находится в отдельной самодостаточной папке.
Нумерация дополнена нулём, чтобы `task01` … `task10` сортировались в порядке курса.

| Задание | Тема | Ветка сдачи | Статус |
| --- | --- | --- | --- |
| `task01/` | ROS 2 graph, interfaces and actions · Hidden Gift 2.0 | `l01` | Frozen `2026.1-l01-rc2` |

## До первого занятия: проверьте Docker

Локально устанавливать ROS 2, Gazebo и Python-пакеты не нужно. Нужны Git,
запущенный Docker и Compose v2 (команда `docker compose`, не
`docker-compose`). Рекомендуется 16 ГБ RAM и 30 ГБ свободного места.

- macOS: установите и запустите
  [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/).
- Windows: установите
  [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)
  с WSL 2. Команды курса выполняйте в терминале Ubuntu/WSL, а репозиторий
  клонируйте в `~/`, не в `/mnt/c/`.
- Ubuntu 24.04: установите
  [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) и
  [Compose plugin](https://docs.docker.com/compose/install/linux/). Команды
  курса должны работать без `sudo`. При `permission denied` выполните
  [официальную post-install инструкцию](https://docs.docker.com/engine/install/linux-postinstall/)
  и полностью выйдите и войдите в систему. Членство в группе `docker` даёт
  root-level доступ к компьютеру.

Проверьте установку до занятия:

```bash
git --version
docker version
docker compose version
docker run --rm hello-world
```

Затем скачайте репозиторий и проверьте именно окружение курса:

```bash
git clone https://github.com/SHAD-ROS2/tasks.git
cd tasks/task01

# Только Linux/WSL, если id -u выводит не 1000:
export LOCAL_UID="$(id -u)"
export LOCAL_GID="$(id -g)"

docker compose pull
docker compose up -d --wait
./course doctor
```

Откройте IDE: <http://127.0.0.1:8080>, поле робота:
<http://127.0.0.1:8081>. Чтобы войти в контейнер из терминала хоста:

```bash
./course shell
course build
exit
```

После проверки остановите окружение:

```bash
docker compose down
```

Если что-то не работает, пришлите преподавателю полный вывод следующих команд,
а также название и версию ОС:

```bash
./course doctor
docker compose ps
docker compose logs --tail=200 workspace
docker version --format '{{.Server.Os}}/{{.Server.Arch}}'
```

## Задание 01

После получения репозитория:

```bash
cd task01
docker compose up -d --wait
./course doctor
```

Полная инструкция находится в `task01/README.md`. Все команды
конкретного задания запускайте из его папки. Workflow в `.github/workflows/`
даёт только формативную обратную связь; итоговая проверка выполняется отдельно.
Git-команды выполняйте на хосте из `task01/`: контейнер монтирует только папку
задания, поэтому встроенный IDE terminal намеренно не видит родительский `.git`.

Решения, закрытые тесты, roster и преподавательские инструменты в этот репозиторий
не публикуются.

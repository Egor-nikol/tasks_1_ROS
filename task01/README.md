# ROS 2 · занятие 01 — Hidden Gift 2.0

> **Release candidate:** the course-owned interface and simplified L01 scope are ready for final Docker/architecture gates. Use only a release that includes `.env` and `release.lock.json` with an immutable image digest.

> The simplified scope in `docs/Practice_L01.md` is authoritative; generated HTML/PDF are released from the same source.

**Для студента:** преподаватель выдаёт Task 01 внутри папки `task01/` после проверки образа и добавления `.env` с immutable digest. До этого release-step `docker compose up` не является поддерживаемым способом запуска задания.

Если в репозитории нет `.env` с immutable digest образа, это ещё не готовый релиз: сообщите преподавателю и не пытайтесь собирать course image во время занятия.

## Подготовка после публикации образа

```bash
# В терминале хоста, в клонированном репозитории:
docker compose up -d --wait
./course doctor
```

IDE: `http://127.0.0.1:8080`. Поле робота: `http://127.0.0.1:8081`.
Контейнер видит только содержимое `task01/`, не родительский `.git`; команды
commit/push ниже выполняйте в терминале хоста.

В терминале IDE:

```bash
course build
course run
# Во втором терминале IDE:
course goal --area 2 2 8 8
```

Стартовый код специально не решает задание. Smoke test проверяет стенд, а не решение.
Полный актуальный гайд: `docs/Practice_L01.md`.

## Что редактировать

`src/hidden_gift/hidden_gift/mission.py`: поиск подарка и подтверждение отсутствия.
`src/hidden_gift/hidden_gift/server.py`: только отображение `found/absent` в успешный action result для core; validation/cancellation infrastructure уже предоставлена.
Навигация `drive_to`, покрытие `raster` и измерение прямоугольника `RectangleProbe` уже предоставлены.

Обязательный scope: окружение и graph, один корректный goal, `found`, `absent`, простой feedback и explicit stop. Concurrency/busy, health responsiveness, sensor loss/deadline, namespaces, QoS и callback synchronization будут оцениваться в следующих неделях.

## Проверка и сдача

```bash
course test --case found
course test --case absent
```

Расширения после core: `course test --case inside`, `course test --case cancel`.

На хосте:

```bash
git switch -c l01  # только один раз; если ветка есть: git switch l01
git add src/hidden_gift reports/environment.json docs/verification.md
git commit -m "L01: implement and verify Hidden Gift action"
git push -u origin l01
git rev-parse HEAD
```

Ни локальный `score.json`, ни зелёная галочка в изменяемом студентом workflow не являются итоговой оценкой. Преподаватель проверяет точный commit SHA внешним observer.

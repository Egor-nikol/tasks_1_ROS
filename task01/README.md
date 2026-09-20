# ROS 2 · занятие 01 — Hidden Gift 2.0

> **Frozen release `2026.1-l01-rc2`:** `.env` and `release.lock.json` bind this task to the validated multi-architecture image manifest. Do not replace it with a mutable tag.

> The simplified scope in `docs/Practice_L01.md` is authoritative; generated HTML/PDF are released from the same source.

**Для студента:** Task 01 находится внутри папки `task01/`. Выполняйте команды ниже из этой папки; образ уже выбран по immutable digest.

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
git switch master
git add src/hidden_gift reports/environment.json docs/verification.md
git commit -m "L01: implement and verify Hidden Gift action"
git push origin master
```

**Commit SHA никуда вписывать и коммитить не нужно:** он появляется автоматически
после `git commit`. От вас требуется только оставить решение внутри `task01/` и
выполнить `git push origin master` до дедлайна. Преподаватель сам сохранит
идентификатор отправленного коммита. Убедитесь на GitHub, что ваши изменения
появились в ветке `master`.

Ни локальный `score.json`, ни зелёная галочка в изменяемом студентом workflow не
являются итоговой оценкой. Преподаватель проверяет автоматически зафиксированный
коммит внешним observer.

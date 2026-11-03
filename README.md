# Android GSI → Google Drive

Автоматическое зеркало GSI-прошивок (Generic System Image) на Google Drive.
GitHub Actions раз в сутки проверяет свежие релизы из [`sources.json`](sources.json),
распаковывает их в **чистый `.img`** (без архивов — сразу для DSU Sideloader или fastboot), загружает на Google Drive и обновляет таблицу ниже.

## Актуальные сборки

<!-- GSI-LIST:START -->
_Пока пусто — запустите workflow **Sync GSI to Google Drive**._
<!-- GSI-LIST:END -->

## Настройка (один раз)

1. На своём ПК установите [rclone](https://rclone.org/downloads/) и выполните `rclone config`:
   новый remote с именем `gdrive`, тип `drive`, scope `drive`, авторизуйтесь в браузере.
2. Скопируйте содержимое файла конфига (`rclone config file` покажет путь).
3. В репозитории: **Settings → Secrets and variables → Actions → New repository secret**,
   имя `RCLONE_CONFIG`, значение — содержимое конфига.
4. (Необязательно) переменная `RCLONE_REMOTE`, по умолчанию `gdrive:GSI`.
5. **Actions → Sync GSI to Google Drive → Run workflow.**

Ссылки создаются через `rclone link` (доступ «всем, у кого есть ссылка»).

## Добавить другую сборку

Добавьте запись в `sources.json`: `repo` — GitHub-репозиторий с релизами,
`asset_regex` — регулярка для имени нужного файла (для большинства телефонов — `arm64-ab`).

## ⚠️ OnePlus 15R

- Нужен **разблокированный загрузчик** (сотрёт все данные).
- GSI прошивается в раздел `system` через **fastbootd**:
  ```
  adb reboot fastboot
  fastboot erase system
  fastboot flash system system.img
  fastboot -w
  fastboot reboot
  ```
- Перед прошивкой отключите проверку vbmeta:
  `fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img` (vbmeta из стоковой прошивки).
- Сохраните стоковую прошивку для отката. Всё на свой риск.

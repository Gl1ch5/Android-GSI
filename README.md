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

В `sources.json` поддерживаются три типа:

```jsonc
// GitHub Releases
{"name": "...", "repo": "owner/repo", "asset_regex": "arm64.*\\.img\\.xz$"}
// SourceForge (имя проекта из адреса sourceforge.net/projects/<project>)
{"name": "...", "type": "sourceforge", "project": "andyyan-gsi", "asset_regex": "arm64.*\\.img\\.gz$"}
// Прямые ссылки (любые: порты, файлы с форумов и т.п.)
{"name": "Мои ссылки", "type": "url", "files": [
  {"tag": "hyperos-port-v1", "file": "system.img.xz", "url": "https://..."}
]}
```

## Telegram-каналы

```json
{"name": "Mystic GSI", "type": "telegram", "channel": "имя_канала_без_@", "asset_regex": "\\.(img|xz|gz|zip|7z)$"}
```

Один раз настроить:
1. На https://my.telegram.org → **API development tools** создайте приложение, получите `api_id` и `api_hash`.
2. На ПК: `pip install telethon` и `python scripts/tg_login.py` — войдите и получите строку сессии.
3. Добавьте секреты `TG_API_ID`, `TG_API_HASH`, `TG_SESSION`.
   ⚠️ `TG_SESSION` = полный доступ к аккаунту. Лучше завести отдельный аккаунт и подписать его на нужные каналы.

Архивы `.xz/.gz/.zip/.7z` автоматически распаковываются в один `.img`.

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

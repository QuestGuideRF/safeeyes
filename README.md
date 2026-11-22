# 👁️ Safe Eyes

> **Защитите свои глаза от перенапряжения** с помощью этого простого и красивого напоминания о перерывах.

---

## 📋 Описание

**Safe Eyes** — это утилитакоторая помогает защитить ваши глаза от перенапряжения (астенопии), напоминая вам делать регулярные перерывы во время длительной работы за компьютером.

### ✨ Основные возможности

- 🔔 **Напоминания о перерывах** с упражнениями для снижения RSI
- ⌨️ **Блокировка клавиатуры** во время перерывов
- 🔔 **Уведомления** до и после перерывов
- ⏸️ **Умная пауза** при простое системы
- 🖥️ **Поддержка нескольких мониторов**
- 🎨 **Настраиваемый интерфейс**
- 🔌 **API для внешнего управления** (RPC)
- ⚙️ **Аргументы командной строки** для управления запущенным экземпляром
- 🔧 **Расширяемость через плагины**

---

## 🚀 Быстрый старт

### Скачайте и распакуйте архив
```

### Установка через pip

```bash
sudo pip3 install safeeyes
```

---

Для работы Safe Eyes требуются следующие зависимости:

- `gir1.2-appindicator3-0.1` или `gir1.2-ayatanaappindicator3-0.1`
- `gir1.2-notify-0.7`
- `libappindicator-gtk3`
- `python3-psutil`
- `xprintidle` (опционально)
- `wlrctl` (опционально, для Wayland)

---

## 💻 Аргументы командной строки

```text
usage: safeeyes [-h] [-a | -d | -e | -q | -s | -t] [--debug] [--version]

Safe Eyes защищает ваши глаза от перенапряжения, напоминая делать перерывы
во время длительной работы за компьютером.

Опциональные аргументы:
  -h, --help        показать справку и выйти
  -a, --about       показать диалог "О программе"
  -d, --disable     отключить текущий запущенный экземпляр safeeyes
  -e, --enable      включить текущий запущенный экземпляр safeeyes
  -q, --quit        завершить работу safeeyes и выйти
  -s, --settings    показать диалог настроек
  -t, --take-break  сделать перерыв сейчас
  --debug           запустить safeeyes в режиме отладки
  --status          вывести статус запущенного экземпляра safeeyes и выйти
  --version         показать номер версии программы и выйти
```

---

## 🔌 Плагины

Safe Eyes поддерживает расширяемость через систему плагинов. Дополнительные плагины доступны в отдельном репозитории: [safeeyes-plugins](https://github.com/slgobinath/safeeyes-plugins).

### Встроенные плагины

- **Audible Alert** — звуковые уведомления
- **Do Not Disturb** — режим "Не беспокоить"
- **Health Stats** — статистика здоровья
- **Media Control** — управление медиа
- **Notification** — уведомления
- **Screen Saver** — экранная заставка
- **Smart Pause** — умная пауза
- **Tray Icon** — иконка в системном трее

---

## 🛠️ Установка в виртуальном окружении

Для систем, где зависимости недоступны в репозиториях (например, CentOS 7):

1. Установите необходимые зависимости:

   ```bash
   sudo yum install python3-devel dbus dbus-devel cairo cairo-devel cairomm-devel libjpeg-turbo-devel pango pango-devel pangomm pangomm-devel gobject-introspection-devel cairo-gobject-devel
   ```

2. Создайте виртуальное окружение:

   ```bash
   mkdir ~/safeeyes
   cd ~/safeeyes/
   pip3 install virtualenv --user
   virtualenv --no-site-packages venv
   source venv/bin/activate
   pip3 install dbus-python safeeyes
   ```

3. Запустите Safe Eyes:

   ```bash
   cd ~/safeeyes
   source venv/bin/activate
   python3 -m safeeyes
   ```

Подпись относится к текущей версии проекта.

---

Автор: legenda  
Telegram: [@LEGENDA_SD](https://t.me/LEGENDA_SD)

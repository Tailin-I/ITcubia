import logging

import arcade
import json
import os


class InputManager:
    """Класс для обработки ввода с настройкой клавиш"""

    def __init__(self, config_file="settings/key_bindings.json"):
        """
        Инициализация обработчика клавиш
        config_file: имя файла для сохранения/загрузки настроек
        """
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.logger.debug(f"Инициализация KeyHandler с config_file={config_file}")

        self.keys_pressed = set()
        self.config_file = config_file

        # Конфигурация клавиш по умолчанию (в виде строк)
        self.default_key_bindings = {
            'up': ["W", "UP"],
            'down': ["S", "DOWN"],
            'left': ["A", "LEFT"],
            'right': ["D", "RIGHT"],

            'select': ["ENTER"],
            'escape': ["ESCAPE"],

            'stats': ["B"],

            'lose_health': ["H"],
            'cheat_console': ["F2"],
            'ghost_mode': ["NUM_0"],
            'debug_mode': ["NUM_1"]

        }

        # Инициализация преобразования клавиш
        self._init_key_mapping()

        # Загружаем настройки или используем значения по умолчанию
        self.key_bindings = self.load_key_bindings()

        # Конвертируем строки в коды клавиш для внутреннего использования
        self.key_codes = self._convert_strings_to_codes(self.key_bindings)

        # Состояние действий
        self.actions = {}
        self._init_actions()

        # Для отслеживания "полезного" нажатия
        self.last_valid_direction = None

    # работа с JSON
    def load_key_bindings(self):
        """
        Загружает привязки клавиш из JSON файла.
        Если файл не существует, создает его с настройками по умолчанию.
        """
        self.logger.debug(f"Попытка загрузки настроек из {self.config_file}")

        # Проверка, существует ли файл
        if os.path.exists(self.config_file):
            try:
                # Открываем файл для чтения
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    # Загружаем данные из JSON
                    saved_data = json.load(f)
                    self.logger.debug(f"Загруженные данные: {saved_data}")

                # Проверяем структуру загруженных данных
                if not isinstance(saved_data, dict):
                    self.logger.error("✗ Ошибка: загруженные данные не являются словарем")
                    return self.default_key_bindings.copy()

                # Убеждаемся, что у нас есть все необходимые действия
                result_bindings = {}
                for action, default_keys in self.default_key_bindings.items():
                    if action in saved_data:
                        # Проверяем, что сохраненные ключи являются списком строк
                        saved_keys = saved_data[action]
                        if isinstance(saved_keys, list):
                            # Проверяем, что все элементы - строки
                            if all(isinstance(key, str) for key in saved_keys):
                                result_bindings[action] = saved_keys
                                self.logger.debug(f"Действие '{action}': {saved_keys}")
                            else:
                                self.logger.warning(f"Внимание: не все ключи для '{action}' являются строками")
                                result_bindings[action] = default_keys.copy()
                        else:
                            self.logger.error(f"Неверный формат ключей для действия '{action}'")
                            result_bindings[action] = default_keys.copy()
                    else:
                        # Если действия нет в сохраненных данных, используем значения по умолчанию
                        result_bindings[action] = default_keys.copy()
                        self.logger.warning(f"Действие '{action}' не найдено в сохраненных данных")

                self.logger.info(f"Настройки успешно загружены из {self.config_file}")

                return result_bindings

            except json.JSONDecodeError:
                self.logger.error(f"Ошибка чтения файла {self.config_file}.\nКлавиши установлены по умолчанию.")
                return self.default_key_bindings.copy()
            except Exception as e:
                self.logger.exception(f"Ошибка при загрузке настроек: {e}.\nКлавиши установлены по умолчанию.")
                return self.default_key_bindings.copy()
        else:
            self.logger.warning(f"Файл настроек не найден. Создаем новый...")

            # Создаем директорию если нужно
            directory = os.path.dirname(self.config_file)
            if directory:
                os.makedirs(directory, exist_ok=True)

            # Используем значения по умолчанию
            result_bindings = self.default_key_bindings.copy()

            # Сохраняем настройки по умолчанию
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(result_bindings, f, indent=4, ensure_ascii=False)
                self.logger.info(f"Создан новый файл настроек: {self.config_file}")
            except Exception as e:
                self.logger.error(f"Ошибка при создании файла настроек: {e}")

            return result_bindings

    def save_key_bindings(self):
        """
        Сохраняет текущие привязки клавиш в JSON файл.
        """
        try:
            # Создаем директорию если нужно
            directory = os.path.dirname(self.config_file)
            if directory:
                os.makedirs(directory, exist_ok=True)

            self.key_bindings = self._convert_codes_to_strings(self.key_codes)

            # Открываем файл для записи
            with open(self.config_file, 'w', encoding='utf-8') as f:
                # Сохраняем данные в JSON с красивым форматированием
                json.dump(self.key_bindings, f, indent=4, ensure_ascii=False)

            self.logger.info(f"Настройки сохранены в {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении настроек: {e}")
            return False

    def reset_to_defaults(self):
        """
        Сбрасывает все привязки к значениям по умолчанию.
        """
        self.key_bindings = self.default_key_bindings.copy()
        self.key_codes = self._convert_strings_to_codes(self.key_bindings)
        self._init_actions()
        self.save_key_bindings()
        self.logger.info("Настройки сброшены к значениям по умолчанию")

    def rebind_action(self, action_name, new_key):
        """Переназначает клавишу для указанного действия"""
        if action_name not in self.key_codes:
            self.logger.error(f"Действие '{action_name}' не найдено")
            return False

        new_key_string = self.code_to_string.get(new_key)
        if new_key_string is None:
            self.logger.error(f"Неизвестный код клавиши {new_key}")
            return False

        # Проверка конфликта
        for action, codes in self.key_codes.items():
            if new_key in codes and action != action_name:
                # Автоматически удалить конфликтующую привязку
                self.remove_key_binding(action, new_key)
                break

        # Добавляем новую клавишу
        if new_key_string not in self.key_bindings[action_name]:
            self.key_bindings[action_name].append(new_key_string)
            self.key_codes[action_name].append(new_key)

        return self.save_key_bindings()

    def remove_key_binding(self, action_name, key_to_remove):
        """
        Удаляет привязку клавиши для указанного действия.
        key_to_remove: может быть либо кодом клавиши (int), либо строкой (str)
        """
        if action_name not in self.key_bindings:
            self.logger.error(f"Действие '{action_name}' не найдено")
            return False

        # Определяем, что передано: код или строка
        if isinstance(key_to_remove, int):
            # Преобразуем код в строку
            key_string = self.code_to_string.get(key_to_remove)
            if key_string is None:
                self.logger.error(f"Неизвестный код клавиши {key_to_remove}")
                return False
        else:
            key_string = key_to_remove
            # Преобразуем строку в код для удаления из key_codes
            key_to_remove = self.string_to_code.get(key_string)

        # Удаляем из строковых привязок
        if key_string in self.key_bindings[action_name]:
            self.key_bindings[action_name].remove(key_string)

            # Удаляем из кодовых привязок
            if key_to_remove in self.key_codes[action_name]:
                self.key_codes[action_name].remove(key_to_remove)

            self.save_key_bindings()
            self.logger.info(f"Привязка '{key_string}' удалена для действия '{action_name}'")
            return True

        self.logger.warning(f"Клавиша '{key_string}' не найдена для действия '{action_name}'")
        return False

    def get_key_names(self, key_codes):
        """
        Преобразует коды клавиш в читаемые имена.

        Args:
            key_codes (list): Список кодов клавиш

        Returns:
            list: Список имен клавиш
        """
        names = []
        for key_code in key_codes:
            name = self.code_to_string.get(key_code)
            if name is not None:
                names.append(name)
            else:
                names.append(f"Key_{key_code}")
        return names

    def get_action_info(self):
        """
        Возвращает информацию о всех действиях и их привязках.
        Полезно для отображения в меню настроек.
        """
        info = {}
        for action, key_strings in self.key_bindings.items():
            # Получаем коды для этого действия
            codes = self.key_codes.get(action, [])
            info[action] = {
                'keys': codes,
                'key_names': key_strings  # Уже строки, готовы для отображения
            }
            self.logger.info(info)
        return info

    def on_key_release(self, key: int, modifiers: int) -> None:
        """Обработка отпускания клавиши"""
        # Удаляем клавишу из нажатых
        self.keys_pressed.discard(key)

        # Определяем, какое направление было отпущено
        released_direction = None
        if key in self.key_codes.get('up', []):
            released_direction = 'up'
        elif key in self.key_codes.get('down', []):
            released_direction = 'down'
        elif key in self.key_codes.get('left', []):
            released_direction = 'left'
        elif key in self.key_codes.get('right', []):
            released_direction = 'right'

        # Если отпущено активное направление
        if released_direction and self.actions.get(released_direction, False):
            # Сбрасываем это направление
            self.actions[released_direction] = False

            # Ищем другую нажатую клавишу направления
            new_direction = None
            for direction in ['up', 'down', 'left', 'right']:
                if direction != released_direction:
                    # Проверяем, нажата ли какая-то из клавиш этого направления
                    keys = self.key_codes.get(direction, [])
                    if any(k in self.keys_pressed for k in keys):
                        new_direction = direction
                        break

            # Если найдена другая нажатая клавиша направления, активируем её
            if new_direction:
                self.actions[new_direction] = True

        # Обновляем last_valid_direction
        self._update_last_direction()
        self.update_actions()

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Обработка нажатия клавиши (только одно направление за раз)"""
        self.keys_pressed.add(key)

        # Определяем, какая клавиша направления была нажата
        new_direction = None
        if key in self.key_codes.get('up', []):
            new_direction = 'up'
        elif key in self.key_codes.get('down', []):
            new_direction = 'down'
        elif key in self.key_codes.get('left', []):
            new_direction = 'left'
        elif key in self.key_codes.get('right', []):
            new_direction = 'right'

        # Если нажата клавиша направления
        if new_direction:
            # Отключаем ВСЕ направления
            for direction in ['up', 'down', 'left', 'right']:
                self.actions[direction] = False

            # Включаем только новое направление
            self.actions[new_direction] = True

        # Для остальных действий обновляем как обычно
        else:
            for action, codes in self.key_codes.items():
                if action not in ['up', 'down', 'left', 'right']:
                    self.actions[action] = any(key in codes for key in self.keys_pressed)

        # Обновляем last_valid_direction
        self._update_last_direction()
        self.update_actions()

    def _update_last_direction(self) -> None:
        """Обновляет last_valid_direction на основе активного направления"""
        self.last_valid_direction = None
        for direction in ['up', 'down', 'left', 'right']:
            if self.actions.get(direction, False):
                self.last_valid_direction = direction
                break

    def update_actions(self) -> None:
        """Обновление состояний не-направленных действий"""
        # Для направлений НЕ используем этот метод - они управляются вручную
        # Обновляем только остальные действия
        for action, codes in self.key_codes.items():
            if action not in ['up', 'down', 'left', 'right']:
                self.actions[action] = any(key in codes for key in self.keys_pressed)

    def reset_action(self, action_name):
        """Сбрасывает конкретное действие"""
        if action_name in self.actions:
            self.actions[action_name] = False
            # Также удаляем все клавиши этого действия из keys_pressed
            if action_name in self.key_codes:
                for key_code in self.key_codes[action_name]:
                    self.keys_pressed.discard(key_code)

    def get_action(self, action_name):
        """Проверяет, активно ли действие"""
        return self.actions.get(action_name, False)

    def get_key_string_for_code(self, key_code):
        """Возвращает строковое представление клавиши по коду"""
        return self.code_to_string.get(key_code, f"Key_{key_code}")

    def get_key_code_for_string(self, key_string):
        """Возвращает код клавиши по строковому представлению"""
        return self.string_to_code.get(key_string)

    def _init_actions(self):
        """Инициализирует состояния всех действий как False"""
        for action in self.key_bindings:
            self.actions[action] = False

    def _init_key_mapping(self):
        """Инициализирует словари для преобразования кодов клавиш"""
        # Словарь для преобразования строк в коды клавиш
        self.string_to_code = {
            # Буквы
            "A": arcade.key.A, "B": arcade.key.B, "C": arcade.key.C,
            "D": arcade.key.D, "E": arcade.key.E, "F": arcade.key.F,
            "G": arcade.key.G, "H": arcade.key.H, "I": arcade.key.I,
            "J": arcade.key.J, "K": arcade.key.K, "L": arcade.key.L,
            "M": arcade.key.M, "N": arcade.key.N, "O": arcade.key.O,
            "P": arcade.key.P, "Q": arcade.key.Q, "R": arcade.key.R,
            "S": arcade.key.S, "T": arcade.key.T, "U": arcade.key.U,
            "V": arcade.key.V, "W": arcade.key.W, "X": arcade.key.X,
            "Y": arcade.key.Y, "Z": arcade.key.Z,

            # Цифры
            "0": arcade.key.KEY_0, "1": arcade.key.KEY_1, "2": arcade.key.KEY_2,
            "3": arcade.key.KEY_3, "4": arcade.key.KEY_4, "5": arcade.key.KEY_5,
            "6": arcade.key.KEY_6, "7": arcade.key.KEY_7, "8": arcade.key.KEY_8,
            "9": arcade.key.KEY_9,

            "NUM_0": arcade.key.NUM_0, "NUM_1": arcade.key.NUM_1, "NUM_2": arcade.key.NUM_2,
            "NUM_3": arcade.key.NUM_3, "NUM_4": arcade.key.NUM_4, "NUM_5": arcade.key.NUM_5,
            "NUM_6": arcade.key.NUM_6, "NUM_7": arcade.key.NUM_7, "NUM_8": arcade.key.NUM_8,
            "NUM_9": arcade.key.NUM_9,

            # Функциональные клавиши
            "F1": arcade.key.F1, "F2": arcade.key.F2, "F3": arcade.key.F3,
            "F4": arcade.key.F4, "F5": arcade.key.F5, "F6": arcade.key.F6,
            "F7": arcade.key.F7, "F8": arcade.key.F8, "F9": arcade.key.F9,
            "F10": arcade.key.F10, "F11": arcade.key.F11, "F12": arcade.key.F12,

            # Специальные клавиши
            "SPACE": arcade.key.SPACE, "ENTER": arcade.key.ENTER,
            "ESCAPE": arcade.key.ESCAPE, "TAB": arcade.key.TAB,
            "BACKSPACE": arcade.key.BACKSPACE, "DELETE": arcade.key.DELETE,
            "INSERT": arcade.key.INSERT, "HOME": arcade.key.HOME,
            "END": arcade.key.END, "PAGEUP": arcade.key.PAGEUP,
            "PAGEDOWN": arcade.key.PAGEDOWN,

            # Стрелки
            "UP": arcade.key.UP, "DOWN": arcade.key.DOWN,
            "LEFT": arcade.key.LEFT, "RIGHT": arcade.key.RIGHT,

            # Модификаторы
            "LSHIFT": arcade.key.LSHIFT, "RSHIFT": arcade.key.RSHIFT,
            "LCTRL": arcade.key.LCTRL, "RCTRL": arcade.key.RCTRL,
            "LALT": arcade.key.LALT, "RALT": arcade.key.RALT,

            # Дополнительные
            "CAPSLOCK": arcade.key.CAPSLOCK, "NUMLOCK": arcade.key.NUMLOCK,
            "SCROLLLOCK": arcade.key.SCROLLLOCK,

            # Символьные клавиши
            "`": arcade.key.GRAVE, "-": arcade.key.MINUS, "=": arcade.key.EQUAL,
            "[": arcade.key.BRACKETLEFT, "]": arcade.key.BRACKETRIGHT,
            "\\": arcade.key.BACKSLASH, ";": arcade.key.SEMICOLON,
            "'": arcade.key.APOSTROPHE, ",": arcade.key.COMMA,
            ".": arcade.key.PERIOD, "/": arcade.key.SLASH,
        }

        # Обратный словарь (код -> строка)
        self.code_to_string = {v: k for k, v in self.string_to_code.items()}

    def _convert_strings_to_codes(self, string_bindings):
        """Конвертирует строковые привязки в коды клавиш"""
        code_bindings = {}
        for action, key_strings in string_bindings.items():
            codes = []
            for key_string in key_strings:
                code = self.string_to_code.get(key_string)
                if code is not None:
                    codes.append(code)
                else:
                    self.logger.warning(f"⚠ Внимание: неизвестная клавиша '{key_string}' для действия '{action}'")
            code_bindings[action] = codes
        return code_bindings

    def _convert_codes_to_strings(self, code_bindings):
        """Конвертирует коды клавиш в строковые привязки"""
        string_bindings = {}
        for action, key_codes in code_bindings.items():
            strings = []
            for key_code in key_codes:
                key_string = self.code_to_string.get(key_code)
                if key_string is not None:
                    strings.append(key_string)
                else:
                    self.logger.warning(f"Внимание: неизвестный код клавиши {key_code} для действия '{action}'")
            string_bindings[action] = strings
        return string_bindings

    def typing(self, key, first_part, second_part):
        key_value = self.get_key_string_for_code(key)
        if key_value.startswith("NUM_"):
            key_value = key_value[-1]


        # Обработка обычных букв
        if (key_value.isalpha() or key_value.isdigit()) and len(key_value) == 1:
            return f"{first_part}{key_value}|{second_part}"

        # Обработка специальных клавиш через словарь
        handlers = {
            "SPACE": lambda: f"{first_part}_|{second_part}",
            "BACKSPACE": lambda: f"{first_part[:-1]}|{second_part}" if first_part else f"|{second_part}",
            "DELETE": lambda: f"{first_part}|{second_part[1:]}" if second_part else f"{first_part}|{second_part}",
            "UP": lambda: f"|{first_part}{second_part}",
            "DOWN": lambda: f"{first_part}{second_part}|",
            "LEFT": lambda: f"{first_part[:-1]}|{first_part[-1:]}{second_part}" if first_part else f"|{second_part}",
            "RIGHT": lambda: f"{first_part}{second_part[:1]}|{second_part[1:]}" if second_part else f"{first_part}|"
        }

        if key_value in handlers:
            return handlers[key_value]()

        return f"{first_part}|{second_part}"

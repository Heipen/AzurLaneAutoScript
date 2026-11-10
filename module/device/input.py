from module.device.app_control import AppControl
from module.device.method.adb_input import AdbInput
from module.device.method.fastinput_ime import FastInputIME
from module.logger import logger


class Input(AdbInput, FastInputIME):
    @property
    def _use_fastinput(self):
        return self.config.Emulator_ControlMethod in AppControl._app_u2_family

    def input_text(self, text, button):
        method = self.input_text_fastinput_ime if self._use_fastinput else self.input_text_adb
        method(text, button)

    def current_ime(self):
        return self.current_ime_adb()

    def is_keyboard_shown(self):
        return self.current_ime()[1]

    def ensure_clipboard(self):
        method = self.ensure_clipboard_uiautomator2 if self._use_fastinput else self.ensure_clipboard_adb
        method()

    def get_clipboard(self):
        try:
            method = self.get_clipboard_uiautomator2 if self._use_fastinput else self.get_clipboard_adb
            return method()
        finally:
            self.stuck_record_clear()

    def ime_shown(self) -> bool:
        _, shown = self.u2_current_ime()
        return shown

    def text_input_and_confirm(self, text: str, clear: bool = False):
        for fail_count in range(3):
            try:
                self.u2_send_keys(text=text, clear=clear)
                self.u2_send_action(6)
                break
            except EnvironmentError as e:
                if fail_count >= 2:
                    raise
                logger.exception(str(e) + f'Retrying {fail_count + 1}/3')

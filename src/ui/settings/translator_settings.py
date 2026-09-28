"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.widgets.enum_radiobutton_widget import EnumRadiobuttonsWidget
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from core.config.translator_config import TranslatorConfig
from core.translator.apis import TranslatorApi
from core.translator.exceptions import LlmError
from core.translator.llm import LlmTranslator


class TranslatorSettings(SettingsPage[TranslatorConfig]):
    """Widget for translator API settings."""

    __flayout: QFormLayout
    __api_selector: EnumRadiobuttonsWidget[TranslatorApi]
    __api_key_label: QLabel
    __api_key_entry: KeyLineEdit
    __prompt_label: QLabel
    __prompt_entry: QPlainTextEdit
    __llm_url_label: QLabel
    __llm_url_entry: QLineEdit
    __llm_model_label: QLabel
    __llm_model_entry: QComboBox
    __llm_refresh_button: QPushButton
    __reasoning_effort_label: QLabel
    __reasoning_effort_entry: QComboBox
    __show_confirmations_box: QCheckBox

    @override
    def _init_ui(self) -> None:
        scroll_widget = QWidget()
        self.setWidget(scroll_widget)

        self.__flayout = QFormLayout()
        self.__flayout.setContentsMargins(4, 0, 4, 0)
        scroll_widget.setLayout(self.__flayout)
        self.__init_api_settings()
        self.__init_confirmation_box()

    def __init_api_settings(self) -> None:
        self.__api_selector = EnumRadiobuttonsWidget(
            TranslatorApi,
            self._initial_config.translator,
            orientation=Qt.Orientation.Horizontal,
        )
        self.__api_selector.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__flayout.addRow(self.tr("Translator API"), self.__api_selector)

        self.__api_key_label = QLabel(self.tr("Translator API key"))
        self.__api_key_entry = KeyLineEdit()
        if self._initial_config.api_key:
            self.__api_key_entry.setText(self._initial_config.api_key)
        self.__api_key_entry.textChanged.connect(lambda _: self.changed_signal.emit())
        self.__flayout.addRow(self.__api_key_label, self.__api_key_entry)

        self.__prompt_label = QLabel(self.tr("System prompt"))
        self.__prompt_entry = QPlainTextEdit(self._initial_config.prompt)
        self.__prompt_entry.setMinimumHeight(120)
        self.__prompt_entry.setToolTip(
            self.tr("The selected target language is appended automatically.")
        )
        self.__prompt_entry.textChanged.connect(lambda: self.changed_signal.emit())
        self.__flayout.addRow(self.__prompt_label, self.__prompt_entry)

        self.__init_llm_settings()
        self.__api_selector.currentValueChanged.connect(
            self.__set_translator_fields_enabled
        )
        self.__set_translator_fields_enabled(self._initial_config.translator)

    @staticmethod
    def __requires_key(translator_api: TranslatorApi) -> bool:
        return translator_api in (
            TranslatorApi.DeepL,
            TranslatorApi.LLM,
        )

    @staticmethod
    def __requires_prompt(translator_api: TranslatorApi) -> bool:
        return translator_api == TranslatorApi.LLM

    def __set_translator_fields_enabled(self, translator_api: TranslatorApi) -> None:
        """Updates API-specific settings when the selected translator changes."""

        api_key_required = self.__requires_key(translator_api)
        self.__api_key_label.setEnabled(api_key_required)
        self.__api_key_entry.setEnabled(api_key_required)
        prompt_required = self.__requires_prompt(translator_api)
        self.__prompt_label.setEnabled(prompt_required)
        self.__prompt_entry.setEnabled(prompt_required)

        llm_selected = translator_api == TranslatorApi.LLM
        self.__llm_url_label.setEnabled(llm_selected)
        self.__llm_url_entry.setEnabled(llm_selected)
        self.__llm_model_label.setEnabled(llm_selected)
        self.__llm_model_entry.setEnabled(llm_selected)
        self.__llm_refresh_button.setEnabled(llm_selected)
        self.__reasoning_effort_label.setEnabled(llm_selected)
        self.__reasoning_effort_entry.setEnabled(llm_selected)

    def __init_llm_settings(self) -> None:
        """Initializes settings for OpenAI-compatible LLM APIs."""

        self.__llm_url_label = QLabel(self.tr("LLM API URL"))
        self.__llm_url_entry = QLineEdit(self._initial_config.llm_base_url)
        self.__llm_url_entry.setPlaceholderText("http://127.0.0.1:8888/v1")
        self.__llm_url_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__flayout.addRow(self.__llm_url_label, self.__llm_url_entry)

        self.__llm_model_label = QLabel(self.tr("LLM model"))
        self.__llm_model_entry = QComboBox()
        self.__llm_model_entry.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        if self._initial_config.llm_model:
            self.__llm_model_entry.addItem(self._initial_config.llm_model)
        self.__llm_model_entry.currentTextChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__llm_refresh_button = QPushButton(self.tr("Refresh models"))
        self.__llm_refresh_button.clicked.connect(self.__refresh_llm_models)
        model_widget = QWidget()
        model_layout = QHBoxLayout(model_widget)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.addWidget(self.__llm_model_entry, 1)
        model_layout.addWidget(self.__llm_refresh_button)
        self.__flayout.addRow(self.__llm_model_label, model_widget)

        self.__reasoning_effort_label = QLabel(self.tr("Reasoning"))
        self.__reasoning_effort_entry = QComboBox()
        for label, value in (
            (self.tr("Off"), "none"),
            (self.tr("Auto"), None),
            (self.tr("Minimal"), "minimal"),
            (self.tr("Low"), "low"),
            (self.tr("Medium"), "medium"),
            (self.tr("High"), "high"),
        ):
            self.__reasoning_effort_entry.addItem(label, value)
        current_index = self.__reasoning_effort_entry.findData(
            self._initial_config.reasoning_effort
        )
        self.__reasoning_effort_entry.setCurrentIndex(max(current_index, 0))
        self.__reasoning_effort_entry.currentIndexChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__flayout.addRow(
            self.__reasoning_effort_label, self.__reasoning_effort_entry
        )

    def __refresh_llm_models(self) -> None:
        """Loads models currently available from the configured LLM API."""

        try:
            models = LlmTranslator.get_available_models(
                self.__llm_url_entry.text(), self.__api_key_entry.text()
            )
        except LlmError as ex:
            QMessageBox.warning(self, self.tr("LLM"), str(ex))
            return

        selected_model = self.__llm_model_entry.currentText()
        self.__llm_model_entry.clear()
        self.__llm_model_entry.addItems(models)
        if selected_model in models:
            self.__llm_model_entry.setCurrentText(selected_model)
        if not models:
            QMessageBox.information(
                self,
                self.tr("LLM"),
                self.tr("No models are currently available from the LLM API."),
            )

    def __init_confirmation_box(self) -> None:
        self.__show_confirmations_box = QCheckBox(
            self.tr("Ask for confirmation before starting a batch machine translation")
        )
        self.__show_confirmations_box.setChecked(
            self._initial_config.show_confirmation_dialogs
        )
        self.__show_confirmations_box.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__flayout.addRow(self.__show_confirmations_box)

    @override
    def validate(self) -> None:
        translator_api = self.__api_selector.getCurrentValue()
        api_key = self.__api_key_entry.text().strip()
        prompt = self.__prompt_entry.toPlainText().strip()
        if translator_api == TranslatorApi.DeepL and not api_key:
            raise ConfigValidationError(
                self.tr("An API key is required for DeepL translator!")
            )
        if translator_api == TranslatorApi.LLM:
            try:
                LlmTranslator.normalize_base_url(self.__llm_url_entry.text())
            except LlmError as ex:
                raise ConfigValidationError(str(ex)) from ex
            if not api_key:
                raise ConfigValidationError(
                    self.tr("An API key is required for LLM translator!")
                )
            if not self.__llm_model_entry.currentText().strip():
                raise ConfigValidationError(
                    self.tr("Select an LLM model!")
                )
            if not prompt:
                raise ConfigValidationError(
                    self.tr("A system prompt is required for LLM translator!")
                )

    @override
    def apply(self, config: TranslatorConfig) -> None:
        config.translator = self.__api_selector.getCurrentValue()
        config.api_key = self.__api_key_entry.text().strip() or None
        config.prompt = self.__prompt_entry.toPlainText().strip()
        config.llm_base_url = self.__llm_url_entry.text().strip()
        config.llm_model = self.__llm_model_entry.currentText().strip() or None
        config.reasoning_effort = self.__reasoning_effort_entry.currentData()
        config.show_confirmation_dialogs = self.__show_confirmations_box.isChecked()

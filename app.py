"""Gradio entry point — orchestrates conversion, transcription and reporting.

This file deliberately keeps no business logic: it wires the building blocks
defined in :mod:`src` and exposes a mobile-friendly UI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

import gradio as gr

from src.audio.audio_converter import AudioConversionError, convert_to_wav
from src.audio.audio_validator import AudioValidationError, AudioValidator
from src.reports.docx_exporter import DocxExporter
from src.reports.markdown_report_generator import MarkdownReportGenerator
from src.reports.pdf_exporter import PdfExporter
from src.reports.report_model import MeetingReport
from src.reports.text_exporter import MarkdownExporter, TextExporter
from src.reports.whatsapp_report_generator import WhatsAppReportGenerator
from src.shared.cleanup import cleanup_files
from src.shared.settings import Settings
from src.summary.heuristic_summary_provider import HeuristicSummaryProvider
from src.summary.summary_provider import SummaryError, SummaryProvider
from src.transcription.transcriber import Transcriber, TranscriptionError
from src.transcription.whisper_transcriber import WhisperTranscriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_LOGGER = logging.getLogger("meeting-report")

SUMMARY_MODE_AUTO = "Automatique"
SUMMARY_MODE_HEURISTIC = "Algorithmique"
SUMMARY_MODE_GROQ = "Groq (Llama 3.3 70B)"
SUMMARY_MODE_GEMINI = "Gemini"

CONSENT_WARNING = (
    "⚠️ **Avertissement** — Assurez-vous d'avoir obtenu le consentement explicite "
    "de tous les participants avant d'enregistrer ou de téléverser un audio de réunion."
)


@dataclass(frozen=True)
class _PipelineResult:
    transcription: str
    markdown: str
    whatsapp: str
    markdown_path: str | None
    text_path: str | None
    docx_path: str | None
    pdf_path: str | None


SummaryProviderFactory = Callable[[], Optional[SummaryProvider]]


class MeetingPipeline:
    """End-to-end run: validate → convert → transcribe → summarise → export.

    The pipeline depends only on the abstractions (``Transcriber``,
    ``SummaryProvider``) — never on concrete cloud or local implementations.
    """

    def __init__(
        self,
        settings: Settings,
        validator: AudioValidator,
        transcriber: Transcriber,
        local_transcriber: Transcriber,
        heuristic_provider: HeuristicSummaryProvider,
        gemini_provider_factory: SummaryProviderFactory | None,
        groq_provider_factory: SummaryProviderFactory | None,
        markdown_generator: MarkdownReportGenerator,
        whatsapp_generator: WhatsAppReportGenerator,
        text_exporter: TextExporter,
        markdown_exporter: MarkdownExporter,
        docx_exporter: DocxExporter,
        pdf_exporter: PdfExporter,
    ) -> None:
        self._settings = settings
        self._validator = validator
        self._transcriber = transcriber
        self._local_transcriber = local_transcriber
        self._heuristic = heuristic_provider
        self._gemini_factory = gemini_provider_factory
        self._groq_factory = groq_provider_factory
        self._markdown = markdown_generator
        self._whatsapp = whatsapp_generator
        self._text_exporter = text_exporter
        self._markdown_exporter = markdown_exporter
        self._docx_exporter = docx_exporter
        self._pdf_exporter = pdf_exporter

    def run(
        self,
        audio_path: str,
        language: str,
        whisper_model: str,
        summary_mode: str,
    ) -> _PipelineResult:
        temp_files: list[str] = []
        try:
            self._validator.validate(audio_path)
            wav_path = convert_to_wav(audio_path)
            temp_files.append(wav_path)

            transcription = self._transcribe_with_fallback(
                wav_path=wav_path,
                language=None if language == "auto" else language,
                model_size=whisper_model,
            )
            if not transcription:
                raise TranscriptionError("La transcription est vide.")

            report = self._summarise_with_fallback(transcription, summary_mode)

            markdown = self._markdown.generate(report)
            whatsapp = self._whatsapp.generate(report)
            return self._export_all(report, markdown, whatsapp, transcription)
        finally:
            cleanup_files(temp_files)

    def _transcribe_with_fallback(
        self, wav_path: str, language: str | None, model_size: str
    ) -> str:
        try:
            return self._transcriber.transcribe(
                audio_path=wav_path, language=language, model_size=model_size
            )
        except TranscriptionError as error:
            if self._transcriber is self._local_transcriber:
                raise
            _LOGGER.warning(
                "Transcription primaire échouée (%s) — repli sur Whisper local.", error
            )
            return self._local_transcriber.transcribe(
                audio_path=wav_path, language=language, model_size=model_size
            )

    def _summarise_with_fallback(
        self, transcription: str, summary_mode: str
    ) -> MeetingReport:
        provider = self._pick_summary_provider(summary_mode)
        try:
            return provider.generate_report(transcription)
        except SummaryError as error:
            _LOGGER.warning("Résumé IA indisponible (%s) — repli sur heuristique.", error)
            return self._heuristic.generate_report(transcription)

    def _pick_summary_provider(self, summary_mode: str) -> SummaryProvider:
        if summary_mode == SUMMARY_MODE_HEURISTIC:
            return self._heuristic

        if summary_mode == SUMMARY_MODE_GROQ:
            provider = self._try_build(self._groq_factory)
            if provider is not None:
                return provider

        if summary_mode == SUMMARY_MODE_GEMINI:
            provider = self._try_build(self._gemini_factory)
            if provider is not None:
                return provider

        if summary_mode == SUMMARY_MODE_AUTO:
            for factory in (self._groq_factory, self._gemini_factory):
                provider = self._try_build(factory)
                if provider is not None:
                    return provider

        return self._heuristic

    @staticmethod
    def _try_build(factory: SummaryProviderFactory | None) -> SummaryProvider | None:
        if factory is None:
            return None
        return factory()

    def _export_all(
        self,
        report: MeetingReport,
        markdown: str,
        whatsapp: str,
        transcription: str,
    ) -> _PipelineResult:
        text_content = f"{markdown}\n\n----- VERSION WHATSAPP -----\n\n{whatsapp}"
        return _PipelineResult(
            transcription=transcription,
            markdown=markdown,
            whatsapp=whatsapp,
            markdown_path=self._markdown_exporter.export(markdown),
            text_path=self._text_exporter.export(text_content),
            docx_path=self._docx_exporter.export(report),
            pdf_path=self._pdf_exporter.export(report),
        )


def _build_pipeline(settings: Settings) -> tuple[MeetingPipeline, str]:
    """Build the pipeline and return it alongside a description of the
    active transcription engine, used for UI hints."""
    validator = AudioValidator(
        supported_extensions=settings.supported_extensions,
        max_size_mb=settings.max_audio_size_mb,
    )
    local_transcriber = WhisperTranscriber(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )
    transcriber, engine_label = _pick_transcriber(settings, local_transcriber)

    return MeetingPipeline(
        settings=settings,
        validator=validator,
        transcriber=transcriber,
        local_transcriber=local_transcriber,
        heuristic_provider=HeuristicSummaryProvider(),
        gemini_provider_factory=_make_gemini_factory(settings),
        groq_provider_factory=_make_groq_summary_factory(settings),
        markdown_generator=MarkdownReportGenerator(),
        whatsapp_generator=WhatsAppReportGenerator(),
        text_exporter=TextExporter(),
        markdown_exporter=MarkdownExporter(),
        docx_exporter=DocxExporter(),
        pdf_exporter=PdfExporter(),
    ), engine_label


def _pick_transcriber(settings: Settings, local: Transcriber) -> tuple[Transcriber, str]:
    if settings.groq_enabled:
        try:
            from src.transcription.groq_transcriber import GroqTranscriber
            return (
                GroqTranscriber(settings.groq_api_key, settings.groq_whisper_model),
                f"☁️ Groq Whisper Large V3 (cloud, rapide)",
            )
        except TranscriptionError as error:
            _LOGGER.warning("Init Groq transcription impossible : %s — repli sur local.", error)
    return local, f"💻 faster-whisper {settings.whisper_model_size} (local, CPU)"


def _make_gemini_factory(settings: Settings) -> SummaryProviderFactory | None:
    if not settings.gemini_enabled:
        return None

    def factory() -> SummaryProvider | None:
        try:
            from src.summary.gemini_summary_provider import GeminiSummaryProvider
            return GeminiSummaryProvider(settings.gemini_api_key, settings.gemini_model)
        except SummaryError as error:
            _LOGGER.warning("Initialisation Gemini impossible : %s", error)
            return None

    return factory


def _make_groq_summary_factory(settings: Settings) -> SummaryProviderFactory | None:
    if not settings.groq_enabled:
        return None

    def factory() -> SummaryProvider | None:
        try:
            from src.summary.groq_summary_provider import GroqSummaryProvider
            return GroqSummaryProvider(settings.groq_api_key, settings.groq_chat_model)
        except SummaryError as error:
            _LOGGER.warning("Initialisation Groq résumé impossible : %s", error)
            return None

    return factory


def _build_interface(
    pipeline: MeetingPipeline, settings: Settings, transcription_engine_label: str
) -> gr.Blocks:
    summary_modes = [SUMMARY_MODE_AUTO, SUMMARY_MODE_HEURISTIC]
    if settings.groq_enabled:
        summary_modes.append(SUMMARY_MODE_GROQ)
    if settings.gemini_enabled:
        summary_modes.append(SUMMARY_MODE_GEMINI)

    with gr.Blocks(title="Assistant Compte Rendu Réunion") as demo:
        gr.Markdown("# 📝 Assistant Compte Rendu Réunion")
        gr.Markdown(
            "Téléversez un audio de réunion pour générer une transcription et un compte rendu structuré. "
            "Le compte rendu peut être téléchargé en PDF, Word, texte ou Markdown."
        )
        gr.Markdown(f"**Moteur de transcription :** {transcription_engine_label}")
        gr.Markdown(CONSENT_WARNING)

        with gr.Row():
            with gr.Column(scale=2):
                audio = gr.Audio(type="filepath", label="Fichier audio de la réunion", sources=["upload"])
            with gr.Column(scale=1):
                language = gr.Dropdown(
                    choices=["auto", "fr", "en"], value="auto", label="Langue"
                )
                whisper_model = gr.Dropdown(
                    choices=["tiny", "base", "small"],
                    value=settings.whisper_model_size if settings.whisper_model_size in {"tiny", "base", "small"} else "base",
                    label="Modèle Whisper (utilisé seulement en mode local)",
                )
                summary_mode = gr.Dropdown(
                    choices=summary_modes,
                    value=SUMMARY_MODE_AUTO,
                    label="Mode de résumé",
                )

        submit = gr.Button("🎙️ Transcrire et générer le compte rendu", variant="primary")
        status = gr.Markdown("", visible=False)

        with gr.Tab("📋 Compte rendu"):
            report_view = gr.Markdown(label="Compte rendu")
        with gr.Tab("💬 Version WhatsApp"):
            whatsapp_view = gr.Textbox(label="À copier/coller dans WhatsApp", lines=12)
        with gr.Tab("📝 Transcription"):
            transcription_view = gr.Textbox(label="Transcription complète", lines=16)

        gr.Markdown("### 📥 Téléchargements")
        with gr.Row():
            pdf_file = gr.File(label="PDF (recommandé)")
            docx_file = gr.File(label="Word (.docx)")
        with gr.Row():
            text_file = gr.File(label="Texte (.txt)")
            markdown_file = gr.File(label="Markdown (.md)")

        submit.click(
            fn=lambda *_: gr.update(value="⏳ Traitement en cours… cela peut prendre quelques minutes.", visible=True),
            inputs=[audio],
            outputs=[status],
            queue=False,
        ).then(
            fn=_make_handler(pipeline),
            inputs=[audio, language, whisper_model, summary_mode],
            outputs=[
                report_view,
                whatsapp_view,
                transcription_view,
                pdf_file,
                docx_file,
                text_file,
                markdown_file,
                status,
            ],
        )

    return demo


def _make_handler(pipeline: MeetingPipeline):
    def handle(audio_path, language, whisper_model, summary_mode):
        if not audio_path:
            return (
                "",
                "",
                "",
                None,
                None,
                None,
                None,
                gr.update(value="❌ Veuillez d'abord déposer un fichier audio.", visible=True),
            )
        try:
            result = pipeline.run(audio_path, language, whisper_model, summary_mode)
        except (AudioValidationError, AudioConversionError, TranscriptionError) as error:
            return (
                "",
                "",
                "",
                None,
                None,
                None,
                None,
                gr.update(value=f"❌ {error}", visible=True),
            )
        except Exception as error:  # noqa: BLE001 - last-resort guard for the UI
            _LOGGER.exception("Erreur inattendue durant le traitement")
            return (
                "",
                "",
                "",
                None,
                None,
                None,
                None,
                gr.update(value=f"❌ Erreur inattendue : {error}", visible=True),
            )

        return (
            result.markdown,
            result.whatsapp,
            result.transcription,
            result.pdf_path,
            result.docx_path,
            result.text_path,
            result.markdown_path,
            gr.update(value="✅ Compte rendu généré.", visible=True),
        )

    return handle


def main() -> None:
    settings = Settings.load()
    pipeline, engine_label = _build_pipeline(settings)
    demo = _build_interface(pipeline, settings, engine_label)
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()

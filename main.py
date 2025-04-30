# Program Zapisywacz Tekstu 2025 Paweł‑w (Python 3.13.x)
#
# Obsługiwane formaty: mp3, mp4, wav, m4a, flac, opus, aiff, mov, avi, mkv.
# Pliki są tymczasowo konwertowane do WAV: PCM 16-bit, mono, 16000 Hz.
#
# SRT – format napisów (np. używany w YouTube i filmach).
# CSV – format eksportu danych, przydatny np. do importu do arkuszy kalkulacyjnych.
#
# Dodatkowo, tworzony jest autorski format TXT (autorski_<nazwa_pliku>.txt) – 
# zawiera czysty tekst wypowiedzi (każda linijka kolejna wypowiedź) bez sygnatur czasowych i numerków.
#
# Ustawienia sprzętowe (wybór przetwarzania):
#   • "Korzystaj z GPU i CPU (Ctrl+Shift+Esc – monitoruj wydajność)" – domyślnie zaznaczony, gdy GPU jest dostępne.
#   • "Wykonaj działania tylko na CPU" – domyślnie zaznaczony, gdy GPU nie jest dostępne.
#   • "Korzystaj tylko z GPU – opcja eksperymentalna" – domyślnie odznaczona.
# Tylko jedna z tych opcji może być aktywna.
#
# Logi są zapisywane w folderze "logs" znajdującym się w katalogu źródłowym.
# Dla każdego pliku źródłowego tworzony jest folder "Tymczasowy_<nazwa_pliku>" w tym samym katalogu.
#
# Po zakończeniu transkrypcji odtwarzany jest domyślny dźwięk systemowy.
#
# Jeżeli GPU nie jest dostępne spełniające wymagania (NVIDIA GPU wspierająca CUDA 11.8 lub nowszą oraz min. 3GB VRAM), 
# program działa wolniej na CPU – komunikat zostanie zapisany w logu.

import os
import sys
import glob
import time
import json
import csv
import logging
import threading
import random
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import re
import winsound  # Do dźwięku powiadomienia

import torch
import whisper
import moviepy.editor as mp
from pydub import AudioSegment

# Importy dla diaryzacji
from resemblyzer import VoiceEncoder, preprocess_wav
from spectralcluster import SpectralClusterer
import numpy as np
import soundfile as sf
import librosa

# Funkcja zwracająca ścieżkę folderu logów – w katalogu źródłowym.
def get_log_dir(base_dir):
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

# Domyślny folder logów (tymczasowy, dopóki nie użytkownik wybierze plików)
DEFAULT_LOG_DIR = os.path.join(os.path.expanduser("~"), "Documents", "TranscriptionApp", "logs")
os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DEFAULT_LOG_DIR, f"transcription_log_{time.strftime('%Y%m%d_%H%M%S')}.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TranscriptionApp")

# Klasa ScrollableFrame – zawartość przewijalna (pionowo i poziomo)
class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg="green")
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

# Lista rozdzielczości do menu
RESOLUTIONS = [
    "800x600", "1024x768", "1152x864", "1280x720", "1280x800",
    "1280x1024", "1360x768", "1366x768", "1440x900", "1600x900",
    "1600x1200", "1680x1050", "1920x1080", "1920x1200", "2048x1152",
    "2560x1080", "2560x1440", "2560x1600", "3440x1440", "3840x2160"
]

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        # Pobierz rozdzielczość ekranu, wycentruj okno
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        win_width, win_height = 1680, 1050
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        self.root.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.root.title("Program Zapisywacz Tekstu 2025 Paweł‑w (Python 3.13.x)")
        self.root.configure(bg="green")
        self.create_menu()
        
        self.main_frame = ScrollableFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_variables()
        self.create_ui()
        self.start_time = None
        self.transcription_running = False

        # Ustawienie trybu sprzętowego:
        # Jeśli GPU jest dostępne, domyślnie wybieramy "gpu_cpu",
        # w przeciwnym razie "cpu". Dodatkowo logujemy informację o wymaganiach.
        if torch.cuda.is_available():
            try:
                self.gpu_name = torch.cuda.get_device_name(0)
            except Exception as e:
                self.gpu_name = "Błąd przy pobieraniu nazwy GPU"
            self.hardware_info_text.set(f"Wykryto GPU: {self.gpu_name} (CUDA {torch.version.cuda})")
            self.hardware_mode.set("gpu_cpu")
        else:
            self.hardware_info_text.set("ALERT: GPU nie wykryte lub nieobsługiwane przez CUDA!")
            self.hardware_mode.set("cpu")
            logger.info("Brak karty graficznej spełniającej wymagania. Wymagania: NVIDIA GPU wspierająca CUDA 11.8 lub nowszą oraz minimum 3GB VRAM. Program będzie działał wolniej na CPU.")
        
    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        view_menu = tk.Menu(menu_bar, tearoff=0)
        for res in RESOLUTIONS:
            view_menu.add_radiobutton(label=res, command=lambda r=res: self.change_resolution(r))
        menu_bar.add_cascade(label="Widok", menu=view_menu)
        self.root.config(menu=menu_bar)
        
    def change_resolution(self, res):
        self.root.geometry(res)
        logger.info(f"Zmieniono rozdzielczość na: {res}")
        
    def setup_variables(self):
        self.file_paths = []
        self.source_dir = ""
        self.file_path_var = tk.StringVar()
        self.output_dir = tk.StringVar()
        # Wybór modelu – radiobuttony
        self.model_choice = tk.StringVar(value="large")
        self.status_var = tk.StringVar(value="Gotowy")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.update_interval = tk.IntVar(value=4)
        
        self.force_polish = tk.BooleanVar(value=True)
        self.enable_speaker_diarization = tk.BooleanVar(value=True)
        self.diarization_method = tk.StringVar(value="advanced")
        self.enable_logging = tk.BooleanVar(value=True)
        self.remove_duplicates = False
        
        # Tryb przetwarzania – teraz jako radiobuttony; wartości: "cpu", "gpu_cpu", "gpu"
        self.hardware_mode = tk.StringVar()
        
        # Format eksportu – domyślnie wszystkie zaznaczone
        self.export_txt = tk.BooleanVar(value=True)
        self.export_srt = tk.BooleanVar(value=True)
        self.export_vtt = tk.BooleanVar(value=True)
        self.export_json = tk.BooleanVar(value=True)
        self.export_csv = tk.BooleanVar(value=True)
        
        self.hardware_info_text = tk.StringVar(value="Sprawdzam dostępność GPU...")
        
        # Zmienna opisu modelu – dynamiczna treść
        self.model_description = tk.StringVar(value="Large – najwolniejszy, ale zapewniający najwyższą dokładność transkrypcji.")
        
    def create_ui(self):
        # Panel z informacją o sprzęcie
        self.hardware_info_label = tk.Label(self.main_frame.scrollable_frame, textvariable=self.hardware_info_text,
                                            bg="green", fg="white", font=("Helvetica", 12, "bold"))
        self.hardware_info_label.pack(fill=tk.X, padx=10, pady=5)
        self.cpu_info_label = tk.Label(self.main_frame.scrollable_frame, text="",
                                       bg="green", fg="white", font=("Helvetica", 12, "bold"))
        self.cpu_info_label.pack(fill=tk.X, padx=10, pady=2)
        
        # Panel wyboru plików i opis
        files_info_frame = ttk.Frame(self.main_frame.scrollable_frame, padding="10")
        files_info_frame.pack(fill=tk.X, padx=10, pady=5)
        file_frame = ttk.LabelFrame(files_info_frame, text="Wybór plików źródłowych", padding="10")
        file_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        file_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Przeglądaj...", command=self.browse_files).grid(row=0, column=1, padx=5, pady=5)
        desc_text = (
            "Obsługiwane formaty: mp3, mp4, wav, m4a, flac, opus, aiff, mov, avi, mkv.\n"
            "Pliki są tymczasowo konwertowane do WAV (PCM 16-bit, mono, 16000 Hz).\n\n"
            "SRT – format napisów (np. używany w YouTube i filmach).\n"
            "CSV – format eksportu danych, przydatny np. do importu do arkuszy kalkulacyjnych.\n"
        )
        desc_label = tk.Label(files_info_frame, text=desc_text, bg="green", fg="white", justify=tk.LEFT)
        desc_label.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        files_info_frame.columnconfigure(0, weight=1)
        files_info_frame.columnconfigure(1, weight=1)
        
        # Katalog wyjściowy
        output_frame = ttk.LabelFrame(self.main_frame.scrollable_frame, text="Katalog wyjściowy", padding="10")
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir, width=80)
        output_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(output_frame, text="Przeglądaj...", command=self.browse_output_dir).grid(row=0, column=1, padx=5, pady=5)
        
        # Opcje transkrypcji – wybór modelu (radiobuttony) oraz opis modelu
        options_frame = ttk.LabelFrame(self.main_frame.scrollable_frame, text="Opcje transkrypcji", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(options_frame, text="Wybierz rozmiar modelu:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        models = ["tiny", "base", "small", "medium", "large"]
        for idx, model in enumerate(models):
            rb = ttk.Radiobutton(options_frame, text=model.capitalize(),
                                 variable=self.model_choice, value=model, command=self.update_model_info)
            rb.grid(row=1, column=idx, padx=5, pady=5)
        self.model_info_label = tk.Label(options_frame, textvariable=self.model_description,
                                         bg="white", justify=tk.LEFT)
        self.model_info_label.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=5)
        
        # Pozostałe opcje: język i rozpoznawanie mówców
        ttk.Checkbutton(options_frame, text="Wymuś język polski", variable=self.force_polish).grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(options_frame, text="Rozpoznawanie mówców", variable=self.enable_speaker_diarization).grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(options_frame, text="Podstawowy (resemblyzer + spectralcluster)", variable=self.diarization_method, value="basic").grid(row=5, column=0, sticky="w", padx=30, pady=2)
        ttk.Radiobutton(options_frame, text="Zaawansowany (dokładniejszy, wolniejszy)", variable=self.diarization_method, value="advanced").grid(row=6, column=0, sticky="w", padx=30, pady=2)
        
        # Tryb przetwarzania – radiobuttony (mutually exclusive)
        hardware_frame = ttk.LabelFrame(options_frame, text="Tryb przetwarzania", padding="10")
        hardware_frame.grid(row=7, column=0, columnspan=5, sticky="w", padx=5, pady=5)
        # Możliwe wartości: "cpu", "gpu_cpu", "gpu"
        rb_cpu = ttk.Radiobutton(hardware_frame, text="Wykonaj działania tylko na CPU", variable=self.hardware_mode, value="cpu")
        rb_gpu_cpu = ttk.Radiobutton(hardware_frame, text="Korzystaj z GPU i CPU (Ctrl+Shift+Esc – monitoruj wydajność)", variable=self.hardware_mode, value="gpu_cpu")
        rb_gpu = ttk.Radiobutton(hardware_frame, text="Korzystaj tylko z GPU – opcja eksperymentalna", variable=self.hardware_mode, value="gpu")
        rb_cpu.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        rb_gpu_cpu.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        rb_gpu.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        # Suwak częstotliwości aktualizacji
        scale_frame = ttk.Frame(options_frame)
        scale_frame.grid(row=8, column=0, columnspan=5, sticky="w", padx=5, pady=5)
        ttk.Label(scale_frame, text="Częstotliwość aktualizacji (0-120 sek, 0 = brak):").pack(side=tk.LEFT)
        self.update_scale = ttk.Scale(scale_frame, from_=0, to=120, orient=tk.HORIZONTAL, variable=self.update_interval, command=self.update_scale_label)
        self.update_scale.pack(side=tk.LEFT, padx=5)
        self.scale_value_label = ttk.Label(scale_frame, text=f"{self.update_interval.get()} sek")
        self.scale_value_label.pack(side=tk.LEFT, padx=5)
        
        # Panel wyboru formatów eksportu – checkboxy, domyślnie wszystkie zaznaczone
        export_frame = ttk.LabelFrame(self.main_frame.scrollable_frame, text="Format eksportu", padding="10")
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Checkbutton(export_frame, text="TXT", variable=self.export_txt).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(export_frame, text="SRT", variable=self.export_srt).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(export_frame, text="VTT", variable=self.export_vtt).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(export_frame, text="JSON", variable=self.export_json).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(export_frame, text="CSV", variable=self.export_csv).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # Pasek postępu i status
        progress_frame = ttk.Frame(self.main_frame.scrollable_frame, padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        status_frame = ttk.Frame(self.main_frame.scrollable_frame, padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor="w")
        
        # Panel logów – z pionowym i poziomym paskiem przewijania
        log_frame = ttk.LabelFrame(self.main_frame.scrollable_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text = tk.Text(log_frame, wrap=tk.NONE, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        log_v_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_v_scroll.pack(fill=tk.Y, side=tk.RIGHT)
        log_h_scroll = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log_text.xview)
        log_h_scroll.pack(fill=tk.X, side=tk.BOTTOM)
        self.log_text.config(yscrollcommand=log_v_scroll.set, xscrollcommand=log_h_scroll.set)
        self.log_handler = LogTextHandler(self.log_text)
        logger.addHandler(self.log_handler)
        
        # Panel przycisków akcji – na samym dole
        action_frame = ttk.Frame(self.main_frame.scrollable_frame, padding="10")
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(action_frame, text="Rozpocznij transkrypcję", command=self.start_transcription).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Anuluj", command=self.cancel_transcription).pack(side=tk.LEFT, padx=5)
        
    def update_model_info(self):
        choice = self.model_choice.get()
        descriptions = {
            "tiny": "Tiny – bardzo szybki, ale mniej dokładny model. Idealny, gdy kluczowa jest szybkość, kosztem precyzji.",
            "base": "Base – szybki model o umiarkowanej dokładności, dobry kompromis.",
            "small": "Small – zbalansowany wybór: umiarkowana prędkość i dokładność.",
            "medium": "Medium – wolniejszy od Small, ale oferuje wyższą jakość transkrypcji.",
            "large": "Large – najwolniejszy, ale zapewniający najwyższą dokładność transkrypcji."
        }
        self.model_description.set(descriptions.get(choice, ""))
    
    def update_scale_label(self, value):
        self.scale_value_label.config(text=f"{int(float(value))} sek")
        
    def browse_files(self):
        filetypes = (("Pliki audio/wideo", "*.mp3 *.mp4 *.wav *.m4a *.flac *.opus *.aiff *.mov *.avi *.mkv"), ("Wszystkie pliki", "*.*"))
        files = filedialog.askopenfilenames(title="Wybierz pliki do transkrypcji", filetypes=filetypes)
        if files:
            self.file_paths = list(files)
            self.file_path_var.set("; ".join(self.file_paths))
            self.source_dir = os.path.dirname(self.file_paths[0])
            self.output_dir.set(self.source_dir)
            global DEFAULT_LOG_DIR
            DEFAULT_LOG_DIR = get_log_dir(self.source_dir)
            logger.info(f"Wybrano pliki: {self.file_paths}")
        
    def browse_output_dir(self):
        dirpath = filedialog.askdirectory(title="Wybierz katalog wyjściowy")
        if dirpath:
            self.output_dir.set(dirpath)
            logger.info(f"Wybrano katalog wyjściowy: {dirpath}")
    
    def start_transcription(self):
        if not self.file_paths:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać pliki do transkrypcji.")
            return
        self.cancel_flag = False
        self.transcription_running = True
        self.start_time = time.time()
        self.status_var.set("Rozpoczynanie transkrypcji...")
        self.progress_var.set(0)
        self.transcription_thread = threading.Thread(target=self.transcribe_all_files)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
        if self.update_interval.get() > 0:
            self.root.after(self.update_interval.get() * 1000, self.update_progress)
    
    def update_progress(self):
        if self.transcription_running:
            elapsed = int(time.time() - self.start_time)
            self.status_var.set(f"Transkrypcja trwa już {elapsed} sekund...")
            if self.update_interval.get() > 0:
                self.root.after(self.update_interval.get() * 1000, self.update_progress)
    
    def transcribe_all_files(self):
        total = len(self.file_paths)
        for idx, file_path in enumerate(self.file_paths, start=1):
            try:
                self.status_var.set(f"Przetwarzanie pliku {idx} z {total}...")
                self.run_transcription(file_path)
                self.progress_var.set((idx / total) * 100)
            except Exception as e:
                logger.error(f"Błąd przy przetwarzaniu {file_path}: {str(e)}")
                messagebox.showerror("Błąd", f"Błąd przy przetwarzaniu {file_path}:\n{str(e)}")
        self.transcription_running = False
        self.status_var.set("Transkrypcja zakończona.")
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
    
    def run_transcription(self, file_path):
        model_size = self.model_choice.get()
        file_ext = os.path.splitext(file_path)[1].lower()
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        # Folder tymczasowy: "Tymczasowy_<nazwa_pliku>" w katalogu źródłowym
        temp_dir = os.path.join(os.path.dirname(file_path), f"Tymczasowy_{base_filename}")
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Pliki tymczasowe zapisane są w: {temp_dir}. Usuń je samodzielnie lub wykorzystaj do innych celów.")
        
        audio_path = file_path
        if file_ext == ".wav":
            try:
                with sf.SoundFile(file_path) as _:
                    pass
            except Exception as e:
                logger.warning(f"Plik audio może być uszkodzony: {str(e)}")
                audio_path = self.fix_audio_file(file_path, temp_dir)
        
        if file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
            self.status_var.set("Wyodrębnianie audio z wideo...")
            logger.info("Wyodrębnianie audio z wideo...")
            audio_path = os.path.join(temp_dir, os.path.basename(file_path).replace(file_ext, '.wav'))
            try:
                video = mp.VideoFileClip(file_path)
                video.audio.write_audiofile(audio_path, logger=None)
                logger.info(f"Audio zapisane do: {audio_path}")
            except Exception as e:
                logger.error(f"Błąd podczas wyodrębniania audio: {str(e)}")
                raise Exception(f"Nie można wyodrębnić audio: {str(e)}")
        elif file_ext not in ['.mp3', '.wav']:
            self.status_var.set("Konwertowanie pliku audio do WAV...")
            logger.info(f"Konwertowanie {file_ext} do WAV...")
            audio_path = os.path.join(temp_dir, os.path.basename(file_path).replace(file_ext, '.wav'))
            try:
                audio = AudioSegment.from_file(file_path)
                audio.export(audio_path, format="wav")
                logger.info(f"Audio skonwertowane do: {audio_path}")
            except Exception as e:
                logger.error(f"Błąd konwersji audio: {str(e)}")
                audio_path = self.fix_audio_file(file_path, temp_dir)
        
        try:
            y, sr = librosa.load(audio_path, sr=None, duration=5)
            if len(y)==0:
                raise Exception("Plik audio jest pusty.")
        except Exception as e:
            logger.error(f"Błąd weryfikacji audio: {str(e)}")
            raise Exception(f"Plik audio jest nieprawidłowy: {str(e)}")
        
        hw_mode = self.hardware_mode.get()
        if hw_mode == "cpu":
            device = "cpu"
            logger.info("Tryb sprzętowy: Tylko CPU.")
        elif hw_mode == "gpu":
            device = "cuda"
            logger.info("Tryb sprzętowy: Tylko GPU (eksperymentalny).")
        else:
            device = "cuda"
            logger.info("Tryb sprzętowy: GPU i CPU.")
        
        self.status_var.set(f"Ładowanie modelu Whisper ({model_size}) na {device}...")
        try:
            model = whisper.load_model(model_size, device=device)
        except Exception as e:
            logger.error(f"Błąd ładowania modelu: {str(e)}")
            raise Exception(f"Nie można załadować modelu Whisper: {str(e)}")
        
        self.status_var.set("Transkrypcja w toku...")
        transcribe_options = {}
        if self.force_polish.get():
            transcribe_options["language"] = "pl"
        try:
            result = model.transcribe(audio_path, **transcribe_options)
        except Exception as e:
            logger.error(f"Błąd transkrypcji: {str(e)}")
            raise Exception(f"Błąd transkrypcji: {str(e)}")
        
        segments = result.get("segments", [])
        diarization_label = ""
        if self.enable_speaker_diarization.get():
            self.status_var.set("Rozpoznawanie mówców...")
            logger.info("Rozpoczynanie diaryzacji...")
            try:
                y, sr = librosa.load(audio_path, sr=None)
                if sr != 16000:
                    y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                    sr = 16000
                temp_audio = os.path.join(temp_dir, "processed_audio.wav")
                sf.write(temp_audio, y, sr)
                wav = preprocess_wav(temp_audio)
                encoder = VoiceEncoder()
                max_duration = 60
                if wav.duration > max_duration:
                    all_emb = []
                    all_ts = []
                    for start in range(0, int(wav.duration), max_duration):
                        end = min(start + max_duration, wav.duration)
                        seg_samples = wav[int(start*sr):int(end*sr)]
                        if len(seg_samples) > sr:
                            seg_emb, seg_ts = encoder.embed_utterance(seg_samples, return_partials=True, rate=16)
                            seg_ts = [t+start for t in seg_ts]
                            all_emb.extend(seg_emb)
                            all_ts.extend(seg_ts)
                    embeddings = np.array(all_emb)
                    timestamps = np.array(all_ts)
                else:
                    embeddings, timestamps = encoder.embed_utterance(wav, return_partials=True, rate=16)
                if len(embeddings) > 1:
                    clusterer = SpectralClusterer(min_clusters=2, max_clusters=10)
                    labels = clusterer.predict(embeddings)
                    diarized_segments = []
                    for i, seg in enumerate(segments):
                        start = seg["start"]
                        end = seg["end"]
                        idx = int(np.argmin(np.abs(timestamps - start)))
                        speaker = f"Osoba{labels[idx]+1}" if idx < len(labels) else "NieznanyMówca"
                        diarized_segments.append({"start": start, "end": end, "text": f"{speaker}: {seg['text'].strip()}"})
                    segments = diarized_segments
                    diarization_label = f"({self.diarization_method.get().capitalize()})"
                else:
                    logger.warning("Za mało danych do diaryzacji, pomijam...")
            except Exception as e:
                logger.error(f"Błąd podczas diaryzacji: {str(e)}")
        
        # Folder wynikowy: "wyniki_<nazwa_pliku>" w katalogu źródłowym
        output_subdir = os.path.join(os.path.dirname(file_path), f"wyniki_{base_filename}")
        os.makedirs(output_subdir, exist_ok=True)
        output_base = os.path.join(output_subdir, base_filename)
        self.status_var.set("Zapisywanie wyników...")
        logger.info("Zapisywanie wyników...")
        try:
            if self.export_txt.get():
                with open(f"{output_base}.txt", 'w', encoding='utf-8') as f:
                    for s in segments:
                        f.write(f"{s['text']}\n")
                logger.info(f"TXT zapisany: {output_base}.txt")
            if self.export_srt.get():
                self._write_srt(segments, f"{output_base}.srt")
                logger.info(f"SRT zapisany: {output_base}.srt")
            if self.export_vtt.get():
                self._write_vtt(segments, f"{output_base}.vtt")
                logger.info(f"VTT zapisany: {output_base}.vtt")
            if self.export_json.get():
                with open(f"{output_base}.json", 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
                logger.info(f"JSON zapisany: {output_base}.json")
            if self.export_csv.get():
                self._write_csv(segments, f"{output_base}.csv")
                logger.info(f"CSV zapisany: {output_base}.csv")
            # Autorski format – tekst bez sygnatur czasowych i numerków
            with open(f"{output_base}_autorski.txt", 'w', encoding='utf-8') as f:
                for s in segments:
                    f.write(f"{s['text'].strip()}\n")
            logger.info(f"Autorski TXT zapisany: {output_base}_autorski.txt")
            # Zapis logów w folderze "logs" w katalogu źródłowym
            log_dir = get_log_dir(os.path.dirname(file_path))
            log_out = os.path.join(log_dir, f"{base_filename}.log")
            with open(log_out, 'w', encoding='utf-8') as f:
                f.write(f"LOGI dla: {file_path}\n")
                f.write(json.dumps({"segments": segments}, ensure_ascii=False, indent=2))
            logger.info(f"Log zapisany: {log_out}")
        except Exception as e:
            logger.error(f"Błąd zapisu wyników: {str(e)}")
            raise Exception(f"Błąd zapisu wyników: {str(e)}")
    
    def fix_audio_file(self, audio_path, temp_dir):
        try:
            logger.info(f"Próba naprawy pliku audio: {audio_path}")
            fixed_path = os.path.join(temp_dir, "fixed_" + os.path.basename(audio_path))
            y, sr = librosa.load(audio_path, sr=None)
            sf.write(fixed_path, y, sr)
            return fixed_path
        except Exception as e:
            logger.error(f"Błąd naprawy audio: {str(e)}")
            raise Exception(f"Błąd naprawy audio: {str(e)}")
    
    def _write_srt(self, segments, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments):
                start = self._format_srt_time(seg["start"])
                end = self._format_srt_time(seg["end"])
                f.write(f"{i+1}\n{start} --> {end}\n{seg['text'].strip()}\n\n")
    
    def _format_srt_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    def _write_vtt(self, segments, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for seg in segments:
                start = self._format_vtt_time(seg["start"])
                end = self._format_vtt_time(seg["end"])
                f.write(f"{start} --> {end}\n{seg['text'].strip()}\n\n")
    
    def _format_vtt_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    
    def _write_csv(self, segments, output_path):
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["start", "end", "text"])
            for seg in segments:
                writer.writerow([seg["start"], seg["end"], seg["text"].strip()])
    
    def start_blinking(self, widget, base_text, blink_type):
        colors = ["green", "red", "yellow", "orange", self.random_color()]
        def blink(idx=0):
            new_color = colors[idx % len(colors)]
            widget.config(fg=new_color, text=base_text)
            widget.after(500, lambda: blink(idx+1))
        blink()
    
    def random_color(self):
        return "#%06x" % random.randint(0, 0xFFFFFF)
    
    def cancel_transcription(self):
        if hasattr(self, 'transcription_thread') and self.transcription_thread.is_alive():
            logger.info("Anulowanie transkrypcji...")
            self.status_var.set("Anulowanie...")
            self.cancel_flag = True
        else:
            logger.info("Brak aktywnej transkrypcji do anulowania.")

class LogTextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg+"\n")
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        self.text_widget.after(0, append)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = TranscriptionApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Krytyczny błąd: {str(e)}")
        messagebox.showerror("Krytyczny błąd", f"Aplikacja napotkała błąd: {str(e)}")
        sys.exit(1)

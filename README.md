<<<<<<< HEAD
# TranskrypcjaTeksuZAudio
Zapisywacz Tekstu 2025 to aaplikacja do automatycznej transkrypcji plików audio i wideo, oparta na technologii sztucznej inteligencji. Program obsługuje szeroki zakres formatów multimedialnych i umożliwia zapis wyników transkrypcji w różnych formatach: TXT, SRT, VTT, JSON, CSV. 
=======
# Program Zapisywacz Tekstu 2025

> **Uwaga:** Program został stworzony z pomocą Chata AI Capilot oraz Claude.

## Opis
**Program Zapisywacz Tekstu 2025** to aplikacja stworzona w języku Python, służąca do automatycznej transkrypcji plików audio i wideo na tekst. Program wykorzystuje model Whisper do rozpoznawania mowy oraz zawiera funkcję rozpoznawania mówców (diaryzacji). Aplikacja jest dostępna wyłącznie w języku polskim.

![Interfejs programu](images/interfejs1.png)

### Główne funkcje:
- Transkrypcja plików audio i wideo na tekst
- Obsługa wielu formatów plików: mp3, mp4, wav, m4a, flac, opus, aiff, mov, avi, mkv
- Rozpoznawanie mówców (diaryzacja)
- Eksport wyników w różnych formatach: TXT, SRT, VTT, JSON, CSV
- Możliwość wyboru rozmiaru modelu Whisper (tiny, base, small, medium, large)
- Wsparcie dla przetwarzania na CPU lub GPU (NVIDIA z CUDA)

## Wymagania systemowe
- Python 3.13.x (program działa TYLKO z tą wersją Pythona)
- CUDA 11.8 (program działa TYLKO z tą wersją CUDA)
- Biblioteki: torch, whisper, moviepy, pydub, resemblyzer, spectralcluster, numpy, soundfile, librosa
- Dla pełnej wydajności: karta graficzna NVIDIA wspierająca CUDA 11.8 oraz min. 3GB VRAM

> **WAŻNE:** Program został przetestowany na karcie graficznej NVIDIA GeForce GTX 1060 3GB z obsługą CUDA.

### Zmienne środowiskowe CUDA
Upewnij się, że zmienne środowiskowe CUDA są prawidłowo skonfigurowane w systemie:

```
CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8
PATH=%PATH%;%CUDA_HOME%\bin
```

![Zmienne środowiskowe](images/srodowisko.png)

## Instalacja

### 1. Pobierz i zainstaluj CUDA 11.8
Pobierz CUDA 11.8 ze strony NVIDIA: [https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local](https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local)

### 2. Sklonuj repozytorium:
```
git clone https://github.com/twój-użytkownik/zapisywacz-tekstu-2025.git
```

### 3. Zainstaluj wymagane biblioteki:
```
pip install -r requirements.txt
```

Lub zainstaluj je ręcznie:
```
pip install torch torchvision torchaudio
pip install openai-whisper moviepy pydub resemblyzer spectralcluster numpy soundfile librosa
```

## Wydajność programu

Program został przetestowany na następującej konfiguracji:
- Procesor: Intel i7
- RAM: 32GB
- Karta graficzna: NVIDIA GeForce GTX 1060 3GB
- Ustawienia: model 'large', tryb 'cpu+gpu'

Wyniki testu:
- Czas trwania nagrania testowego: 1 minuta 3 sekundy
- Czas przetwarzania: 4 minuty 40 sekund

![Wyniki testu](images/cpugpu.png)

Na podstawie tych wyników, wydajność programu wynosi około 12.9 minut przetworzonego materiału na godzinę pracy komputera. Oznacza to, że przetworzenie 1 godziny nagrania zajmie około 4 godzin 39 minut.

> **Ostrzeżenie:** W przypadku starszych komputerów zaleca się włączenie wentylatorów CPU na maksymalną prędkość (np. poprzez Smart Fan 5) w celu uniknięcia przegrzania.

## Instrukcja użytkowania

### Uruchomienie programu
```
python main.py
```

### Krok po kroku:
1. **Wybór plików**:
   - Kliknij przycisk "Przeglądaj..." w sekcji "Wybór plików źródłowych"
   - Wybierz jeden lub więcej plików audio/wideo do transkrypcji

2. **Katalog wyjściowy**:
   - Domyślnie jest to katalog, z którego wybrano pliki
   - Możesz zmienić katalog wyjściowy klikając "Przeglądaj..." w sekcji "Katalog wyjściowy"

3. **Opcje transkrypcji**:
   - Wybierz rozmiar modelu (tiny, base, small, medium, large)
   - Zdecyduj czy wymusić język polski
   - Włącz lub wyłącz rozpoznawanie mówców
   - Wybierz metodę diaryzacji (podstawowa lub zaawansowana)
   - Wybierz tryb przetwarzania (CPU, GPU+CPU, tylko GPU)
   - Ustaw częstotliwość aktualizacji informacji o postępie

4. **Format eksportu**:
   - Zaznacz formaty, w których chcesz otrzymać wyniki (TXT, SRT, VTT, JSON, CSV)

5. **Rozpocznij transkrypcję**:
   - Kliknij przycisk "Rozpocznij transkrypcję"
   - Postęp będzie widoczny na pasku postępu oraz w polu logów
   - Po zakończeniu usłyszysz sygnał dźwiękowy

![Interfejs programu](images/interfejs2.png)

### Wyniki
Wyniki transkrypcji są zapisywane w katalogu `wyniki_<nazwa_pliku>` w miejscu wskazanym jako katalog wyjściowy. Pliki tymczasowe są przechowywane w katalogu `Tymczasowy_<nazwa_pliku>`. Logi są zapisywane w folderze `logs`.

## Rozwiązywanie problemów

### Problemy z wyświetlaniem
W przypadku problemów z wyświetlaniem interfejsu:
1. Naciśnij "Widok" w górnym menu
2. Wybierz rozdzielczość 800x600
3. Używaj paska przewijania po prawej stronie do nawigacji (przewijanie myszką może nie działać)

## Pliki testowe

W katalogu `test` znajduje się przykładowy plik `Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.mp3`, który został przetworzony przez program. Katalog zawiera również wyniki transkrypcji w różnych formatach oraz pliki tymczasowe i logi.

Struktura katalogu testowego:
```
test/
├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.mp3
├── logs/
│   └── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.log
├── Tymczasowy_Pierwsze_slowa_Jana_Pawla_II_do_Rodakow/
│   └── processed_audio.wav
└── wyniki_Pierwsze_slowa_Jana_Pawla_II_do_Rodakow/
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.csv
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.json
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.srt
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.txt
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.vtt
    └── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow_autorski.txt
```

---

# Text Recorder Program 2025

> **Note:** This program was created with the help of Chat AI Capilot and Claude.

## Description
**Text Recorder Program 2025** is a Python application designed for automatic transcription of audio and video files to text. The program uses the Whisper model for speech recognition and includes speaker recognition (diarization) functionality. The application is available only in Polish language.

![Program Interface](images/interfejs1.png)

### Main features:
- Transcription of audio and video files to text
- Support for multiple file formats: mp3, mp4, wav, m4a, flac, opus, aiff, mov, avi, mkv
- Speaker recognition (diarization)
- Export results in various formats: TXT, SRT, VTT, JSON, CSV
- Ability to choose Whisper model size (tiny, base, small, medium, large)
- Support for processing on CPU or GPU (NVIDIA with CUDA)

## System Requirements
- Python 3.13.x (program works ONLY with this Python version)
- CUDA 11.8 (program works ONLY with this CUDA version)
- Libraries: torch, whisper, moviepy, pydub, resemblyzer, spectralcluster, numpy, soundfile, librosa
- For full performance: NVIDIA graphics card supporting CUDA 11.8 and min. 3GB VRAM

> **IMPORTANT:** The program was tested on an NVIDIA GeForce GTX 1060 3GB graphics card with CUDA support.

### CUDA Environment Variables
Make sure CUDA environment variables are properly configured in your system:

```
CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8
PATH=%PATH%;%CUDA_HOME%\bin
```

![Environment Variables](images/srodowisko.png)

## Installation

### 1. Download and install CUDA 11.8
Download CUDA 11.8 from NVIDIA website: [https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local](https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local)

### 2. Clone the repository:
```
git clone https://github.com/your-username/zapisywacz-tekstu-2025.git
```

### 3. Install required libraries:
```
pip install -r requirements.txt
```

Or install them manually:
```
pip install torch torchvision torchaudio
pip install openai-whisper moviepy pydub resemblyzer spectralcluster numpy soundfile librosa
```

## Program Performance

The program was tested with the following configuration:
- Processor: Intel i7
- RAM: 32GB
- Graphics card: NVIDIA GeForce GTX 1060 3GB
- Settings: 'large' model, 'cpu+gpu' mode

Test results:
- Test recording duration: 1 minute 3 seconds
- Processing time: 4 minutes 40 seconds

![Test Results](images/cpugpu.png)

Based on these results, the program performance is approximately 12.9 minutes of processed material per hour of computer work. This means processing 1 hour of recording will take approximately 4 hours 39 minutes.

> **Warning:** For older computers, it is recommended to set CPU fans to maximum speed (e.g., via Smart Fan 5) to prevent overheating.

## Usage Instructions

### Running the program
```
python main.py
```

### Step by step:
1. **File selection**:
   - Click the "Przeglądaj..." button in the "Wybór plików źródłowych" section
   - Select one or more audio/video files for transcription

2. **Output directory**:
   - By default, this is the directory from which the files were selected
   - You can change the output directory by clicking "Przeglądaj..." in the "Katalog wyjściowy" section

3. **Transcription options**:
   - Choose the model size (tiny, base, small, medium, large)
   - Decide whether to force Polish language
   - Enable or disable speaker recognition
   - Choose diarization method (basic or advanced)
   - Select processing mode (CPU, GPU+CPU, GPU only)
   - Set the frequency of progress updates

4. **Export format**:
   - Select the formats in which you want to receive results (TXT, SRT, VTT, JSON, CSV)

5. **Start transcription**:
   - Click the "Rozpocznij transkrypcję" button
   - Progress will be visible on the progress bar and in the log field
   - You will hear a sound signal upon completion

![Program Interface](images/interfejs2.png)

### Results
Transcription results are saved in the `wyniki_<filename>` directory in the location specified as the output directory. Temporary files are stored in the `Tymczasowy_<filename>` directory. Logs are saved in the `logs` folder.

## Troubleshooting

### Display Problems
If you experience interface display problems:
1. Click "Widok" in the top menu
2. Select 800x600 resolution
3. Use the scroll bar on the right side for navigation (mouse scrolling may not work)

## Test Files

The `test` directory contains a sample file `Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.mp3` that has been processed by the program. The directory also includes transcription results in various formats, temporary files, and logs.

Test directory structure:
```
test/
├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.mp3
├── logs/
│   └── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.log
├── Tymczasowy_Pierwsze_slowa_Jana_Pawla_II_do_Rodakow/
│   └── processed_audio.wav
└── wyniki_Pierwsze_slowa_Jana_Pawla_II_do_Rodakow/
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.csv
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.json
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.srt
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.txt
    ├── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow.vtt
    └── Pierwsze_slowa_Jana_Pawla_II_do_Rodakow_autorski.txt
```
>>>>>>> 2e73ef8 (Pierwsza wersja projektu)

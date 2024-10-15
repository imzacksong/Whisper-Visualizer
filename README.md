## Features

- **Audio Upload:** Easily select and upload various audio formats (e.g., WAV, MP3, M4A, FLAC, OGG, AAC).
- **Real-Time Waveform Visualization:** View dynamic and customizable waveforms with different styles (Line, Bar, Filled) and color options.
- **Synchronized Subtitles:** Automatic transcription of audio with accurate timing, displaying subtitles in real-time.
- **Customization Options:** 
  - Choose waveform colors or enable a rainbow effect.
  - Select subtitle font and color.
  - Adjust amplitude scaling for waveform clarity.
  - Set the maximum number of words per subtitle chunk.
- **Video Export:** Export your visualization with subtitles as high-quality videos in formats like MP4, AVI, or MKV without needing to install FFmpeg separately.
- **Progress Indicators:** Monitor transcription and export processes with integrated progress bars.

## Usage

    Launch the Application:

    Run the Python script:

    python textwaveform.py

    Upload Audio:
        Click on the "Select Audio" button to upload your audio file.
        Supported formats include WAV, MP3, M4A, FLAC, OGG, and AAC.

    Customize Settings:

        Waveform Settings:
            Select Waveform Color: Choose your preferred color or enable the rainbow effect.
            Waveform Style: Select between Line, Bar, or Filled styles.
            Amplitude Scaling: Adjust the waveform's amplitude for better visibility.

        Subtitle Settings:
            Select Subtitle Color: Choose the color of the subtitles.
            Select Subtitle Font: Pick a font that suits your preference.
            Max Words per Subtitle: Define the maximum number of words per subtitle chunk for readability.

        Export Settings:
            Export Format: Choose your desired video format (MP4, AVI, MKV).
            Export Quality: Select the quality level (Low, Medium, High).

    Preview:
        Click on "Start Preview" to see the waveform and subtitles in action.
        Use the Pause, Resume, and Stop buttons to control playback.
        Adjust the playback slider to seek through the audio.

    Export Video:
        Once satisfied with the preview, click on "Select Output Location & Export".
        Choose the destination and filename for your video.
        The application will render and save the video with the waveform and subtitles.


**Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.**

This project is licensed under the **MIT License**.

import os
import pygame
from paths import resource_path

AUDIO_DIR = 'assets/audio'


class SoundManager:
    def __init__(self):
        self.start_sound = self._load_sound('start.wav', volume=0.4)
        self.waka_sound = self._load_sound('wakawaka.wav', volume=0.5)
        self.powerup_sound = self._load_sound('powerup.wav', volume=0.4)
        self.death_sound = self._load_sound('death.wav', volume=0.5)

        # Dedicated channels for sounds that need control
        self._waka_channel = pygame.mixer.Channel(0)
        self._powerup_channel = pygame.mixer.Channel(1)

    def _load_sound(self, filename, volume=0.5):
        path = resource_path(os.path.join(AUDIO_DIR, filename))
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            sound.set_volume(volume)
            return sound
        return None

    def play_start(self):
        if self.start_sound:
            self.start_sound.play()

    def is_start_playing(self):
        if self.start_sound:
            return self.start_sound.get_num_channels() > 0
        return False

    def play_waka(self):
        if self.waka_sound and not self._waka_channel.get_busy():
            self._waka_channel.play(self.waka_sound, loops=-1)

    def stop_waka(self):
        self._waka_channel.stop()

    def play_powerup(self):
        if self.powerup_sound:
            self._powerup_channel.play(self.powerup_sound, loops=-1)

    def stop_powerup(self):
        if self._powerup_channel:
            self._powerup_channel.stop()

    def pause_powerup(self):
        if self._powerup_channel:
            self._powerup_channel.pause()

    def unpause_powerup(self):
        if self._powerup_channel:
            self._powerup_channel.unpause()

    def play_death(self):
        if self.death_sound:
            self.death_sound.play()

    def is_death_playing(self):
        if self.death_sound:
            return self.death_sound.get_num_channels() > 0
        return False

    def stop_all(self):
        pygame.mixer.stop()

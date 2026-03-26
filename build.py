import PyInstaller.__main__

PyInstaller.__main__.run([
    "main.py",
    "--name=pacman",
    "--onedir",
    "--windowed",
    "--add-data=assets;assets",
    "--add-data=freesansbold.ttf;.",
])

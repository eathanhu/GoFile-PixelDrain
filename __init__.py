# bot/__init__.py
"""
bot package initializer.

This package contains:
 - config.py          (environment & token loading)
 - db.py              (MongoDB utilities)
 - gofile.py          (GoFile API logic)
 - pixeldrain.py      (Pixeldrain API logic)
 - handlers.py        (Telegram commands & callbacks)
 - utils.py           (helpers like progress bars)

Usage example:
    from bot import config, db, handlers

This file marks the directory as a Python package but does not auto-import handlers,
allowing explicit control in main.py.
"""

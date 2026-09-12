# Working in runviewer

## Tests must not invoke the application

`runviewer/__main__.py` builds a `Splash` and calls `.show()` at module scope,
and `Splash.__init__` creates the `QApplication`. `splash.hide()` runs only
inside `if __name__ == '__main__'`. So **importing `runviewer.__main__` puts a
banner on the user's screen and leaves it there** — during a test run, during a
REPL session, during anything.

This repository has no `tests/` directory yet. When one is added, the rule, in
order of preference:

1. **Import the leaf module, not `__main__`.** Most of what is worth testing can
   be reached without the application. Sibling repositories do this: lyse's
   tests import `lyse.widgets`, and blacs's import `blacs.front_panel_settings`.
2. **If that is not possible**, load the module by path and stub its
   dependencies in `sys.modules`, restoring them in a `finally`. The worked
   example is `blacs/tests/test_plugins_compat.py`, which exercises the real
   `blacs/plugins/__init__.py` without importing the `blacs` package at all.
3. **If a test must borrow from `__main__`** — to exercise a real method rather
   than a description of it — stub `labscript_utils.splash` in `sys.modules`
   *before* the import. A fake `Splash` whose `__init__`, `show`, `hide` and
   `update_text` do nothing, and a `get_qapplication` returning `None`, is
   enough: no `QApplication` is created and the real methods are still borrowed.

A test that genuinely renders — geometry or pixel assertions — must still call
`.show()`, because Qt does not lay out or paint an unshown widget. Do not
"fix" such a test by removing the `show()`; its assertions would then read
nothing and pass vacuously.

Add a `tests/conftest.py` alongside the first test, so that nobody has to
remember a command-line setting:

    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

It must be a conftest rather than a fixture, because it has to take effect
before qtutils imports Qt, and pytest imports conftest first. `setdefault`
leaves an explicit setting alone, so anyone who wants to watch a test drive the
window can export it. `blacs/tests/conftest.py` is the model.

## Running tests, once there are any

From inside this repository, never from the workspace root — a workspace-root
cwd shadows the installed packages:

    LABSCRIPT_NO_ERROR_DIALOG=1 python -m pytest tests -q

`LABSCRIPT_NO_ERROR_DIALOG=1` stops `labscript_utils.excepthook` spawning a
tkinter window per unhandled exception. Exceptions are still logged and still
reach stderr.

## More

The workspace `AGENTS.md`, one directory up, carries the longer reasoning and
the conventions shared across the suite. This file exists because work often
happens inside one repository with no view of that one.

# Working in runviewer

## Tests must not invoke the application

`runviewer/__main__.py` builds a `Splash` and calls `.show()` at module scope,
and `Splash.__init__` creates the `QApplication`. `splash.hide()` runs only
inside `if __name__ == '__main__'`. So **importing `runviewer.__main__` puts a
banner on the user's screen and leaves it there** — during a test run, during a
REPL session, during anything.

The rule, in order of preference:

1. **Import the leaf module, not `__main__`.** Most of what is worth testing can
   be reached without the application. Sibling repositories do this: lyse's
   tests import `lyse.widgets`, and blacs's import `blacs.front_panel_settings`.
2. **If that is not possible**, load the module by path and stub its
   dependencies in `sys.modules`, restoring them in a `finally`. The worked
   example is `blacs/tests/test_plugins_compat.py`, which exercises the real
   `blacs/plugins/__init__.py` without importing the `blacs` package at all.
3. **If a test must borrow from `__main__`** — to exercise a real method rather
   than a description of it — stub `labscript_utils.splash` in `sys.modules`
   *before* the import.

`tests/fixtures.py` is where the third of those is done, because a method of
`RunViewer` leaves no other way in: there is no leaf module holding it, and
loading `__main__` by path would mean stubbing every one of its imports to reach
a single handler. It owns both the stub and the import and re-exports what the
tests borrow, so that **no test file imports `runviewer.__main__` itself** — a
reordered import block in a test would otherwise bring the banner back. Add to
its `__all__` rather than importing from the application directly. runmanager
and blacs keep a `fixtures.py` for the same reason.

A test that genuinely renders — geometry or pixel assertions — must still call
`.show()`, because Qt does not lay out or paint an unshown widget. Do not
"fix" such a test by removing the `show()`; its assertions would then read
nothing and pass vacuously.

`tests/conftest.py` sets `QT_QPA_PLATFORM=offscreen` and
`LABSCRIPT_NO_ERROR_DIALOG=1` with `os.environ.setdefault`, so that running the
tests depends on nobody remembering them. Both have to be set before the module
that reads them is imported — `QT_QPA_PLATFORM` before qtutils imports Qt,
`LABSCRIPT_NO_ERROR_DIALOG` before `labscript_utils.excepthook` — and pytest
imports conftest before the test modules that pull either in, which is why it is
a conftest and not a fixture. `setdefault` means an exported value still wins.
`blacs/tests/conftest.py` is the model.

## Running tests

From inside this repository, never from the workspace root — a workspace-root
cwd shadows the installed packages:

    python -m pytest tests -q

Use the interpreter the suite is installed into,
`~/miniforge3/envs/labscript/bin/python`; the default `python` on PATH has
neither pytest nor the suite.

## More

The workspace `AGENTS.md`, one directory up, carries the longer reasoning and
the conventions shared across the suite. This file exists because work often
happens inside one repository with no view of that one.

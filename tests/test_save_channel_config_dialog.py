"""The save panel behind *Save channel config*.

A save panel decides the extension of the file it returns. Given a name that
already has one it keeps that one, and typing replaces only the stem. Given a
bare folder it has no extension to preserve and supplies one of its own, taken
from the host's type database rather than from the name filter the dialog asked
for -- so the file that comes back need not be a ``.toml`` file at all, and
nothing between the panel and ``save_appconfig`` would notice.

What is pinned here is that the handler hands the panel a filename carrying the
extension a channel configuration is meant to have, in the folder those
configurations live in, and that the name offered is not the runviewer state
file -- which sits in that same folder, holds something else entirely, and is
the one file an operator must not be invited to overwrite from this dialog.

The panel belongs to the operating system and cannot be driven from a test, so
the seam under test is the call into it: ``QFileDialog`` is replaced in the
application's namespace and the arguments it was given are read back.
"""
import os
import shutil
import tempfile
import unittest

# fixtures stubs the splash and does the guarded import of the application,
# once, for every test module. Importing runviewer.__main__ here instead would
# show the startup banner.
from fixtures import RunViewer, main_module


class FakeRunViewer(object):
    """Enough of a RunViewer for ``on_save_channel_config`` to run.

    ``RunViewer.__init__`` builds the whole application, which this one handler
    has no use for.
    """

    on_save_channel_config = RunViewer.on_save_channel_config

    def __init__(self, folder):
        # The dialog's parent widget. Never reached, because the call into the
        # panel is intercepted.
        self.ui = None
        self.default_config_path = folder
        # Read only when the panel returns a name, which the offered-name tests
        # do not do.
        self.channel_model = None

    def get_default_config_file(self, ensure_directory=False):
        """The runviewer state file, as ``LabscriptApplication`` returns it.

        The handler does not call this. It is here so that the test which says
        the offered name is not this file can fail when it is: a stand-in
        without the method would raise instead, and an error raised reaching
        the assertion is not the assertion doing its work.
        """
        return os.path.join(self.default_config_path, RunViewer.default_config_filename)


class FakeFileDialog(object):
    """Stands in for ``QFileDialog`` in the application's namespace.

    ``runviewer.__main__`` takes ``QFileDialog`` from a star import, so it is a
    name in that module rather than an attribute of a package, and rebinding
    the name is enough to intercept the call. Doing it this way leaves the real
    Qt class untouched for everything else in the process.
    """

    def __init__(self):
        # Directories the panel was opened at, one per call, and the name it is
        # to hand back. A falsy name is a cancelled dialog.
        self.calls = []
        self.answer = ''

    def getSaveFileName(self, parent, caption, directory, filter=None):
        self.calls.append(directory)
        return (self.answer, filter)


class SaveChannelConfigDialogTests(unittest.TestCase):
    """What the handler asks the panel for."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)

        self.file_dialog = FakeFileDialog()
        self.saved_file_dialog = main_module.QFileDialog
        main_module.QFileDialog = self.file_dialog
        self.addCleanup(self.restore)

        self.app = FakeRunViewer(self.folder)

    def restore(self):
        main_module.QFileDialog = self.saved_file_dialog

    def suggested_path(self):
        """The name the panel was offered, the dialog having been cancelled."""
        self.file_dialog.answer = ''
        self.app.on_save_channel_config()
        self.assertEqual(len(self.file_dialog.calls), 1, 'the panel is opened once')
        return self.file_dialog.calls[0]

    def test_the_offered_filename_carries_the_toml_extension(self):
        suggested = self.suggested_path()

        self.assertTrue(
            suggested.lower().endswith('.toml'),
            'the panel keeps the extension it is given and replaces only the '
            'stem, so the name offered has to end in .toml; got %r' % suggested,
        )

    def test_the_offered_filename_sits_in_the_default_config_folder(self):
        suggested = self.suggested_path()

        self.assertEqual(
            os.path.dirname(suggested),
            self.folder,
            'the panel still opens where saved configurations are kept',
        )

    def test_the_offered_filename_is_not_the_runviewer_state_file(self):
        # The state file lives in this same folder, and *Save runviewer state*
        # writes window geometry to it. A channel configuration written over it
        # would take that geometry with it, so the panel must not offer its
        # name as the one to accept.
        suggested = self.suggested_path()

        self.assertNotEqual(
            os.path.basename(suggested).lower(),
            RunViewer.default_config_filename.lower(),
            'the name offered is one to type over, not a file that exists',
        )


if __name__ == '__main__':
    unittest.main()

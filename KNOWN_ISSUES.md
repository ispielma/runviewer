# Known issues

- `__main__.py`, `update_plots`: adding a selected shot creates placeholder traces even for channels absent from that shot, unlike create_plot; those placeholders are never resampled, with visible/autorange effects unverified.

- A pseudoclock triggered from a DigitalOut line, not an intermediate device's trigger connection, is not drawn: labscript-devices' parsers return the line, and `Shot._load_device` (`runviewer/__main__.py`) then finds no runviewer parser for its Trigger and logs "Failed to load device".

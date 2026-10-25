"""
The Sensitor platform: one identity, one navigation, one account across every
space — Academy, Library, Trading Lab, and the spaces still in preparation.

    spaces   the registry: which spaces exist, their status and their pages
    brand    the official mark, read from assets/brand/
    ui       the Streamlit shell (theme, components, navigation, routing)

A space is added by declaring it in `spaces.SPACES` and giving its pages a
renderer in `ui.shell`. Nothing else in the shell changes.
"""

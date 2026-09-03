"""
One module per page of the window.

A page owns its own widgets and its own state, knows how to draw the result of
one calculation, and is created the first time somebody opens it. Switching
pages hides the old one instead of destroying it, so what was typed is still
there on the way back.
"""

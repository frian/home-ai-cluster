# Loopback Browser Workspace Code

The loopback browser's existing Code view is text-only by default. To allow a
workspace-aware turn, explicitly enable workspace access, enter an existing
host workspace root, and select one or more grants: `list`, `read`, `write`, or
`create`.

The browser keeps that root and grant selection only in the current page. After
a successful workspace-enabled turn, changing either requires reloading or
closing the page to begin a new conversation. Reloading discards browser state;
it does not undo filesystem changes.

Each enabled turn constructs fresh caller-local workspace authority and uses
ordinary independently routed Code inference. Configured remote Code nodes can
receive bounded textual workspace-derived context, but never direct filesystem
authority. Writes and creates that have already committed remain real if a
later failure or disconnect occurs; HAC does not retry or roll them back.

# clipboard_manager.py
#
# IMPORTANT (cloud deployment fix):
# The original version used `pyperclip`, which copies to the SERVER's OS
# clipboard. That works when you run Streamlit on your own laptop, but on
# Streamlit Community Cloud (or any headless container) there is no OS
# clipboard to copy to, so pyperclip.copy() throws:
#   "pyperclip.PyperclipException: Could not find a copy/paste mechanism"
#
# The fix: copy text into the VISITOR's browser clipboard using JavaScript's
# navigator.clipboard API, injected via st.components.v1.html. This runs in
# the user's browser, not on the server, so it works the same locally and
# when deployed.

import streamlit as st
import streamlit.components.v1 as components


class ClipboardManager:
    def copy_to_clipboard(self, text, clear_after=30, key="default"):
        """
        Copy text to the VISITING BROWSER's clipboard via JavaScript.
        Note: clear_after is cosmetic here -- a sandboxed iframe cannot
        reliably reach back into the clipboard later, so we just show the
        message; the calling code's own countdown/UI handles "clearing".
        """
        try:
            safe_text = (
                text.replace("\\", "\\\\").replace("`", "\\`").replace("</script>", "")
            )
            components.html(
                f"""
                <script>
                navigator.clipboard.writeText(`{safe_text}`).catch(function(err) {{
                    console.error('Clipboard write failed', err);
                }});
                </script>
                """,
                height=0,
                width=0,
            )
            st.success(f"✅ Copied to clipboard! (clears from view in {clear_after}s)")
            return True
        except Exception as e:
            st.error(f"❌ Clipboard error: {str(e)}")
            return False

    def clear_clipboard(self, key="default"):
        """
        Best-effort clear of the browser clipboard. Browsers only allow a
        page to overwrite the clipboard while the tab is focused, so this
        is not guaranteed, but we try.
        """
        try:
            components.html(
                """
                <script>
                navigator.clipboard.writeText("").catch(function(err) {});
                </script>
                """,
                height=0,
                width=0,
            )
        except Exception:
            pass

    def cancel_all_timers(self):
        """Kept for backwards compatibility with existing call sites; no-op now
        since there are no server-side threading.Timer instances anymore."""
        pass


# Global clipboard manager instance
clipboard_manager = ClipboardManager()

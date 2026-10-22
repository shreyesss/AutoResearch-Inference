"""Source-checkout import bridge for the separately packaged research tools.

From the repository root, historical artifact folders such as ``ideation/evidence``
must not shadow modules in ``ideation/ideation``. Installed wheels use the inner
package directly; this bridge only governs imports from the outer checkout.
"""
from pathlib import Path as _Path

__path__ = [str(_Path(__file__).parent / "ideation")]

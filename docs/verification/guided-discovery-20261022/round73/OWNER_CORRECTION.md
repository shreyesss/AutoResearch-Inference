# Owner-name correction to the frozen round73 review

The actual pinned class owning the hash buffers is **NgramHashState**, declared in common/engram.py:423 and instantiated as self.engram_hash in nvidia/model.py:902. The earlier author report/card and my frozen review called this owner EngramHash; that class name was incorrect.

Any typed proposal and implementation handoff must name NgramHashState. The constant ownership recommendation refers to that existing state object and its ordered prime/layout buffers. This corrects the symbol, not the arithmetic proof, execution status or deferred disposition. The original author packet and independent review remain unchanged. This addendum uses source inspection only; no runtime, native or GPU execution occurred.

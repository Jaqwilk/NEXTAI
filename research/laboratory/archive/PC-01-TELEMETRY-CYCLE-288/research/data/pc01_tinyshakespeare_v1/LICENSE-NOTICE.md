# PC-01 Tiny Shakespeare — provenance and license notice

Acquired 2026-09-04 for local scientific calibration only. No model weights,
generated data, API or account was used. Payload stays in the ignored archive/.

The upstream author describes the included tinyshakespeare file as a subset of
Shakespeare's works and declares the repository MIT in the License section of
[the pinned Readme](https://github.com/karpathy/char-rnn/blob/6f9487a6fe5b420b7ca9afb0d7c078e37c1d1b4e/Readme.md).
Attribution: William Shakespeare (underlying works); Andrej Karpathy (dataset
distribution and char-rnn repository). The underlying historical works are public
domain; the repository's explicit declaration is MIT. No separate dataset-specific
license text was found. This notice preserves that distinction, and does not claim
that a repository license newly grants rights over Shakespeare's original works.
The initially checked uppercase README.md and root LICENSE URLs returned 404;
the actual upstream declaration is in Readme.md, not a fabricated LICENSE file.

Payload: [pinned input.txt](https://raw.githubusercontent.com/karpathy/char-rnn/6f9487a6fe5b420b7ca9afb0d7c078e37c1d1b4e/data/tinyshakespeare/input.txt).
Exact bytes, SHA-256, intervals, storage checks and acquisition URL are in
acquisition.json. No text normalization, extraction, deduplication or resampling
was performed. Hashing read the whole file, including the final interval; corpus
text and final quality were not displayed. This is a local, inspectable holdout,
not a blind or independently inaccessible evaluation.

The model recipe is a separate source, nanoGPT by Andrej Karpathy, under an
explicit [MIT license](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/LICENSE).
If model code is adapted in a later preregistered cycle, retain that full copyright
and permission notice with the implementation. No upstream model code is vendored
or executed in this contract-design cycle.

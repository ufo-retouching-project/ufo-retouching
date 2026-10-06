# PSD retouching

## Repository contents

The Git repository contains project instructions and Python workflow scripts. PSD sources, finished references, whip assets, generated images, and `.retouch/` job data stay local and are excluded by `.gitignore`. Add the required PSD assets to your local checkout before running Photoshop jobs.

The Photoshop UXP plugin is an external dependency at the local path documented below; it is not included in this repository. Several preparation and review scripts are specific UFO 4 trials, not general-purpose component classifiers. This repository does not install Photoshop or automatically retouch a fresh photograph.

1. Drop new source PSDs into **input**.
2. In this project's chat, say **“Retouch the new files.”**
3. Review the new layered PSDs and previews in **outputs**. Describe corrections in ordinary language; mention the component or area you mean.

Photoshop must be running with the **1000Bulbs Retouching Assistant** plugin loaded. Codex handles inspection, mask preparation, and queued Photoshop operations. Dropping files into the folder alone does not start editing. The workflow is agent-assisted: it does not reuse UFO 4's mask coordinates on unrelated photos.

Component masks start with Photoshop's **Object Selection or Quick Selection**, or a **color-based selection** where the part has a distinct color. For UFOs and high bays, combine the connected housing, rim, and controls in one independently editable **Fixture** mask. Keep parts likely to need separate treatment—such as LEDs, lens, sensor, CCT label, and screws—in separate masks. Refine with **Select and Mask** as appropriate and correct remaining errors; tracing is a fallback. Inspect actual edges at full resolution. This is the required workflow going forward; the queue importer consumes prepared masks, so native component selection must be performed through Photoshop or added and verified in the plugin. See **AGENTS.md** for the detailed method and efficiency guidance.

The first phase cleans clear defects, isolates the subject, and creates editable component masks refined to the actual part edges. Hardware means screws by default. Remove silver labels from ordinary product shots, while preserving dedicated label shots and the front CCT label. For UFOs and high bays, always remove all photographed cables and replace them with the correct whip, even without red X marks. Preserve real product details and flag uncertain areas. Finished UFO/high-bay images must be upright, centered horizontally and vertically on a square canvas, with 20 px margins at left and right; the photographer's original orientation and framing are not the target. The product-page reference shows the hanging orientation: lens/diffuser bowl down, mounting/rear housing above, lower rim level, and whip coil above-right. Transform the isolated product and aligned masks together, then place the editable whip to match without distorting proportions. Keep the PSD at the largest square size supported by native fixture detail and export JPEGs at 2000 × 2000 px minimum. See **AGENTS.md** for the detailed rule.

For UFO and high-bay whip replacement, match the fixture finish: use the supplied black whip for a black fixture and white whip for a white fixture. Place it at the fixture's upper right, following the finished references, and keep it editable separately from the fixture. The confirmed top-to-bottom order is **CC → RT → Black Whip or White Whip → White Background → Original**, so the whip sits behind the masked fixture. Editable imports of both supplied assets have passed internal save-and-reopen tests. These tests do not establish final mask or retouch quality.

Outputs use new filenames. Source PSDs and finished reference files are never overwritten. The first engine supports a single image layer in RGB PSDs, including the tested 16-bit source; existing layered edits require inspection before processing.

## Agent commands

Option to evaluate when work resumes after lunch: use the Adobe plugin in this chat to generate component selection masks, then import them through the custom Photoshop plugin to build the editable PSD. Accuracy and speed on these UFO photographs have not yet been tested. Keep this option in consideration when improving the workflow.

Use `python3 scripts/retouch_jobs.py list` to find inputs. Use `inspect <source-path>` to request a full-resolution preview and initial Photoshop subject selection. Inspect and refine masks for each photo, then use `apply <spec-path>` to enqueue the reviewed edits. Use `status <job-id>` or `wait <job-id>` to read completion or failures.

Internal inspection files, full-canvas mask assets, job requests, and results live in `.retouch/`. The current plugin source lives at `/Users/joshuabrown/Desktop/1000Bulbs Retouching Assistant/com.1000bulbs.retouching/`. Its job service polls this project's queue and executes one job at a time.

The user has reviewed the UFO 4 v4 trial and chose to refine the same source toward an approved standard before moving to UFO 5. Preserve v4 and save refinements under new filenames. Move to UFO 5 after the user approves the refined standard; production batches also require that review. No cable-policy question remains pending. See **AGENTS.md** for the agreed editing and acceptance standards.

The latest UFO 4 mask review candidate is **outputs/UFO 4 - Native Selection Trial v6b.psd**. It preserves the reviewed v5 cleanup and whip while updating component selections. The user reported that some selections still need refinement and requested one combined **Fixture** mask for the former Housing, Rim, and Controls areas in the next revision. Keep the CCT label, LEDs, lens, sensor, and screws separately editable where present. Human acceptance remains pending; use v6b and its detail previews to guide the next revision.

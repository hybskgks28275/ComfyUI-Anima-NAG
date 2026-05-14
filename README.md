# ComfyUI-Anima-NAG

Experimental Normalized Attention Guidance node for Anima Preview 3 in ComfyUI.

Common SD/SDXL NAG nodes patch `BasicTransformerBlock.attn2`, but Anima Preview 3 is detected by ComfyUI as `image_model="anima"` and uses the Anima/Cosmos Predict2 attention path. This custom node wraps ComfyUI's `optimized_attention` path instead, so it can affect Anima cross-attention.

This node is intended to be used together with [Anima Turbo LoRA](https://civitai.red/models/2560840/anima-turbo-lora). The LoRA page describes it as trained on Anima Preview 3 and suggests CFG 1 with 8-12 steps; this node is meant to add negative-guidance control to that kind of low-CFG turbo workflow.

## Node

### Anima Normalized Attention Guidance

- Category: `Anima/Guidance`
- Input:
  - `model` (MODEL): Anima Preview 3 model
  - `scale` (FLOAT): NAG strength
  - `tau` (FLOAT): normalization threshold
  - `alpha` (FLOAT): blend between original positive attention and normalized guided attention
  - `start_percent` / `end_percent` (FLOAT): active sampling range; `0.0` is the first step and `1.0` is the last step
  - `only_anima` (BOOLEAN): apply only when the model is detected as `image_model="anima"`
  - `optimize_outside_range` (BOOLEAN): compute only the positive branch outside the active NAG range for faster CFG 1 turbo workflows
- Output:
  - `model` (MODEL): patched model

## Usage

1. Load an Anima Preview 3 diffusion model.
2. Apply Anima Turbo LoRA to the model and clip.
3. Connect the LoRA-applied model to `Anima Normalized Attention Guidance`.
4. Connect the patched model output to your sampler.
5. Connect both positive and negative conditioning to the sampler.

Suggested starting values:

- Anima Turbo LoRA strength: around `1.0`, or slightly below `1.0` for more variety
- sampler CFG: `1.0`
- sampler steps: `8-12`
- `scale`: `2.0`
- `tau`: `2.5`
- `alpha`: `0.5`
- `start_percent`: `0.0`
- `end_percent`: `1.0`
- `only_anima`: `true`
- `optimize_outside_range`: `true`

## Notes

- This is experimental and tuned for Anima Preview 3's current ComfyUI implementation.
- `start_percent` / `end_percent` are converted internally to the model's sigma range with ComfyUI's `percent_to_sigma()`.
- With `optimize_outside_range=true`, partial ranges can speed up because steps outside the NAG range use the same positive-only behavior as ComfyUI's CFG 1 optimization. This option is intended for CFG 1 turbo workflows.
- The node needs a CFG batch containing both positive and negative branches. If no negative conditioning is connected, it will have no effect.
- Masked attention calls are skipped to avoid shape-specific mask slicing issues.
- If another node already set `optimized_attention_override`, this node wraps the previous override rather than replacing it outright.

## Install

Place this folder under `ComfyUI/custom_nodes/` and restart ComfyUI.

```powershell
cd path\to\ComfyUI\custom_nodes
git clone <your-repo-url> ComfyUI-Anima-NAG
```

## License

MIT

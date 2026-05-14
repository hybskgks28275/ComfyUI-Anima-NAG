# ComfyUI-Anima-NAG

Experimental Normalized Attention Guidance node for Anima Preview 3 in ComfyUI.

Common SD/SDXL NAG nodes patch `BasicTransformerBlock.attn2`, but Anima Preview 3 is detected by ComfyUI as `image_model="anima"` and uses the Anima/Cosmos Predict2 attention path. This custom node wraps ComfyUI's `optimized_attention` path instead, so it can affect Anima cross-attention.

## Node

### Anima Normalized Attention Guidance

- Category: `Anima/Guidance`
- Input:
  - `model` (MODEL): Anima Preview 3 model
  - `scale` (FLOAT): NAG strength
  - `tau` (FLOAT): normalization threshold
  - `alpha` (FLOAT): blend between original positive attention and normalized guided attention
  - `sigma_start` / `sigma_end` (FLOAT): active sigma range; `-1` means no limit
  - `only_anima` (BOOLEAN): apply only when the model is detected as `image_model="anima"`
- Output:
  - `model` (MODEL): patched model

## Usage

1. Load an Anima Preview 3 diffusion model.
2. Connect the model to `Anima Normalized Attention Guidance`.
3. Connect the patched model output to your sampler.
4. Connect both positive and negative conditioning to the sampler.

Suggested starting values:

- `scale`: `2.0`
- `tau`: `2.5`
- `alpha`: `0.5`
- `sigma_start`: `-1`
- `sigma_end`: `-1`
- `only_anima`: `true`

## Notes

- This is experimental and tuned for Anima Preview 3's current ComfyUI implementation.
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

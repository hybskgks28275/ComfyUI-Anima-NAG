# ComfyUI-Anima-NAG

[日本語版 README](README_ja.md)

Experimental Normalized Attention Guidance node for the official Anima base model in ComfyUI.

Common SD/SDXL NAG nodes patch `BasicTransformerBlock.attn2`, but Anima is detected by ComfyUI as `image_model="anima"` and uses the Anima/Cosmos Predict2 attention path. This custom node wraps ComfyUI's `optimized_attention` path instead, so it can affect Anima cross-attention.

Anima is a 2B text-to-image model from CircleStone Labs and Comfy Org, focused on anime, illustration, and other non-photorealistic artwork. The official release is natively supported by ComfyUI and is available from:

- Civitai: [Anima base-v1.0](https://civitai.red/models/2458426/anima?modelVersionId=2945208)
- Hugging Face: [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima)

This node can be used with the official base model to add negative-guidance control through Anima's cross-attention path. It can also be used together with Anima Turbo LoRA-style low-CFG workflows when you want NAG control at CFG 1.

## Model files

For the official Anima base release, place the files in ComfyUI's model folders as follows:

- `anima-base-v1.0.safetensors` -> `ComfyUI/models/diffusion_models`
- `qwen_3_06b_base.safetensors` -> `ComfyUI/models/text_encoders`
- `qwen_image_vae.safetensors` -> `ComfyUI/models/vae`

## Node

### Anima Normalized Attention Guidance

- Category: `Anima/Guidance`
- Input:
  - `model` (MODEL): Anima model
  - `scale` (FLOAT): NAG strength
  - `tau` (FLOAT): normalization threshold
  - `alpha` (FLOAT): blend between original positive attention and normalized guided attention
  - `start_percent` / `end_percent` (FLOAT): active sampling range; `0.0` is the first step and `1.0` is the last step
  - `only_anima` (BOOLEAN): apply only when the model is detected as `image_model="anima"`
  - `optimize_outside_range` (BOOLEAN): compute only the positive branch outside the active NAG range for faster CFG 1 turbo workflows
- Output:
  - `model` (MODEL): patched model

## Usage

1. Load `anima-base-v1.0.safetensors` with ComfyUI's Anima workflow.
2. Load `qwen_3_06b_base.safetensors` as the text encoder and `qwen_image_vae.safetensors` as the VAE.
3. Connect the Anima model to `Anima Normalized Attention Guidance`.
4. Connect the patched model output to your sampler.
5. Connect both positive and negative conditioning to the sampler.

Example settings:

- Anima Turbo LoRA: enabled
- sampler CFG: `1.0`
- sampler steps: `8-12`
- `scale`: `2.0`
- `tau`: `2.5`
- `alpha`: `0.5`
- `start_percent`: `0.0`
- `end_percent`: `0.5`
- `only_anima`: `true`
- `optimize_outside_range`: `true`

These settings assume the Anima Turbo LoRA recommended `8-12` sampler steps. If you use a different step count or a different acceleration method, review `start_percent`, `end_percent`, `scale`, `tau`, and `alpha` for that workflow.

## Sample workflow

A sample workflow is included at:

- `WorkFlow/AnimaTurboLoRAwithNAG.json`

This workflow demonstrates using Anima Turbo LoRA together with `Anima Normalized Attention Guidance` at CFG 1. It is intended as a starting point for the `8-12` step turbo setup described above.

## Prompting notes

The official Anima model accepts Danbooru-style tags, natural language captions, and mixtures of both.

- Recommended positive prefix: `masterpiece, best quality, score_7, safe, `
- Recommended negative: `worst quality, low quality, score_1, score_2, score_3, artist name`
- Use lowercase for tags and spaces instead of underscores, except score tags such as `score_7`.
- A typical tag order is quality/meta/year/safety tags, subject count, character, series, artist, then general tags.
- Artist tags should use an `@` prefix.

## Notes

- This is experimental and tuned for Anima's current ComfyUI implementation.
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

"""Anima/Cosmos Predict2 compatible Normalized Attention Guidance."""

from __future__ import annotations

import torch

import comfy.samplers

from .comfy_api_compat import io


_Model = getattr(io, "Model", io.Custom("MODEL"))


def _call_attention(func, q, k, v, heads, kwargs):
    return func(q, k, v, heads, **kwargs)


def _first_sigma(transformer_options: dict) -> float | None:
    sigmas = transformer_options.get("sigmas")
    if sigmas is None:
        return None
    try:
        if len(sigmas) == 0:
            return None
        return float(sigmas[0])
    except Exception:
        return None


def _is_anima_model(model) -> bool:
    try:
        image_model = model.model.model_config.unet_config.get("image_model")
        return image_model == "anima"
    except Exception:
        return False


def _percent_to_sigma_range(model, start_percent: float, end_percent: float) -> tuple[float, float]:
    start_percent = max(0.0, min(1.0, float(start_percent)))
    end_percent = max(0.0, min(1.0, float(end_percent)))
    if end_percent < start_percent:
        start_percent, end_percent = end_percent, start_percent

    model_sampling = model.get_model_object("model_sampling")
    sigma_start = float(model_sampling.percent_to_sigma(start_percent))
    sigma_end = float(model_sampling.percent_to_sigma(end_percent))
    return sigma_start, sigma_end


def _sigma_in_range(sigma: torch.Tensor, sigma_start: float, sigma_end: float) -> bool:
    try:
        sigma_value = float(sigma[0])
    except Exception:
        return True
    return sigma_end < sigma_value <= sigma_start


class AnimaNormalizedAttentionGuidance(io.ComfyNode):
    """Apply NAG through optimized_attention for Anima Preview 3."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AnimaNormalizedAttentionGuidance",
            display_name="Anima Normalized Attention Guidance",
            category="Anima/Guidance",
            search_aliases=["anima", "nag", "normalized attention guidance", "negative guidance"],
            essentials_category="Model Patches/Guidance",
            inputs=[
                _Model.Input("model", tooltip="Anima Preview 3 model to patch."),
                io.Float.Input(
                    "scale",
                    default=2.0,
                    min=0.0,
                    max=100.0,
                    step=0.1,
                    tooltip="NAG scale. Higher values push away from the negative branch more strongly.",
                ),
                io.Float.Input(
                    "tau",
                    default=2.5,
                    min=0.01,
                    max=100.0,
                    step=0.1,
                    tooltip="Normalization threshold. Higher values allow stronger guidance.",
                ),
                io.Float.Input(
                    "alpha",
                    default=0.5,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    tooltip="Blend between original positive attention and normalized guided attention.",
                ),
                io.Float.Input(
                    "start_percent",
                    default=0.0,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    tooltip="Relative sampling progress to start applying NAG. 0.0 is the first step.",
                ),
                io.Float.Input(
                    "end_percent",
                    default=1.0,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    tooltip="Relative sampling progress to stop applying NAG. 1.0 is the last step.",
                ),
                io.Boolean.Input(
                    "only_anima",
                    default=True,
                    tooltip="When enabled, do nothing unless the model is detected as image_model='anima'.",
                ),
                io.Boolean.Input(
                    "optimize_outside_range",
                    default=True,
                    tooltip=(
                        "When enabled, steps outside the NAG percent range compute only the positive branch. "
                        "This preserves CFG=1 turbo workflows and makes partial ranges faster."
                    ),
                ),
            ],
            outputs=[
                _Model.Output(display_name="model"),
            ],
            description=(
                "Experimental NAG patch for Anima Preview 3. It wraps the optimized_attention path instead of "
                "searching SD/SDXL BasicTransformerBlock.attn2 modules."
            ),
        )

    @classmethod
    def execute(
        cls,
        model,
        scale: float,
        tau: float,
        alpha: float,
        start_percent: float,
        end_percent: float,
        only_anima: bool,
        optimize_outside_range: bool,
    ) -> io.NodeOutput:
        m = model.clone()
        if only_anima and not _is_anima_model(m):
            return io.NodeOutput(m)

        sigma_start, sigma_end = _percent_to_sigma_range(m, start_percent, end_percent)
        scale = float(scale)
        tau = float(tau)
        alpha = float(alpha)

        transformer_options = m.model_options.setdefault("transformer_options", {}).copy()
        previous_override = transformer_options.get("optimized_attention_override")
        previous_calc_cond_batch = m.model_options.get("sampler_calc_cond_batch_function")

        def run_attention(func, q, k, v, heads, call_kwargs):
            if previous_override is None:
                return _call_attention(func, q, k, v, heads, call_kwargs)
            return previous_override(func, q, k, v, heads, **call_kwargs)

        def attention_override(func, q, k, v, heads, **kwargs):
            call_kwargs = kwargs.copy()
            transformer_options_inner = call_kwargs.get("transformer_options") or {}
            z = run_attention(func, q, k, v, heads, call_kwargs)

            if scale == 0.0 or alpha == 0.0:
                return z

            cond_or_uncond = transformer_options_inner.get("cond_or_uncond")
            if not isinstance(cond_or_uncond, list) or 0 not in cond_or_uncond or 1 not in cond_or_uncond:
                return z

            sigma = _first_sigma(transformer_options_inner)
            if sigma is not None and not (sigma_end < sigma <= sigma_start):
                return z

            # This generic override is intended for cross-attention. Self-attention has matching
            # query/key token counts and should be left untouched.
            if q.shape[-2] == k.shape[-2]:
                return z

            # Mask slicing for arbitrary attention backends is model-specific; skip masked calls.
            if call_kwargs.get("mask") is not None:
                return z

            chunk_count = len(cond_or_uncond)
            if q.shape[0] % chunk_count != 0 or k.shape[0] % chunk_count != 0 or z.shape[0] % chunk_count != 0:
                return z

            try:
                q_chunks = q.chunk(chunk_count, dim=0)
                k_chunks = k.chunk(chunk_count, dim=0)
                v_chunks = v.chunk(chunk_count, dim=0)
                z_chunks = z.chunk(chunk_count, dim=0)

                neg_index = cond_or_uncond.index(1)
                pos_indices = [i for i, value in enumerate(cond_or_uncond) if value == 0]
                if not pos_indices:
                    return z

                q_pos = torch.cat([q_chunks[i] for i in pos_indices], dim=0)
                z_pos = torch.cat([z_chunks[i] for i in pos_indices], dim=0)
                k_neg = torch.cat([k_chunks[neg_index]] * len(pos_indices), dim=0)
                v_neg = torch.cat([v_chunks[neg_index]] * len(pos_indices), dim=0)

                z_neg = run_attention(func, q_pos, k_neg, v_neg, heads, call_kwargs)
                z_tilde = z_pos + scale * (z_pos - z_neg)

                eps = 1e-6
                norm_pos = torch.norm(z_pos, p=1, dim=-1, keepdim=True).clamp_min(eps)
                norm_tilde = torch.norm(z_tilde, p=1, dim=-1, keepdim=True).clamp_min(eps)
                ratio = norm_tilde / norm_pos
                z_hat = torch.minimum(ratio, torch.full_like(ratio, tau)) / ratio * z_tilde
                z_nag = alpha * z_hat + (1.0 - alpha) * z_pos

                out_chunks = list(z_chunks)
                z_nag_chunks = z_nag.chunk(len(pos_indices), dim=0)
                for pos_index, z_nag_chunk in zip(pos_indices, z_nag_chunks):
                    out_chunks[pos_index] = z_nag_chunk
                return torch.cat(out_chunks, dim=0)
            except Exception:
                return z

        def calc_cond_batch_function(args):
            conds = args["conds"]
            if (
                not optimize_outside_range
                or len(conds) < 2
                or conds[1] is None
                or _sigma_in_range(args["sigma"], sigma_start, sigma_end)
            ):
                if previous_calc_cond_batch is not None:
                    return previous_calc_cond_batch(args)
                return comfy.samplers.calc_cond_batch(
                    args["model"],
                    conds,
                    args["input"],
                    args["sigma"],
                    args["model_options"],
                )

            cond_only = [conds[0], None]
            if previous_calc_cond_batch is not None:
                cond_args = args.copy()
                cond_args["conds"] = cond_only
                out = previous_calc_cond_batch(cond_args)
            else:
                out = comfy.samplers.calc_cond_batch(
                    args["model"],
                    cond_only,
                    args["input"],
                    args["sigma"],
                    args["model_options"],
                )

            # At CFG=1 this is equivalent to ComfyUI's CFG1 optimization, while keeping the
            # NAG range free to compute both positive and negative branches.
            return [out[0], out[0]]

        transformer_options["optimized_attention_override"] = attention_override
        m.model_options["transformer_options"] = transformer_options
        m.set_model_sampler_calc_cond_batch_function(calc_cond_batch_function)
        m.disable_model_cfg1_optimization()
        return io.NodeOutput(m)

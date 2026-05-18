# ComfyUI-Anima-NAG

ComfyUI の正式版 Anima ベースモデル向け Normalized Attention Guidance 実験ノードです。

一般的な SD/SDXL 向け NAG ノードは `BasicTransformerBlock.attn2` をパッチしますが、Anima は ComfyUI では `image_model="anima"` として検出され、Anima/Cosmos Predict2 系の attention 経路を使います。このカスタムノードは `optimized_attention` 経路をラップして、Anima の cross-attention に NAG を適用します。

Anima は CircleStone Labs と Comfy Org による 2B パラメータの text-to-image モデルで、アニメ、イラスト、その他の非写実系アートを主対象にしています。正式版は ComfyUI にネイティブ対応しており、以下から入手できます。

- Civitai: [Anima base-v1.0](https://civitai.red/models/2458426/anima?modelVersionId=2945208)
- Hugging Face: [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima)

このノードは正式版 Anima ベースモデルに対して、Anima の cross-attention 経路から negative guidance の制御を追加するためのものです。CFG 1 の低CFGワークフローで NAG を効かせたい場合は、Anima Turbo LoRA 系の構成とも併用できます。

## モデルファイル

正式版 Anima ベースモデルでは、各ファイルを ComfyUI の以下のフォルダに配置します。

- `anima-base-v1.0.safetensors` -> `ComfyUI/models/diffusion_models`
- `qwen_3_06b_base.safetensors` -> `ComfyUI/models/text_encoders`
- `qwen_image_vae.safetensors` -> `ComfyUI/models/vae`

## ノード

### Anima Normalized Attention Guidance

- カテゴリ: `Anima/Guidance`
- 入力:
  - `model` (MODEL): Anima のモデル
  - `scale` (FLOAT): NAG の強度
  - `tau` (FLOAT): 正規化しきい値
  - `alpha` (FLOAT): 元の positive attention と NAG 結果のブレンド率
  - `start_percent` / `end_percent` (FLOAT): 有効なサンプリング範囲。`0.0` が最初のステップ、`1.0` が最後のステップ
  - `only_anima` (BOOLEAN): `image_model="anima"` として検出されたモデルだけに適用
  - `optimize_outside_range` (BOOLEAN): NAG範囲外では positive branch のみを計算し、CFG 1 turboワークフローを高速化
- 出力:
  - `model` (MODEL): パッチ済みモデル

## 使い方

1. ComfyUI の Anima 用ワークフローで `anima-base-v1.0.safetensors` を読み込みます。
2. text encoder に `qwen_3_06b_base.safetensors`、VAE に `qwen_image_vae.safetensors` を読み込みます。
3. Anima の model を `Anima Normalized Attention Guidance` に接続します。
4. 出力 model を sampler に接続します。
5. sampler には positive / negative conditioning の両方を接続します。

設定例:

- Anima Turbo LoRA: 有効
- sampler CFG: `1.0`
- sampler steps: `8-12`
- `scale`: `2.0`
- `tau`: `2.5`
- `alpha`: `0.5`
- `start_percent`: `0.0`
- `end_percent`: `0.5`
- `only_anima`: `true`
- `optimize_outside_range`: `true`

この設定例は、Anima Turbo LoRA の推奨である sampler steps `8-12` を前提にしています。異なるステップ数や別の高速化手法を使う場合は、そのワークフローに合わせて `start_percent`、`end_percent`、`scale`、`tau`、`alpha` を見直してください。

## プロンプトのメモ

正式版 Anima は Danbooru 形式のタグ、自然文キャプション、およびその混在を扱えます。

- positive prefix の推奨: `masterpiece, best quality, score_7, safe, `
- negative の推奨: `worst quality, low quality, score_1, score_2, score_3, artist name`
- タグは小文字、アンダースコアではなくスペース区切りが基本です。ただし `score_7` のような score タグは例外です。
- タグ順は quality/meta/year/safety、人数、キャラクター、作品、artist、general tags の順が目安です。
- artist タグには `@` prefix を付けます。

## 注意

- 現在の ComfyUI の Anima 実装向けの実験ノードです。
- `start_percent` / `end_percent` は内部で ComfyUI の `percent_to_sigma()` によりモデルごとの sigma 範囲へ変換されます。
- `optimize_outside_range=true` の場合、NAG範囲外のステップは ComfyUI の CFG 1 最適化と同じ positive-only 相当で計算するため、部分適用時に高速化できます。このオプションは CFG 1 の turboワークフロー向けです。
- positive / negative の両方を含む CFG バッチが必要です。negative conditioning が接続されていない場合は効果が出ません。
- shape 固有の mask 処理を避けるため、masked attention 呼び出しでは処理をスキップします。
- 既に別ノードが `optimized_attention_override` を設定している場合、このノードは既存 override を包む形で動作します。

## インストール

このフォルダを `ComfyUI/custom_nodes/` に配置し、ComfyUI を再起動してください。

```powershell
cd path\to\ComfyUI\custom_nodes
git clone <your-repo-url> ComfyUI-Anima-NAG
```

## ライセンス

MIT

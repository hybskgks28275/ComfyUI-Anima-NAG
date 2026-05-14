# ComfyUI-Anima-NAG

ComfyUI の Anima Preview 3 向け Normalized Attention Guidance 実験ノードです。

一般的な SD/SDXL 向け NAG ノードは `BasicTransformerBlock.attn2` をパッチしますが、Anima Preview 3 は ComfyUI では `image_model="anima"` として検出され、Anima/Cosmos Predict2 系の attention 経路を使います。このカスタムノードは `optimized_attention` 経路をラップして、Anima の cross-attention に NAG を適用します。

このノードは [Anima Turbo LoRA](https://civitai.red/models/2560840/anima-turbo-lora) との併用を想定しています。LoRAページでは Anima Preview 3 で学習され、CFG 1 と 8-12 steps が推奨されています。このノードは、そのような低CFGのturboワークフローに negative guidance の制御を足す目的で作っています。

## ノード

### Anima Normalized Attention Guidance

- カテゴリ: `Anima/Guidance`
- 入力:
  - `model` (MODEL): Anima Preview 3 のモデル
  - `scale` (FLOAT): NAG の強度
  - `tau` (FLOAT): 正規化しきい値
  - `alpha` (FLOAT): 元の positive attention と NAG 結果のブレンド率
  - `sigma_start` / `sigma_end` (FLOAT): 有効 sigma 範囲。`-1` で制限なし
  - `only_anima` (BOOLEAN): `image_model="anima"` として検出されたモデルだけに適用
- 出力:
  - `model` (MODEL): パッチ済みモデル

## 使い方

1. Anima Preview 3 の diffusion model を読み込みます。
2. Anima Turbo LoRA を model / clip に適用します。
3. LoRA適用後の model を `Anima Normalized Attention Guidance` に接続します。
4. 出力 model を sampler に接続します。
5. sampler には positive / negative conditioning の両方を接続します。

初期値の目安:

- Anima Turbo LoRA strength: `1.0` 前後。バリエーションを増やしたい場合は少し下げる
- sampler CFG: `1.0`
- sampler steps: `8-12`
- `scale`: `2.0`
- `tau`: `2.5`
- `alpha`: `0.5`
- `sigma_start`: `-1`
- `sigma_end`: `-1`
- `only_anima`: `true`

## 注意

- 現在の ComfyUI の Anima Preview 3 実装向けの実験ノードです。
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

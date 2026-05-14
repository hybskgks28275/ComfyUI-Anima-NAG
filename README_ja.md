# ComfyUI-Anima-NAG

ComfyUI の Anima Preview 3 向け Normalized Attention Guidance 実験ノードです。

一般的な SD/SDXL 向け NAG ノードは `BasicTransformerBlock.attn2` をパッチしますが、Anima Preview 3 は ComfyUI では `image_model="anima"` として検出され、Anima/Cosmos Predict2 系の attention 経路を使います。このカスタムノードは `optimized_attention` 経路をラップして、Anima の cross-attention に NAG を適用します。

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
2. model を `Anima Normalized Attention Guidance` に接続します。
3. 出力 model を sampler に接続します。
4. sampler には positive / negative conditioning の両方を接続します。

初期値の目安:

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

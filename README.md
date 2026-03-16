# Whisper Local STT

ローカルGPUで動作する音声入力ツール。ホットキーを押しながら話すと、アクティブウィンドウにテキストが直接入力されます。日本語最適化済み。

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) を使用し、クラウドAPIなしで高速な音声認識を実現します。

## Features

- **Push-to-Talk / Toggle** 方式の音声入力
- **GPU推論** (CUDA) による高速な文字起こし
- **IMEバイパス** - WM_CHAR で直接テキスト入力。日本語IMEと干渉しない
- **システムトレイ常駐** - 設定GUIから各種パラメータを変更可能
- **Initial Prompt / Hotwords** - 同音異義語の精度改善や固有名詞の認識向上

## Requirements

- Windows 10/11
- Python 3.11+
- NVIDIA GPU (CUDA対応) + 最新ドライバ
- マイク

## Installation

```bash
git clone https://github.com/gezzzi/whisper-local-stt.git
cd whisper-local-stt
python -m venv .venv
.venv\Scripts\activate
pip install -e .
copy config.example.toml config.toml
```

初回起動時にWhisperモデル (large-v3-turbo, ~1.6GB) が自動ダウンロードされます。

## Usage

### PowerShell から起動

```powershell
cd C:\path\to\whisper-local-stt
Start-Process .venv\Scripts\pythonw.exe -ArgumentList '-m','whisper_stt','--debug'
```

### start.bat から起動

`start.bat` をダブルクリック、またはエクスプローラーから実行。

### 使い方

1. システムトレイにアイコンが表示されるまで待つ（モデルロードに数秒）
2. テキストを入力したいアプリ（メモ帳、ブラウザ等）にフォーカスを合わせる
3. **右Altキーを押しながら話す**
4. キーを離すと文字起こし → テキストが自動入力される

> **Note:** Git Bash (mintty) からの起動はサポートされていません。PowerShell、cmd.exe、またはstart.batから起動してください。

## Settings

システムトレイアイコンをダブルクリック、または右クリック → "Settings..." で設定画面を開けます。

設定は `config.toml` に保存され、再起動後も維持されます。

---

### Whisper

#### Model

| モデル | パラメータ数 | VRAM目安 | 速度 | 精度 | 備考 |
|--------|-----------|---------|------|------|------|
| `tiny` | 39M | ~1GB | 最速 | 低い | テスト用 |
| `base` | 74M | ~1GB | 速い | 低い | 英語の簡易認識向け |
| `small` | 244M | ~2GB | 普通 | 中程度 | 軽量GPU向け |
| `medium` | 769M | ~5GB | やや遅い | 高い | バランス型 |
| `large-v3` | 1550M | ~6GB | 遅い | 最高 | 最高精度だが重い |
| **`large-v3-turbo`** | 809M | ~3GB | **速い** | **高い** | **本アプリで使用。精度と速度の最良バランス** |

#### Language

認識する言語。言語を指定すると言語検出をスキップするため、~100ms速くなります。

| 値 | 説明 |
|----|------|
| `ja` | 日本語（デフォルト） |
| `en` | 英語 |
| `zh` | 中国語 |
| `ko` | 韓国語 |
| `de` | ドイツ語 |
| `fr` | フランス語 |
| `es` | スペイン語 |
| `auto` | 自動検出（多言語混在時。やや遅くなる） |

#### Beam Size

ビームサーチの幅（1〜10）。大きいほど精度が上がるが遅くなります。デフォルト: 8。

| 値 | 説明 |
|----|------|
| `1` | 最速（greedy search）。短い発話なら十分 |
| `3` | 速度と精度のバランス |
| `5` | 精度重視。速度はほぼ変わらない |
| `8` | **推奨。高精度** |
| `10` | 最も精度が高いが遅い |

#### Initial Prompt

モデルに文脈のヒントを与えるフレーズ。設定GUIからリスト形式で追加・削除できます。

同音異義語の改善に効果的です。使用する分野に関連する単語やフレーズを登録すると、モデルがその文脈を考慮して認識精度を向上させます。

**デフォルト:** `よろしくお願いします。` `では、始めましょう。` `はい、わかりました。` `それでは、次に進みます。`

**Tips:** 句読点（。、）を含む日本語の文章をInitial Promptに入れておくと、モデルが「この文脈では句読点を使う」と学習し、音声認識結果に句読点が安定して付くようになります。

**カスタム例:**
- 技術会議の議事録を取る場合: `技術会議`, `開発`, `リリース`
- 医療関連: `医療診断`, `厚生労働省`, `臨床試験`

#### Hotwords

特定の単語のスコアを上げて認識されやすくします。設定GUIからリスト形式で追加・削除できます。

Initial Promptと異なり、特定の単語にピンポイントで効きます。よく間違えて認識される単語や固有名詞を登録しておくと効果的です。

**例:** `国勢調査`, `後期高齢者`, `渋谷区`

---

### Performance

#### Device

推論に使用するハードウェア。変更時はモデルの再ロードが発生します。

| 値 | 説明 |
|----|------|
| `cuda` | **GPU推論（推奨）**。圧倒的に速い |
| `cpu` | CPU推論。GPUがない場合のフォールバック。5〜10倍遅い |

#### Compute Type

数値演算の精度。速度とVRAM使用量のトレードオフ。変更時はモデルの再ロードが発生します。

| 値 | 説明 |
|----|------|
| `float16` | **推奨**。GPU向け。速度と精度のバランスが最良 |
| `int8` | float16よりVRAM節約。わずかに精度低下 |
| `float32` | 最高精度だがVRAM2倍消費で遅い。通常不要 |

---

### Behavior

#### Sound Feedback

録音開始・完了・エラー時のビープ音のON/OFF。

#### VAD Filter

Voice Activity Detection（音声区間検出）。無音部分を自動的にカットしてからWhisperに渡します。

| 値 | 説明 |
|----|------|
| ON | **推奨**。無音区間を除去して高速化・精度向上 |
| OFF | 録音全体をそのままWhisperに渡す。無音が多いとハルシネーション（幻聴）が起きやすい |

---

## Architecture

```
ホットキー押下 → マイク録音開始
ホットキー離す → 録音停止 → faster-whisper GPU推論 → WM_CHAR で直接テキスト入力
```

### Tech Stack

| 用途 | ライブラリ |
|------|-----------|
| 音声認識 | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| 音声キャプチャ | [sounddevice](https://python-sounddevice.readthedocs.io/) |
| システムトレイ | [pystray](https://github.com/moses-palmer/pystray) + [Pillow](https://pillow.readthedocs.io/) |
| テキスト入力 | Win32 PostMessageW (WM_CHAR) |
| ホットキー検出 | Win32 GetAsyncKeyState |
| 設定GUI | tkinter (stdlib) |
| 設定ファイル | TOML (tomllib, stdlib) |

## License

MIT

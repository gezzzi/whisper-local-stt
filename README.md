# Whisper Local STT

ローカルGPUで動作する日本語音声入力ツール。ホットキーを押しながら話すと、アクティブウィンドウにテキストが直接入力されます。

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) を使用し、クラウドAPIなしで高速な音声認識を実現します。

## Features

- **Push-to-Talk / Toggle** 方式の音声入力
- **GPU推論** (CUDA) による高速な文字起こし
- **AutoHotKey共存** - キーボードフックを使わないため、AHKと干渉しない
- **クリップボード不使用** - SendInput Unicode で直接テキスト入力
- **システムトレイ常駐** - 設定GUIから各種パラメータを変更可能
- **ホットリロード** - 多くの設定は再起動なしで即座に反映

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

初回起動時にWhisperモデル (~3GB) が自動ダウンロードされます。

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

設定は `config.toml` に保存されます。

---

### Hotkey

#### Hotkey

録音を開始/停止するキー。

| 設定例 | 説明 |
|--------|------|
| `ralt` | 右Alt（デフォルト） |
| `f9` | F9キー |
| `ctrl+shift+space` | Ctrl+Shift+Space |
| `rctrl` | 右Ctrl |

使用可能なキー名: `ctrl`, `lctrl`, `rctrl`, `shift`, `lshift`, `rshift`, `alt`, `lalt`, `ralt`, `space`, `tab`, `enter`, `esc`, `f1`〜`f12`, `a`〜`z`, `0`〜`9`

#### Mode

録音の動作方式。

| 値 | 説明 |
|----|------|
| `push_to_talk` | キーを**押し続けている間**だけ録音。離すと文字起こし開始。**推奨** |
| `toggle` | キーを1回押すと録音開始、もう1回押すと停止。長文向き |

---

### Whisper

#### Model

Whisperのモデルサイズ。精度と速度のトレードオフ。変更時はモデルの再ロードが発生します（数秒）。

| モデル | VRAM目安 | 速度 | 精度 | 用途 |
|--------|---------|------|------|------|
| `tiny` | ~1GB | 最速 | 低い | テスト用 |
| `base` | ~1GB | 速い | やや低い | 英語の簡易認識 |
| `small` | ~2GB | 普通 | 中程度 | 軽量で使いたい場合 |
| `medium` | ~5GB | やや遅い | 高い | バランス型 |
| `large-v3` | ~6GB | 遅い | 最高 | 最高精度が欲しい場合 |
| `large-v3-turbo` | ~3GB | **速い** | **高い** | **推奨。精度と速度の最良バランス** |

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

ビームサーチの幅（1〜10）。大きいほど精度が上がるが遅くなります。

| 値 | 説明 |
|----|------|
| `1` | 最速（greedy search）。短い発話なら十分 |
| `3` | **推奨。速度と精度のバランス** |
| `5` | 精度重視。速度はほぼ変わらない |
| `10` | 最も精度が高いが遅い |

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
ホットキー離す → 録音停止 → faster-whisper GPU推論 → SendInput で直接テキスト入力
```

### Threading Model

| スレッド | 役割 |
|---------|------|
| Main | pystray イベントループ（システムトレイ） |
| Hotkey | GetAsyncKeyState ポーリング（15ms間隔） |
| Audio | PortAudio コールバック（sounddevice） |
| Worker | ThreadPoolExecutor - モデルロード・文字起こし・テキスト注入 |

### Tech Stack

| 用途 | ライブラリ |
|------|-----------|
| 音声認識 | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| 音声キャプチャ | [sounddevice](https://python-sounddevice.readthedocs.io/) |
| システムトレイ | [pystray](https://github.com/moses-palmer/pystray) + [Pillow](https://pillow.readthedocs.io/) |
| テキスト入力 | Win32 SendInput (KEYEVENTF_UNICODE) |
| ホットキー検出 | Win32 GetAsyncKeyState |
| 設定GUI | tkinter (stdlib) |
| 設定ファイル | TOML (tomllib, stdlib) |

## License

MIT

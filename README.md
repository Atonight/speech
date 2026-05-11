# speech

中文短视频配音项目，用于管理脚本、分句 CSV、SSML 控制稿，并调用阿里云 DashScope CosyVoice 生成音频。

## 功能

- 单句生成：`scripts/generate_one.py`
- 批量生成：`CosyVoiceClient.synthesize_many(...)`
- 多音色对比：`CosyVoiceClient.compare_voices(...)`
- 配置音色：`configs/voices.yaml`
- 配置预设：`configs/presets.yaml`
- 生成音频：`outputs/audio/`

## 目录

```text
configs/
  presets.yaml
  voices.yaml
data/
  scripts/
  sentences/
  ssml/
outputs/
  audio/
scripts/
  generate_one.py
src/
  cosyvoice_tts/
    client.py
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置 API Key

不要把 Key 写入代码或提交到 Git。请从环境变量读取：

```powershell
$env:DASHSCOPE_API_KEY="你的 DashScope API Key"
```

## 生成测试音频

默认会使用 `cosyvoice-v2` 和 `longjixin`，生成：

```text
outputs/audio/longjixin_test.wav
```

运行：

```bash
python scripts/generate_one.py
```

自定义文本和音色：

```bash
python scripts/generate_one.py --voice longyingjing --text "这是一段短视频配音测试。"
```

指定输出文件：

```bash
python scripts/generate_one.py --output outputs/audio/my_test.wav
```

## 支持的示例音色

`configs/voices.yaml` 中预置了以下 `cosyvoice-v2` voice 参数：

- `longbaizhi`
- `longjixin`
- `longyingjing`
- `longyingtao`

更多音色可以继续追加到 `configs/voices.yaml`。

## 生成文件策略

所有音频文件写入 `outputs/audio/`，该目录已在 `.gitignore` 中忽略，不会提交到 Git。

# hitorie-ascii-pv

日常と地球の額縁 · ASCII PV

**用字符、节拍与文字构成的音乐影像。**

**简体中文** · [English](README.en.md)

这是为ヒトリエ《日常と地球の額縁》制作的非官方字符 PV 项目，词曲作者为 wowaka。画面由 Python 程序生成，不依赖 HTML、浏览器或视频剪辑软件。

每帧是一张 160 列、54 行的字符网格：ASCII 符号、日文与文字纹理共同构成画面，再渲染为 1920 × 1080、30 fps 的视频。也可以直接在支持真彩色的终端中播放。

## 最终版的特点

- **逐句分镜**：65 行演唱歌词分别对应镜头，跟随本地 LRC 时间和音频节拍切换。
- **抽象字符动画**：文字潮汐、波形、烟尘、万花筒、干涉纹、画框隧道和字符地球。
- **重复歌词采用不同画面**：例如上升的文字灯笼、无尽阶梯、突破坐标轴的图表，以及逐盏熄灭的聚光灯。
- **多种配色与排版**：黑白、红蓝、全彩与柔和色调随段落变化；问答、判定和重复劳动也成为视觉元素。
- **独立中文字幕区**：中文字幕避开抖动、闪光和故障效果，另可导出日中双语 SRT。
- **可复现的渲染流程**：按时间绘制帧，支持并行编码、分段缓存、静帧和总览图输出。

当前使用的分镜以 [`pv/storyboard.py`](pv/storyboard.py) 为准，主要调用 `scenes5.py` 至 `scenes8.py`。早期房间、人物和街景方案仍保留为代码素材，不代表最终版的完整画面。

## 快速开始

需要 Python、NumPy、Pillow，以及命令行可用的 FFmpeg / FFprobe。推荐使用 Python 3.11 的 conda 环境；终端有声播放还需要 FFplay。

在克隆仓库并进入项目目录后运行：

```bash
conda create -n ascii-pv python=3.11 -y
conda activate ascii-pv
python -m pip install -r requirements.txt
conda install -c conda-forge ffmpeg
```

自行准备歌曲音频和逐行定时歌词，并放在项目根目录（与 Makefile 同级）：

```text
ヒトリエ - 日常と地球の額縁.flac
ヒトリエ - 日常と地球の額縁.lrc
```

然后检查输入并渲染：

```bash
python tools/check_inputs.py
python -m pv render --workers 4 --preset fast --out out/pv-final.mp4
```

默认输出 H.264 视频和 AAC 双声道音频，完整时长约 3 分 46 秒。渲染耗时取决于机器性能与参数；首次运行会分析音频。内存紧张时可减少 `--workers`。

**这是针对特定歌曲和录音版本制作的 PV，不是任意歌曲的自动 MV 生成器。** 分镜按原录音和 65 行歌词设计；替换版本时需检查时序，并同步修改字幕和分镜映射。

## 常用命令

在已激活的 conda 环境中，从项目根目录执行：

| 用途 | 命令 |
|---|---|
| 分析音频 | `python -m pv analyze` |
| 查看分镜时间表 | `python -m pv info` |
| 低分辨率预览 | `python -m pv render --scale 0.5 --workers 4 --out out/preview.mp4` |
| 仅渲染一段 | `python -m pv render --start 89.5 --end 112.5 --out out/chorus.mp4` |
| 导出指定时刻的静帧 | `python -m pv still 52 94.6 173 216` |
| 生成全片总览图 | `python -m pv sheet --every 5 --out out/contact-sheet.png` |
| 终端播放 | `python -m pv play --start 89.5` |
| 导出双语字幕 | `python tools/export_subtitles.py` |
| 检查字幕、镜头边界和确定性 | `python tools/check_redesign.py` |
| 估算全屏亮度变化 | `python tools/flash_check.py` |

输入也可以显式指定，全局参数需放在子命令之前：

```bash
python -m pv --audio /path/to/song.flac --lrc /path/to/song.lrc render --out out/pv-final.mp4
```

完整渲染按约 20 秒分段，缓存在 `build/segments/`。中断后重复同一命令可复用已完成片段；修改代码、字幕或参数通常会生成新缓存。更换音频时应先执行 `python -m pv analyze`，刷新音频分析。

终端播放需要至少 160 列、54 行的画面空间，以及支持 24 位颜色的终端。字幕和静帧默认输出到 `out/`。Makefile 仍可使用，例如 `make PY=python render`；在 conda 中无需再执行会另建虚拟环境的 `make setup`。

## 工作原理

1. **音频分析**：FFmpeg 解码音频，NumPy 计算频谱、起音强度、频段能量和节拍。
2. **时间轴与分镜**：LRC 提供歌词行的开始时间，`storyboard.py` 选择场景与镜头参数。
3. **字符画面**：场景函数根据时间和音频特征，向字符网格写入字形、前景色与背景色。
4. **像素渲染**：字体图集将字符转换为像素，叠加辉光、扫描线等后期效果，再保护字幕区。
5. **视频编码**：工作进程生成画面，FFmpeg 编码并合入原录音。终端播放器则直接输出 ANSI 真彩色字符。

歌词逐字动画是基于行时间的视觉估算，并非逐字人工对齐。`flash_check.py` 是亮度变化的近似检查，不是完整的光敏安全认证；画面包含闪烁和高对比度切换。

## 修改画面与字幕

- 分镜入口：[`pv/storyboard.py`](pv/storyboard.py) 中的 `_line_shots()`。
- 当前主场景：[`pv/scenes5.py`](pv/scenes5.py)、[`pv/scenes6.py`](pv/scenes6.py)、[`pv/scenes7.py`](pv/scenes7.py)、[`pv/scenes8.py`](pv/scenes8.py)。
- 抽象图形与问答组件：[`pv/abstract.py`](pv/abstract.py)、[`pv/quiz.py`](pv/quiz.py)。
- 中文字幕：[`assets/subtitles.zh.json`](assets/subtitles.zh.json)，按 LRC 顺序保存 `ja` 和 `zh` 字段；重复歌词可对应不同译文。加载器会核对行数和日文内容，不匹配时明确报错。
- 修改后先导出静帧或短片检查，再进行完整渲染；字幕更新后重新运行 `tools/export_subtitles.py`。

## 目录结构

```text
pv/
  audio.py          音频分析
  lrc.py            歌词解析
  timeline.py       节拍与场景上下文
  storyboard.py     分镜与逐句映射
  scenes5.py–8.py    最终版主要场景
  abstract.py       抽象图形与颜色场
  quiz.py           问答和判定画面
  canvas.py         字符网格与绘图接口
  glyphs.py         字体图集
  lyricfx.py        歌词排版与动画
  raster.py         字符转像素与后期处理
  render.py         并行渲染与编码
  player.py         终端播放器
assets/
  fonts/            字体与各自许可证
  earth_mask.txt    地球陆地掩模
  subtitles.zh.json 日中字幕数据
tools/             检查、字幕导出与资源生成工具
```

## 致谢

- **歌曲**：ヒトリエ《日常と地球の額縁》，词曲 wowaka。本项目为非官方同人作品。
- **字体**：[BIZ UDGothic](https://github.com/googlefonts/morisawa-biz-ud-gothic) 与 [Fusion Pixel](https://github.com/TakWolf/fusion-pixel-font)，许可证分别保留在 [`OFL.txt`](assets/fonts/OFL.txt) 和 [`OFL-FusionPixel.txt`](assets/fonts/OFL-FusionPixel.txt)。
- **地球数据**：[Natural Earth](https://www.naturalearthdata.com/) 陆地数据，公共领域；可通过 `tools/make_earth_mask.py` 重建。

## 许可证

本项目的原创程序代码采用 [MIT License](LICENSE)。

MIT 许可不涵盖歌曲录音、日文歌词、中文译文、参考视频，以及代码中引用的歌词片段。`assets/subtitles.zh.json` 不在 MIT 授权范围内。字体沿用各自附带的 SIL Open Font License；Natural Earth 数据保持公共领域属性。

完整范围说明见 [第三方内容与许可说明](NOTICE.md)。

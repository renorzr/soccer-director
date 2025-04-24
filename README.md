# 谷粒足球导播 (Soccer Director)

一个用于足球比赛视频分析与剪辑的工具，可以自动生成比赛集锦、添加解说配音，并提供丰富的视频编辑功能。

## 功能特点

- 🎥 自动生成比赛集锦
- 🎤 智能解说配音
- 📝 比赛事件分析
- 🎯 进球集锦生成
- 🎨 自定义记分牌
- 🎬 视频编辑与预览
- 📊 比赛数据统计

## 安装说明

1. 确保已安装 Python 3.8 或更高版本
2. 克隆项目到本地：
   ```bash
   git clone https://github.com/yourusername/soccer-director.git
   cd soccer-director
   ```
3. 创建并激活虚拟环境（推荐）：
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```
4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
5. 配置环境变量：
   创建 `.env` 文件并添加以下配置：
   ```env
   # OpenAI API密钥（用于生成解说文字）
   OPENAI_API_KEY=your_openai_api_key

   # DashScope API密钥（用于语音合成）
   DASHSCOPE_API_KEY=your_dashscope_api_key

   # 鱼声API密钥（用于语音合成）
   FISH_AUDIO_API_KEY=your_fish_audio_api_key
   FISH_AUDIO_MODEL=your_fish_audio_model_id
   ```

## 使用方法

### 基本命令

```bash
python app.py <操作> <比赛描述文件>
```

### 支持的操作

- `mark`: 在原始比赛视频中标记事件
- `preview`: 预览比赛视频中配音解说的部分
- `analyze`: 根据比赛事件生成分析数据和解说文字
- `edit`: 编辑解说文字
- `make`: 创建并保存比赛视频和集锦
- `clean`: 删除该比赛生成的中间文件
- `goals`: 生成进球集锦

### 比赛描述文件示例

创建 `game.yaml` 文件：

```yaml
# 比赛名称
name: "2024年足球友谊赛"

# 比赛描述（可选）
description: "这是一场精彩的足球友谊赛"

# 参赛队伍信息
teams:
  - name: "主队"
    color: "蓝色"     # 队伍颜色（名称，用于解说）
    score: 0          # 初始比分
  - name: "客队"
    color: "红色"
    score: 0

# 视频相关配置
main_video: "game.mp4"        # 主视频文件
logo_img: "logo.png"          # 队伍logo图片（可选）
logo_video: "logo.mp4"        # 开场logo视频（可选）
bgm: "bgm.mp3"               # 背景音乐（可选）

# 时间相关配置
prev_time: 0                  # 上节比赛结束时间（秒）
quarter: 1                    # 当前比赛节数

# 开场配置（可选）
intro:
  - time: 0
    text: "欢迎收看"
  - time: 2
    text: "2024年足球友谊赛"

# 解说员设置
narrator: "云说"              # 解说员名称

# 记分牌配置
scoreboard: "scoreboard.yaml" # 记分牌配置文件
```

### 使用流程

1. 准备比赛视频和配置文件
2. 标记比赛事件：
   ```bash
   python app.py mark game.yaml
   ```
3. 分析比赛事件：
   ```bash
   python app.py analyze game.yaml
   ```
4. 编辑解说文字（可选）：
   ```bash
   python app.py edit game.yaml
   ```
5. 预览效果：
   ```bash
   python app.py preview game.yaml
   ```
6. 生成最终视频：
   ```bash
   python app.py make game.yaml
   ```

## 文件说明

- `app.py`: 主程序入口
- `editor.py`: 视频编辑模块
- `event_analyzer.py`: 事件分析模块
- `game.py`: 游戏数据管理
- `mark.py`: 事件标记工具
- `utils.py`: 工具函数
- `clips.py`: 视频片段处理
- `scoreboard.py`: 记分牌模块
- `.env`: 环境变量配置文件

## 注意事项

1. 确保视频文件格式为 MP4
2. 配置文件必须使用 YAML 格式
3. 所有相关文件（视频、音频、图片）应放在同一目录下
4. 建议使用虚拟环境运行程序
5. 请妥善保管 API 密钥，不要将其提交到版本控制系统

## 常见问题

1. **Q: 为什么视频无法播放？**  
   A: 请确保已安装 VLC 播放器，并且视频格式为 MP4。

2. **Q: 如何修改解说声音？**  
   A: 在配置文件中修改 `narrator` 字段。

3. **Q: 如何自定义记分牌样式？**  
   A: 修改 `scoreboard.yaml` 文件中的相关配置。

4. **Q: 为什么解说生成失败？**  
   A: 请检查 `.env` 文件中的 API 密钥是否正确配置。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

MIT License 
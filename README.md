# 🎬 AI Video Generator

**Automated YouTube video pipeline for AI/Robotics/Unemployment content.**

Generate 15+ minute viral videos with AI narration, stock footage, and trending topics.

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/Nhughes09/youtube-video-generator.git
cd youtube-video-generator

# Install dependencies
pip install -r requirements.txt

# Set your API keys (see below)
export PEXELS_API_KEY="your_key"
export PIXABAY_API_KEY="your_key"

# Generate a video!
python main.py --discover
```

---

## 🔑 API Keys Setup (All FREE)

| Service          | Get Key                                                                  | Purpose             | Required?   |
| ---------------- | ------------------------------------------------------------------------ | ------------------- | ----------- |
| **Pexels**       | [pexels.com/api](https://www.pexels.com/api/)                            | Stock videos/photos | Recommended |
| **Pixabay**      | [pixabay.com/api](https://pixabay.com/api/docs/)                         | Stock videos/photos | Optional    |
| **HuggingFace**  | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) | AI models           | Optional    |
| **Pollinations** | No key needed!                                                           | AI image generation | ✅ Built-in |

### Set Keys in Terminal:

```bash
export PEXELS_API_KEY="your_pexels_key"
export PIXABAY_API_KEY="your_pixabay_key"
export HUGGINGFACE_API_KEY="your_hf_key"
```

Or create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your keys
```

---

## 📁 Project Structure

```
youtube-video-generator/
├── main.py                 # 🎯 Main orchestrator - run this!
├── reasoning_engine.py     # 🧠 Meta-cognitive intelligence
├── topic_discovery.py      # 📰 Finds trending topics
├── script_generator.py     # 📝 Generates video scripts
├── visual_sourcer.py       # 🎬 Gets stock footage + AI images
├── voiceover.py            # 🎙️ Text-to-speech (Edge TTS)
├── video_assembler.py      # 🎥 Assembles final video
├── metadata_generator.py   # 📋 YouTube titles/descriptions
├── compliance_checker.py   # ✅ Monetization safety check
├── config.py               # ⚙️ Configuration
├── utils.py                # 🔧 Utilities
└── requirements.txt        # 📦 Dependencies
```

---

## 🎯 Usage Examples

### Auto-discover trending topic:

```bash
python main.py --discover
```

### Specify a topic:

```bash
python main.py --topic "AI Mass Layoffs 2026"
```

### Test mode (no rendering):

```bash
python main.py --discover --test
```

---

## 🧠 How It Works

1. **Topic Discovery** - Scans Google News & Reddit for trending AI/robotics topics
2. **Script Generation** - Creates 15-20 min script with viral structure
3. **Visual Sourcing** - Gets stock footage from Pexels/Pixabay + AI images from Pollinations
4. **Voiceover** - Generates human-like narration with Microsoft Edge TTS
5. **Assembly** - Combines everything into final MP4
6. **Metadata** - Creates optimized titles, descriptions, tags

---

## 📊 Output Files

After running, check the `output/` folder:

- `video_*.mp4` - Your video (upload to YouTube)
- `*_script.md` - Full script
- `*_metadata.json` - Title/description/tags
- `shorts/` - Vertical shorts clips

---

## 🔒 Monetization Safe

✅ All visuals are royalty-free (Pexels/Pixabay) or AI-generated  
✅ No copyrighted content  
✅ Original commentary/analysis  
✅ Human-like voice (not robotic)

---

## ⚡ Features

- **Trending Topics** - Auto-discovers viral content
- **81+ Visual Segments** - Proper viral pacing (~9 sec each)
- **Edge TTS Voice** - Human-like Microsoft neural voice
- **Shorts Extraction** - Auto-generates vertical clips
- **Reasoning Engine** - Learns from each run
- **Compliance Check** - Verifies monetization safety

---

## 📝 For Cursor/Antigravity Users

Just tell the AI:

> "Generate me a 15-minute video about [TOPIC]"

The AI will:

1. Write the script
2. Generate images with `generate_image` tool
3. Create voiceover with Edge TTS
4. Assemble the video with MoviePy
5. Save to your Downloads folder

---

## 🤝 Contributing

PRs welcome! Focus areas:

- More visual variety
- Better voice options
- Additional news sources
- Caption/subtitle support

---

## 📜 License

MIT - Use freely, credit appreciated.

---

**Built for [@airobotsunemployment](https://youtube.com/@airobotsunemployment)** 🚀

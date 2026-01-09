# 🎬 AI Video Generator

**Automated 15-20 minute YouTube video pipeline for AI/Robotics content.**

100% FREE • Self-Improving • Production-Ready

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys in .env (copy from .env.example)
cp .env.example .env
# Edit with your free API keys

# 3. Run with auto-topic discovery
python main.py --discover

# Or specify a topic
python main.py --topic "AI Mass Layoffs in 2026"

# Test mode (skip rendering)
python main.py --discover --test
```

---

## 🔑 Free API Keys (Required)

| Service           | Get Key                                                     | Purpose             |
| ----------------- | ----------------------------------------------------------- | ------------------- |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com/api-keys) | Script generation   |
| **Pexels**        | [pexels.com/api](https://www.pexels.com/api/)               | Stock videos/photos |
| **Pixabay**       | [pixabay.com/api](https://pixabay.com/api/docs/)            | Stock videos/photos |
| **Pollinations**  | No key needed!                                              | AI image generation |

---

## 📁 Project Structure

```
videogereator2026/
├── main.py                 # 🎯 Main orchestrator
├── reasoning_engine.py     # 🧠 Meta-cognitive intelligence
├── topic_discovery.py      # 📰 News/Reddit fetching
├── script_generator.py     # 📝 Gemini script generation
├── visual_sourcer.py       # 🎬 Pexels/Pixabay/Pollinations
├── voiceover.py            # 🎙️ gTTS text-to-speech
├── video_assembler.py      # 🎥 MoviePy video creation
├── metadata_generator.py   # 📋 YouTube metadata
├── config.py               # ⚙️ Configuration
├── utils.py                # 🔧 Utilities & logging
├── requirements.txt
├── output/                 # Generated videos
├── logs/                   # Execution logs
└── temp/                   # Working files
```

---

## 🧠 Intelligent Features

### Reasoning Engine

- **Chain-of-thought logging** for every decision
- **Pattern learning** from successful executions
- **Self-improvement** through metric analysis

### Quality Metrics

- Risk assessment (all stock = low risk ✓)
- Viral score prediction
- Retention estimation

### All Logs Saved

```
logs/
├── video_generator.log     # Main log
├── knowledge/              # Learned patterns
│   └── patterns.json       # Success patterns
└── assembly_*.json         # Per-video metrics
```

---

## 📊 Output

Each run produces:

- `video_YYYYMMDD_HHMMSS.mp4` - Main 15-20 min video
- `shorts/` - 3 vertical Shorts clips
- `*_script.md` - Full script
- `*_metadata.json` - Titles, tags, description
- `quality_metrics.json` - Analysis

---

## 🎯 Video Structure

| Section      | Time        | Purpose                       |
| ------------ | ----------- | ----------------------------- |
| Hook         | 0:00-0:30   | Shocking stat, scroll-stopper |
| Overview     | 0:30-2:00   | What's covered, why watch     |
| Breakdown    | 2:00-12:00  | 5-7 key points with analysis  |
| Implications | 12:00-15:00 | Fears vs opportunities        |
| Conclusion   | 15:00+      | Takeaways, CTA, next video    |

---

## ⚠️ Important Notes

1. **Manual Review Required** - Review content before uploading
2. **Transformative Content** - Heavy analysis supports fair use
3. **No Scraping** - Uses only safe stock/AI sources
4. **Monetization Ready** - 15+ min enables mid-roll ads

---

## 🔧 Configuration

Edit `config.py` or set environment variables:

```bash
export GEMINI_API_KEY="your_key"
export PEXELS_API_KEY="your_key"
export PIXABAY_API_KEY="your_key"
```

---

## 📈 Self-Improvement

The system learns from each run:

- Tracks which decisions led to success
- Stores patterns for future reference
- Analyzes quality metrics for optimization

Check `logs/knowledge/patterns.json` for learned patterns.

---

**Built with 🧠 meta-cognitive awareness for intelligent video creation.**

# Quick Start Guide

Get your blog generation workflow up and running in minutes!

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Install Mermaid CLI for diagrams
npm install -g @mermaid-js/mermaid-cli
```

### 2. Configure API Keys

Create a `.env` file with your API keys:

```bash
# Copy the example file
cp .env.example .env

# Edit with your keys
nano .env
```

Required keys:
```env
OPENAI_API_KEY=sk-...                    # Get from https://platform.openai.com
TAVILY_API_KEY=tvly-...                  # Get from https://tavily.com
LANGSMITH_API_KEY=ls__...                # Optional: Get from https://smith.langchain.com
```

### 3. Verify Setup

```bash
# Validate your configuration
make validate

# Or
python main.py --dry-run
```

You should see:
```
✓ Required environment variables found
✓ Configuration loaded
✓ Ready to generate blogs!
```

## 📝 Generate Your First Blog

### Simple Example

```bash
# Using Makefile
make start TOPIC="Real-Time Fraud Detection"

# Or using Python directly
python main.py --topic "Real-Time Fraud Detection"
```

### With Custom Requirements

```bash
python main.py \
    --topic "Video Recommendation Systems" \
    --requirements "Scale: 1B users, Latency: <100ms" \
    --author "Your Name"
```

### Generate a Blog Series

```bash
python main.py \
    --series "ML System Design" \
    --topics "Bot Detection" "ETA Prediction" "Search Ranking" \
    --author "Your Name"
```

## 📂 Output Location

Generated blogs are saved to:
- **Markdown files**: `output/`
- **Diagrams**: `images/`
- **Logs**: `logs/workflow.log`

Example output:
```
output/
├── real-time-fraud-detection.md
├── video-recommendation-systems.md
└── bot-detection.md

images/
├── diagram_architecture_abc123.png
├── diagram_pipeline_def456.png
└── diagram_flow_ghi789.png
```

## ⚙️ Configuration

### Quick Config Changes

Edit `config/workflow_config.yaml`:

```yaml
# Use GPT-3.5 for faster/cheaper generation
llm:
  primary:
    model: "gpt-3.5-turbo"  # Change from gpt-4

# Reduce parallel sections for lower memory
agents:
  content_writer:
    parallel_sections: 3    # Change from 6

# Disable checkpoints for fully automated run
workflow:
  checkpoints:
    enabled: false          # Change from true
```

### Environment-Specific Configs

```bash
# Development (faster, cheaper)
python main.py --topic "Test Topic" --config config/dev_config.yaml

# Production (higher quality)
python main.py --topic "Production Topic" --config config/prod_config.yaml
```

## 🎯 Common Use Cases

### 1. Quick Test Run

```bash
# Generate a short blog for testing
python main.py --topic "Machine Learning Basics" --log-level DEBUG
```

### 2. High-Quality Production Blog

```bash
python main.py \
    --topic "Large-Scale Recommendation Systems" \
    --requirements "Netflix-scale, 200M+ users, <100ms latency" \
    --author "Senior ML Engineer"
```

### 3. Batch Generation

Create a script `generate_series.sh`:

```bash
#!/bin/bash
TOPICS=(
    "Real-Time Fraud Detection"
    "Video Recommendation Systems"
    "ETA Prediction Systems"
    "Search Ranking Systems"
    "Bot Detection Systems"
)

for topic in "${TOPICS[@]}"; do
    echo "Generating: $topic"
    python main.py --topic "$topic" --author "Your Name"
    sleep 60  # Wait between generations
done
```

Run it:
```bash
chmod +x generate_series.sh
./generate_series.sh
```

## 🔍 Monitoring

### View Logs

```bash
# Real-time logs
tail -f logs/workflow.log

# Last 100 lines
make logs
```

### LangSmith Tracing

If you configured `LANGSMITH_API_KEY`, view traces at:
https://smith.langchain.com/

You'll see:
- Agent execution flow
- Token usage per agent
- Latency metrics
- Error traces

## 🛠️ Troubleshooting

### Issue: "OPENAI_API_KEY not found"

**Solution**: Check your `.env` file:
```bash
cat .env | grep OPENAI_API_KEY
```

### Issue: "Mermaid CLI not found"

**Solution**: Install Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
# or
brew install mermaid-cli
```

### Issue: Workflow is slow

**Solutions**:
1. Use GPT-3.5 instead of GPT-4 (5x faster)
2. Reduce `parallel_sections` in config
3. Disable diagram generation temporarily

```yaml
features:
  diagram_generation: false
```

### Issue: Low quality score

**Solutions**:
1. Add more specific requirements
2. Increase temperature for creativity
3. Lower quality thresholds in config

```yaml
quality:
  minimum_score: 6.0  # Lower from 7.0
```

### Issue: Rate limit errors

**Solution**: Add delays between API calls:
```yaml
production:
  rate_limiting:
    enabled: true
    requests_per_minute: 30  # Lower from 60
```

## 📊 Expected Performance

| Metric | Value |
|--------|-------|
| Time per blog | 30-45 minutes |
| Token usage | 150K-200K tokens |
| Cost (GPT-4) | $6-10 per blog |
| Cost (GPT-3.5) | $1-2 per blog |
| Quality score | 7.5-9.0 / 10 |

## 🎨 Customization Quick Tips

### Change Blog Style

Edit `prompts/agent_prompts.md` to adjust writing style.

### Add New Section

Edit template in `config/workflow_config.yaml`:
```yaml
template:
  required_sections:
    - introduction
    - problem_statement
    - your_new_section  # Add here
    - models
```

### Change Output Format

```yaml
output:
  markdown:
    output_dir: "custom_output"
    filename_pattern: "{topic_slug}_{date}.md"
```

## 🚦 What's Next?

1. ✅ Generated your first blog? Awesome!
2. 📖 Read the full README for advanced features
3. 🔧 Customize agents and prompts
4. 📊 Set up LangSmith monitoring
5. 🚀 Generate your blog series!

## 💡 Pro Tips

1. **Start Small**: Test with a simple topic first
2. **Monitor Costs**: Check OpenAI usage dashboard
3. **Review Quality**: Always review QA scores
4. **Iterate Prompts**: Refine agent prompts based on output
5. **Use Version Control**: Track changes to prompts and config

## 📚 Additional Resources

- **Full Documentation**: See `docs/` folder
- **Architecture**: `docs/workflow-architecture-overview.md`
- **Implementation**: `docs/implementation-checklist.md`
- **Prompts**: `prompts/agent_prompts.md`

## 🆘 Need Help?

- Check logs: `logs/workflow.log`
- Run with debug: `--log-level DEBUG`
- Validate setup: `make validate`
- Review documentation in `docs/`

---

Happy blog generating! 🎉


# 🎓 Demo Walkthrough - Matiks Social Media Monitor

This guide provides a step-by-step demonstration of the Matiks Social Media Monitor & Review Aggregation Tool for your internship presentation.

## 🎯 Demo Objectives

Showcase the complete system functionality:
- Automated data collection from multiple sources
- Sentiment analysis and data processing
- Interactive dashboard with filtering
- Scheduled automation capabilities

## 📋 Demo Preparation Checklist

### Before Starting
- [ ] Ensure Python 3.8+ is installed
- [ ] Verify internet connection
- [ ] Close any conflicting applications
- [ ] Have terminal/command prompt ready

### Files to Prepare
- [ ] `aggregator.py` - Main application
- [ ] `requirements.txt` - Dependencies
- [ ] `README.md` - Documentation
- [ ] Clean `output/` directory (optional)

## 🚀 Step-by-Step Demo

### Step 1: Environment Setup (2 minutes)

```bash
# Show project structure
dir /b

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Key Points to Highlight:**
- Clean project organization
- Proper Python environment management
- All dependencies clearly defined

### Step 2: One-Time Data Collection (3 minutes)

```bash
# Run initial collection with small limit for demo
python aggregator.py --once --limit 10 --log-level INFO
```

**What to Show:**
- Live collection from all platforms
- Real-time logging output
- Error handling and fallbacks
- Successful completion message

**Expected Output:**
```
Fetched X reviews from Apple RSS feed (storefront=us)
Fetched Y reviews from Apple RSS feed (storefront=in)
2026-02-02 14:21:29,662Z INFO Run finished (new=43, total=314)
```

### Step 3: Generated Output Tour (2 minutes)

```bash
# Show generated files
dir output

# Display key files
type output\last_run.json
```

**Files to Showcase:**
- `dashboard.html` - Interactive interface
- `combined.csv` - Raw data export
- `last_run.json` - Status tracking
- `monitor.log` - System logs

### Step 4: Interactive Dashboard Demo (5 minutes)

```bash
# Start local server
python -m http.server 8000
```

**Dashboard Features to Demonstrate:**

1. **Platform Filtering**
   - Filter by Reddit, Twitter/X, LinkedIn, Google Play, Apple App Store
   - Show how each platform contributes to overall data

2. **Sentiment Analysis**
   - Filter by positive, neutral, negative sentiment
   - Explain sentiment labeling methodology
   - Show sentiment distribution across platforms

3. **Date Range Filtering**
   - Filter by specific time periods
   - Show recent vs historical mentions
   - Demonstrate trend analysis capabilities

4. **Keyword Search**
   - Search for specific terms in text/author/URL
   - Examples: "bug", "crash", "love", "recommend"
   - Show real-time filtering results

5. **Data Export**
   - Show CSV export capability
   - Explain data schema and columns
   - Discuss integration possibilities

### Step 5: Automation Setup (3 minutes)

```bash
# Stop the server (Ctrl+C)

# Show scheduled monitoring
python aggregator.py --every-minutes 60
```

**Automation Features:**
- Scheduled data collection
- Automatic deduplication
- Continuous dashboard updates
- Background operation capability

**Let it run for 1-2 minutes to show:**
- Scheduled execution
- Incremental data collection
- Status updates

### Step 6: Configuration & Customization (2 minutes)

```bash
# Show configuration options
python aggregator.py --help

# Demonstrate environment variables
set MATIKS_QUERY=Matiks
set MATIKS_LIMIT=25
set MATIKS_EVERY_MINUTES=30
```

**Customization Options:**
- Search query modification
- Collection limits per platform
- Update intervals
- Output directory configuration

## 🎯 Key Talking Points

### Technical Excellence
- **Robust Architecture**: Modular design with separate collectors
- **Error Handling**: Retry logic and graceful fallbacks
- **Data Quality**: Deduplication and normalization
- **Performance**: Parallel processing and efficient data handling

### Business Value
- **Brand Monitoring**: Real-time mention tracking
- **Customer Insights**: Sentiment analysis and feedback trends
- **Competitive Intelligence**: Market position analysis
- **Product Feedback**: Direct customer voice integration

### Scalability
- **Multi-Platform**: Extensible to new social platforms
- **International**: Multi-country app store support
- **Automation**: Hands-off operation
- **Integration**: CSV/JSON export for BI tools

## 📊 Sample Demo Script

### Introduction (30 seconds)
"Today I'll demonstrate the Matiks Social Media Monitor - an automated system I developed to track brand mentions across social media and app stores, providing real-time insights into customer sentiment and feedback."

### Technical Demo (10 minutes)
[Follow the step-by-step guide above]

### Business Impact (2 minutes)
"This system provides Matiks with:
- Real-time brand monitoring across 5 platforms
- Automated sentiment analysis for customer insights  
- Scheduled monitoring requiring no manual intervention
- Export capabilities for integration with existing analytics tools"

### Q&A Preparation
Be ready to discuss:
- API rate limiting and error handling
- Sentiment analysis methodology
- Scalability to additional platforms
- Integration with existing systems
- Data privacy and compliance considerations

## 🔧 Troubleshooting for Demo

### Common Issues & Solutions

1. **API Rate Limits**
   ```bash
   # Reduce limit for demo
   python aggregator.py --once --limit 5
   ```

2. **Network Issues**
   ```bash
   # Check connectivity
   ping google.com
   # Use demo data fallback
   ```

3. **Port Conflicts**
   ```bash
   # Use different port
   python -m http.server 8080
   ```

4. **Permission Errors**
   ```bash
   # Run as administrator if needed
   # Or use different output directory
   python aggregator.py --output-dir demo_output
   ```

## 📈 Success Metrics for Demo

### Technical Success
- ✅ All platforms return data
- ✅ Dashboard loads and functions
- ✅ Filters work correctly
- ✅ Automation runs smoothly

### Business Success
- ✅ Demonstrates clear ROI
- ✅ Shows practical application
- ✅ Highlights competitive advantages
- ✅ Presents growth opportunities

## 🎉 Demo Conclusion

"This tool represents a complete solution for Matiks' social media monitoring needs, combining automated data collection, intelligent sentiment analysis, and intuitive visualization. It's production-ready and can be deployed immediately to provide valuable brand insights."

---

**Demo Duration**: ~20 minutes  
**Setup Time**: 5 minutes  
**Q&A Time**: 10 minutes  
**Total Presentation**: 35 minutes

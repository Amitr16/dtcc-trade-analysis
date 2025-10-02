# OpenAI LLM Integration Setup

This guide will help you set up OpenAI integration for the MCP (Model Context Protocol) queries in the DTCC Trade Analysis application.

## Prerequisites

- OpenAI API key
- Python environment with the application installed

## Setup Steps

### 1. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key (starts with `sk-`)

### 2. Set Environment Variable

#### Option A: Windows PowerShell (Recommended)
```powershell
# Set for current session
$env:OPENAI_API_KEY="your-api-key-here"

# Set permanently (requires restart)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-api-key-here", "User")
```

#### Option B: Windows Command Prompt
```cmd
# Set for current session
set OPENAI_API_KEY=your-api-key-here

# Set permanently
setx OPENAI_API_KEY "your-api-key-here"
```

#### Option C: Create .env file
Create a `.env` file in the `dtcc-analysis-app` directory:
```
OPENAI_API_KEY=your-api-key-here
```

### 3. Test the Integration

1. Start the application:
   ```powershell
   python src/main.py
   ```

2. Open the web interface and go to the "MCP Queries" section

3. Try a query like:
   - "Provide me EUR trade summaries for today"
   - "What are the top 5 currencies by DV01?"
   - "Analyze the USD spread trades"

### 4. Verify LLM is Working

The application will automatically detect if the OpenAI API key is configured. You should see:
- More detailed and intelligent analysis
- Better commentary generation
- Enhanced query responses

## Features Enabled with LLM

- **Intelligent Analysis**: AI-powered insights into trade patterns
- **Natural Language Processing**: Better understanding of complex queries
- **Enhanced Commentary**: More sophisticated market commentary
- **Advanced Summaries**: Detailed analysis with context and trends

## Troubleshooting

### Common Issues

1. **"LLM analysis not available"**
   - Check if OPENAI_API_KEY is set correctly
   - Restart the application after setting the environment variable

2. **API Rate Limits**
   - The application includes rate limiting and error handling
   - Large queries may take longer to process

3. **Network Issues**
   - Ensure internet connection is available
   - Check firewall settings

### Testing Commands

```powershell
# Test if environment variable is set
echo $env:OPENAI_API_KEY

# Test Python can access it
python -c "import os; print('API Key set:', bool(os.getenv('OPENAI_API_KEY')))"
```

## Cost Considerations

- OpenAI API usage is charged per token
- The application is optimized to minimize API calls
- Typical usage: $0.01-0.10 per analysis session
- Monitor usage in your OpenAI dashboard

## Security Notes

- Never commit API keys to version control
- Use environment variables for production
- Rotate API keys regularly
- Monitor API usage for unusual activity
